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
import logging

from bson import ObjectId
from django.http import JsonResponse
from django.shortcuts import render_to_response
from django.template import RequestContext

from gui.decorators import group_required
from gui.models.application_settings import Application
from gui.models.monitor_settings import Monitor
from gui.models.system_settings import Cluster
from gui.models.system_settings import Node
from vulture_toolkit.log.elasticsearch_client import ElasticSearchClient
from vulture_toolkit.log.mongodb_client import MongoDBClient
from vulture_toolkit.monitor.data import MonitorData
from vulture_toolkit.log.exceptions import ClientLogException

logger = logging.getLogger('debug')

@group_required('administrator', 'application_manager', 'system_manager', 'security_manager')
def map_traffic(request):
    apps = []
    for app in Application.objects():
        if app.log_custom.repository_type == 'data':
            apps.append(app)
    apps.sort(key=lambda x: x.name)

    if not request.is_ajax():
        cluster = Cluster.objects.get()

        loganalyser_settings = cluster.system_settings.loganalyser_settings
        rules = loganalyser_settings.loganalyser_rules

        tags = []
        for rule in rules:
            tags.extend(rule.tags.split(','))

        return render_to_response('report_map.html', {'apps': apps, 'tags': set(tags)},
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

    errors = []

    results, max_n = {}, 0
    try:
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

    except ClientLogException as e:
        errors.append(str(e))

    return JsonResponse({
        'results': results,
        'max'    : max_n,
        'errors' : errors
    })

@group_required('administrator', 'application_manager', 'system_manager', 'security_manager')
def report_access(request):
    apps = []

    for app in Application.objects():
        if app.log_custom.repository_type == 'data':
            apps.append(app)
    apps.sort(key=lambda x: x.name)

    if not request.is_ajax():
        return render_to_response('report_access.html', {'apps': apps}, context_instance=RequestContext(request))


@group_required('administrator', 'application_manager', 'system_manager', 'security_manager')
def report_security(request):
    apps = []
    for app in Application.objects():
        if app.log_custom.repository_type == 'data':
            apps.append(app)
    apps.sort(key=lambda x: x.name)

    if not request.is_ajax():
        return render_to_response('report_security.html', {'apps': apps}, context_instance=RequestContext(request))

@group_required('administrator', 'application_manager', 'system_manager', 'security_manager')
def report_pf(request):
    apps = []
    for app in Application.objects():
        if app.log_custom.repository_type == 'data':
            apps.append(app)
    apps.sort(key=lambda x: x.name)

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

    if not request.is_ajax():
        return render_to_response('report_pf.html', {'apps': apps, 'packet_filter': packet_filter}, context_instance=RequestContext(request))


@group_required('administrator', 'application_manager', 'system_manager', 'security_manager')
def report_data(request):

    daterange = json.loads(request.POST['daterange'])
    params = {
        'startDate': daterange['startDate'],
        'endDate': daterange['endDate'],
        'reporting_type': request.POST['reporting_type']
    }

    errors = []

    if request.POST['reporting_type'] in ('access', 'security'):
        apps = []
        apps_id = json.loads(request.POST['apps'])
        if apps_id is not None:
            repos = {}
            for app_id in apps_id:
                app = Application.objects.with_id(ObjectId(app_id))
                try:
                    repos[app.log_custom.repository].append(app)
                except:
                    repos[app.log_custom.repository] = [app]
        else:
            for app in Application.objects():
                if app.log_custom.repository_type == 'data':
                    apps.append(app)

            repos = {}
            for app in apps:
                try:
                    repos[app.log_custom.repository].append(app)
                except:
                    repos[app.log_custom.repository] = [app]

        params['type_logs'] = 'access'

        results = {}
        for repo, apps in repos.items():
            params['apps'] = apps
            try:
                if repo.type_uri == 'mongodb':
                    client = MongoDBClient(repo)

                elif repo.type_uri == 'elasticsearch':
                    client = ElasticSearchClient(repo)

                aggregation = client.aggregate(params)
                if results:
                    results = client.merge_aggregations(aggregation, results)
                else:
                    results = aggregation
            except ClientLogException as e:
                errors.append(str(e))

        results = client.fill_data(results)

    elif request.POST['reporting_type'] == 'packet_filter':
        node_id = request.POST['node']
        results = {}

        node = Node.objects.with_id(ObjectId(node_id))
        repo = node.system_settings.pf_settings.repository

        params['type_logs'] = 'packet_filter'
        params['node'] = node.name
        try:
            if repo.type_uri == 'mongodb':
                client = MongoDBClient(repo)
                results = client.aggregate(params)

            elif repo.type_uri == 'elasticsearch':
                client = ElasticSearchClient(repo)
                results = client.aggregate(params)

        except ClientLogException as e:
            errors.append(str(e))

        results = client.fill_data(results)

    return JsonResponse({
        'results': results,
        'errors': errors
    })
