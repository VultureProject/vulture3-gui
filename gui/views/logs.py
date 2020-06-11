#!/usr/bin/python
#-*- coding: utf-8 -*-
"""This file is part of Vulture 3.

Vulture 3 is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Vulture 3 is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Vulture 3.  If not, see http://www.gnu.org/licenses/.
"""
__author__ = "Olivier de Régis"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = 'Django views dedicated to Vulture GUI status pages'

import csv
import json
import mimetypes
import os
import pytz

from bson.objectid import ObjectId
from django.core.servers.basehttp import FileWrapper
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render_to_response
from django.template import RequestContext

from gui.decorators import group_required
from gui.models.application_settings import Application, Filter
from gui.models.system_settings import Cluster
from gui.models.system_settings import Node
from vulture_toolkit.log.elasticsearch_client import ElasticSearchClient
from vulture_toolkit.log.mongodb_client import MongoDBClient
from vulture_toolkit.log.exceptions import ClientLogException


@group_required('administrator', 'application_manager', 'system_manager', 'security_manager')
def logs(request):
    cluster = Cluster.objects.get()
    node    = cluster.get_current_node()

    packet_filter = []
    for node in cluster.members:
        try:
            if node.system_settings.pf_settings.repository_type == 'data':
                packet_filter.append({
                    'id'  : node.id,
                    'name': node.name,
                    'repo': node.system_settings.pf_settings.repository.type_uri
                })
        except:
            pass

    tmp_app, apps, logging_control = [], [], []
    for node in cluster.members:
        for app in node.get_applications():
            if app in tmp_app:
                continue

            if app.log_custom.repository_type == 'data':
                try:
                    apps.append({
                        'app' : app,
                        'repo': app.log_custom.repository.type_uri
                    })

                    tmp_app.append(app)
                    logging_control.append({str(app.id): app.modsec_policy.logging_control})
                except:
                    logging_control.append({str(app.id): None})
    #apps.sort(key=lambda x: x.name)
    return render_to_response('status_logs.html',
                              {'cluster': cluster, 'apps': apps, 'packet_filter': packet_filter,
                              'logging_control': json.dumps(logging_control),
                              'page': 'logs'}, context_instance=RequestContext(request))

@group_required('administrator', 'application_manager', 'system_manager', 'security_manager')
def get_logs(request):
    """ Get logs from databases.
    Handle MongoDB and ElasticSearch

    """
    cluster = Cluster.objects.get()

    params = {
        'type_logs'   : request.POST['type_logs'],
        'start'       : int(request.POST['iDisplayStart']),
        'length'      : int(request.POST['iDisplayLength']),
        'sorting'     : request.POST['sColumns'].split(',')[int(request.POST['iSortCol_0'])],
        'type_sorting': request.POST['sSortDir_0'],
        'columns'     : request.POST['columns'],
        'dataset'     : False,
        'filter'      : {
            'startDate': request.POST["startDate"],
            'endDate'  : request.POST["endDate"],
        }
    }

    if request.POST['type_data'] == 'waf':
        app_id  = request.POST['app_id']

        ## Fetch the application
        app  = Application.objects.with_id(ObjectId(app_id))
        repo = app.log_custom.repository
        params['filter']['rules'] = json.loads(request.POST['rules'])
        params['filter']['app']   = {
            'name'        : str(app.name).replace(' ', '_'),
            'public_dir'  : app.public_dir,
            'public_name' : app.public_name,
            'public_alias': app.public_alias
        }

    elif request.POST['type_data'] == 'packet_filter':
        node_id = request.POST['node']
        result = {
            'max': 0,
            'data': []
        }

        node = Node.objects.with_id(ObjectId(node_id))
        repo = node.system_settings.pf_settings.repository

        params['filter']['node'] = node.name
        try:
            params['filter']['rules'] = json.loads(request.POST[repo.type_uri])
        except:
            params['filter']['rules'] = json.loads(request.POST['rules'])

    elif request.POST['type_data'] in ('vulture', 'diagnostic'):
        params['filter']['rules'] = json.loads(request.POST['rules'])
        repo = cluster.system_settings.global_settings.repository
    try:
        if repo.type_uri == 'mongodb':
            mongo_client = MongoDBClient(repo)
            result = mongo_client.search(params)

        elif repo.type_uri == 'elasticsearch':
            elastic_client = ElasticSearchClient(repo)
            result = elastic_client.search(params)

    except ClientLogException as e:
        result = "Error:\n" + str(e)
        return JsonResponse({
            "iTotalRecords"       : 0,
            "iTotalDisplayRecords": 0,
            "aaData"              : result
        })
    except Exception as e:
        result = "Error:\nAn error occured while fetching logs"
        return JsonResponse({
            "iTotalRecords"       : 0,
            "iTotalDisplayRecords": 0,
            "aaData"              : result
        })

    data = []
    for res in result['data']:
        ## Render data to STR to json parse
        temp = {}
        for key, value in res.items():
            temp['info'] = "<i class='fa fa-chevron-circle-right'></i><i style='display:none;' class='fa fa-chevron-circle-down'></i>"

            if key == 'requested_uri':
                temp[key] = str(value)[0:100]
                temp['requested_uri_full'] = str(value)
            elif key == 'time' and repo.type_uri == 'mongodb':
                temp[key] = value.replace(tzinfo=pytz.UTC).strftime("%Y-%m-%dT%H:%M:%S%z")
            elif key == 'info':
                temp['info_pf'] = str(value)
            else:
                temp[key] = str(value)

        data.append(temp)

    return JsonResponse({
        "iTotalRecords"       : result['max'],
        "iTotalDisplayRecords": result['max'],
        "aaData"              : data
    })

@group_required('administrator', 'application_manager', 'system_manager', 'security_manager')
def get_filter(request):
    search    = request.POST.get('search')
    type_logs = request.POST.get('type_logs')

    filters = Filter.objects.filter(
        user=request.user,
        type_logs=type_logs,
        name__contains=search
    )

    data = []
    for row in filters:
        data.append({
            'id'  : str(row.id)+"|"+row.content,
            'text': row.name
        })

    return JsonResponse({'results': data})

@group_required('administrator', 'application_manager', 'system_manager', 'security_manager')
def save_filter(request):
    data_filtre = request.POST['filter']
    name_filtre = request.POST['name']
    type_logs   = request.POST['type_logs']

    if request.POST['filter_id'] != "":
        filtre           = Filter.objects.with_id(ObjectId(request.POST['filter_id']))
        filtre.content   = data_filtre
        filtre.name      = name_filtre
        filtre.type_logs = request.POST['type_logs']
    else:
        filtre = Filter(name=name_filtre, content=data_filtre, user=request.user, type_logs=type_logs)

    filtre.save()
    return JsonResponse({'status': True, 'id': str(filtre.id)})

@group_required('administrator', 'application_manager', 'system_manager', 'security_manager')
def del_filter(request):
    filter_id = request.POST['filter_id']
    filtre    = Filter.objects.with_id(ObjectId(filter_id))
    filtre.delete()
    return JsonResponse({'status': True})

@group_required('administrator', 'application_manager', 'system_manager', 'security_manager')
def export_logs(request):
    """ Get logs from database with a search query
    Return a csv formatted file
    """

    if request.method == 'POST':
        cluster   = Cluster.objects.get()

        date = json.loads(request.POST['date'])
        params = {
            'start'       : None,
            'length'      : None,
            'sorting'     : None,
            'type_sorting': None,
            'dataset'     : False,
            'type_logs'   : request.POST['type_logs'],
            'filter'      : {
                'startDate': date['startDate'],
                'endDate'  : date["endDate"],
            }
        }


        if request.POST['type_data'] == 'waf':
            app_id  = request.POST['app_id']

            ## Fetch the application
            app  = Application.objects.with_id(ObjectId(app_id))
            repo = app.log_custom.repository
            params['filter']['rules'] = json.loads(request.POST['rules'])
            params['filter']['app']   = {
                'name'        : str(app.name).replace(' ', '_'),
                'public_dir'  : app.public_dir,
                'public_name' : app.public_name,
                'public_alias': app.public_alias
            }

        elif request.POST['type_data'] == 'packet_filter':
            node_id = request.POST['node']
            result = {
                'max': 0,
                'data': []
            }

            node = Node.objects.with_id(ObjectId(node_id))
            repo = node.system_settings.pf_settings.repository
            params['filter']['node'] = node.name;
            try:
                params['filter']['rules'] = json.loads(request.POST[repo.type_uri])
            except:
                params['filter']['rules'] = json.loads(request.POST['rules'])

        elif request.POST['type_data'] == 'vulture':
            repo = cluster.system_settings.global_settings.repository
            params['filter']['rules'] = json.loads(request.POST['rules'])

        try:

            if repo.type_uri == 'mongodb':
                mongo_client = MongoDBClient(repo)
                result = mongo_client.search(params)

            elif repo.type_uri == 'elasticsearch':
                elastic_client = ElasticSearchClient(repo)
                result = elastic_client.search(params)

            with open('/tmp/logs.csv', 'w') as csvfile:
                writer = csv.DictWriter(csvfile, result['data'][0].keys())
                for row in result['data']:
                    if '@timestamp' in row:
                        row.pop('@timestamp')

                    if repo.type_uri == 'mongodb':
                            row['time'] = row['time'].replace(tzinfo=pytz.UTC).strftime("%Y-%m-%dT%H:%M:%S%z")

                    writer.writerow(row)

            return JsonResponse({'status': True})
        except IndexError:
            return JsonResponse({
                "status"              : False,
                "reason"              : "Index Error:\n search results are empty"
            })
        except ClientLogException as e:
            return JsonResponse({
                "status"              : False,
                "reason"              : "Error:\n" + str(e)
            })
        except Exception:
            return JsonResponse({
                "status"              : False,
                "reason"              : "Error:\nAn error occured while exporting logs"
            })
    elif request.method == 'GET':
        wrapper      = FileWrapper(open('/tmp/logs.csv'))
        content_type = mimetypes.guess_type('/tmp/logs.csv')[0]
        response     = HttpResponse(wrapper,content_type=content_type)
        response['Content-Length']      = os.path.getsize('/tmp/logs.csv')
        response['Content-Disposition'] = "attachment; filename=logs.csv"
        return response

@group_required('administrator', 'application_manager', 'system_manager', 'security_manager')
def blacklist_pf(request):
    """ Add a block rule into pf conf
    """
    cluster = Cluster.objects.get()
    src_ip  = request.POST['src_ip']

    for node in cluster.members:
        node.system_settings.pf_settings.pf_blacklist += '\n'+src_ip
        node.save()

    return JsonResponse({'status': True})
