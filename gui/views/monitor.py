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
__author__     = "Olivier de Régis"
__credits__    = []
__license__    = "GPLv3"
__version__    = "3.0.0"
__maintainer__ = "Vulture Project"
__email__      = "contact@vultureproject.org"
__doc__        = 'Django views dedicated to Vulture GUI status pages'

import datetime
import json

from bson import ObjectId
from django.http import JsonResponse
from django.shortcuts import render_to_response
from django.template import RequestContext

from gui.decorators import group_required
from gui.models.application_settings import Application
from gui.models.monitor_settings import Monitor
from gui.models.system_settings import Cluster
from vulture_toolkit.log.elasticsearch_client import ElasticSearchClient
from vulture_toolkit.log.mongodb_client import MongoDBClient
from vulture_toolkit.monitor.data import MonitorData


@group_required('administrator', 'application_manager', 'system_manager', 'security_manager')
def general(request, object_id=None):
    """

    :param request:
    :return:
    """
    cluster      = Cluster.objects.get()
    cluster_data = []
    nodes        = []
    for node in cluster.members:
        if node.temporary_key:
            continue

        if node.is_dead:
            cluster_data.append({
                    'node'   : node,
            })
            continue
        
        nodes.append(str(node.id))
        last = Monitor.objects(node=node).order_by('-id').first()
        try:
            cluster_data.append({
                    'node'   : node,
                    'process': json.loads(last.node_status),
                    'process_date': last.date
            })
        except:
            cluster_data.append({
                    'node'   : node,
            })

    return render_to_response('monitor_general.html',
                              {'cluster': cluster, 'object_id': object_id, 
                              'results': cluster_data, 'nodes': json.dumps(nodes)},
                              context_instance=RequestContext(request))

@group_required('administrator', 'application_manager', 'system_manager', 'security_manager')
def realtime(request):
    cluster = Cluster.objects.get()
    results = cluster.api_request('/api/supervision/realtime/')
    return JsonResponse(results)

@group_required('administrator', 'application_manager', 'system_manager', 'security_manager')
def system(request):
    cluster = Cluster.objects.get()
    return render_to_response('monitor_system.html', {'cluster': cluster},
                            context_instance=RequestContext(request))

@group_required('administrator', 'application_manager', 'system_manager', 'security_manager')
def network(request):
    cluster = Cluster.objects.get()
    return render_to_response('monitor_network.html', {'cluster': cluster},
                            context_instance=RequestContext(request))

@group_required('administrator', 'application_manager', 'system_manager', 'security_manager')
def users(request):
    cluster = Cluster.objects.get()
    return render_to_response('monitor_users.html', {'cluster': cluster},
                            context_instance=RequestContext(request))

@group_required('administrator', 'application_manager', 'system_manager', 'security_manager')
def data(request):
    chart = request.POST['chart']
    if chart == "":
        return JsonResponse({'status': False})

    results = [], 0
    monit   = MonitorData()

    data_chart = {
        'redis_chart'  : "redis_mem_used",
        'memory_chart'    : "mem_percent",
        'cpu_chart'       : "cpu_percent",
        'process_chart'   : "nb_process",
        'root_chart'      : "root_percent",
        'var_chart'       : "var_percent",
        'home_chart'      : "home_percent",
        'swap_chart'      : "swap_percent",
        'bytes_recv_chart': "bytes_recv",
        'bytes_sent_chart': "bytes_sent",
        'dropin_chart'    : "dropin",
        'errin_chart'     : "errin",
        'errout_chart'    : "errout",
        'users_chart'     : "users",
        'pf_state_entries_chart': "pf_state_entries",
    }

    results = monit.get_average(data_chart[chart])
    return JsonResponse({'results': results})

@group_required('administrator', 'application_manager', 'system_manager', 'security_manager')
def diagnostic(request):
    cluster = Cluster.objects.get()
    nodes   = cluster.members
    results = {}

    for node in nodes:
        if node.temporary_key:
            continue

        if node.is_dead:
            results[node.name] = None
            continue

        try:
            results[node.name] = {
                'id': str(node.id),
                'diagnostic': json.loads(node.diagnostic)
            }
            
        except:
            results[node.name] = None



    return render_to_response('monitor_diagnostic.html', {'results': results},
                              context_instance=RequestContext(request))

@group_required('administrator', 'application_manager', 'system_manager', 'security_manager')
def traffic(request):
    apps = []
    for app in Application.objects():
        if app.log_custom.repository_type == 'data':
            apps.append(app)

    if not request.is_ajax():
        cluster = Cluster.objects.get()

        loganalyser_settings = cluster.system_settings.loganalyser_settings
        rules = loganalyser_settings.loganalyser_rules

        tags = []
        for rule in rules:
            tags.extend(rule.tags.split(','))        

        return render_to_response('monitor_traffic.html', {'apps': apps, 'tags': set(tags)},
            context_instance=RequestContext(request))



    codes   = json.loads(request.POST['codes'])
    apps_id = json.loads(request.POST['apps_id'])
    tags    = json.loads(request.POST['tags'])
    if apps_id is not None:
        repos = {}
        for app_id in apps_id:
            app = Application.objects.with_id(ObjectId(app_id))
            try:
                repos[app.log_custom.repository].append(app)
            except:
                repos[app.log_custom.repository] = [app]

    else:
        repos = {}
        for app in apps:
            try:
                repos[app.log_custom.repository].append(app)
            except:
                repos[app.log_custom.repository] = [app]

    now    = datetime.datetime.utcnow()
    before = now - datetime.timedelta(minutes=10)

    params = {
        'codes'    : codes,
        'tags'     : tags,
        'startDate': before,
        'endDate'  : now
    }

    results, max_n = {}, 0
    for repo, apps in repos.items():
        params['apps'] = apps

        if repo.type_uri == 'mongodb':
            client = MongoDBClient(repo)

        elif repo.type_uri == 'elasticsearch':
            client = ElasticSearchClient(repo)

        for key, value in client.map(params).items():
            try:
                results[key] += value
            except KeyError:
                results[key] = value
                
            if value > max_n:
                max_n = value

    return JsonResponse({
        'results': results,
        'max'    : max_n
    })