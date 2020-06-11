#!/usr/bin/python
# -*- coding: utf-8 -*-
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
__author__ = "Kevin Guillemot"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = 'Django views dedicated to Monitoring Agents'


# Django system imports
from django.conf import settings
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

# Django project imports
from gui.decorators import group_required
from gui.forms.agents_settings import ZabbixAgentForm
from gui.forms.forms_utils import DivErrorList
from gui.models.system_settings import Cluster, Node

# Required exceptions imports
from bson.errors import InvalidId

# Extern modules imports
from bson.objectid import ObjectId
from time import sleep

# Logger configuration imports
import logging
logging.config.dictConfig(settings.LOG_SETTINGS)
logger = logging.getLogger('debug')


@group_required('administrator', 'system_manager')
def agent_zabbix_view(request, object_id=None):
    """ """
    # API url of zabbix-agent status
    api_url_zabbix = "/api/services/zabbix"

    # Retrieving cluster configuration
    cluster = Cluster.objects.get()
    zabbix_status = {}
    nodes = []
    popup = ""

    # Object_id is defined => we are configuring a Node
    if object_id:
        try:
            node_or_cluster = Node.objects.with_id(ObjectId(object_id))
            if not node_or_cluster:
                raise InvalidId()
        except InvalidId:
            return HttpResponseForbidden("Injection detected")

        system_settings = node_or_cluster.system_settings
        nodes.append(node_or_cluster)

        # Instantiate form
        form = ZabbixAgentForm(request.POST or None, instance=system_settings.zabbix_settings, node=node_or_cluster,
                               error_class=DivErrorList)

        # form validation
        if request.method == 'POST' and form.is_valid():
            zabbix_conf = form.save(commit=False)
            zabbix_conf.save()
            old_enabled = None
            if system_settings.zabbix_settings:
                old_enabled = system_settings.zabbix_settings.enabled

            system_settings.zabbix_settings = zabbix_conf
            # We are configuring Node
            node_or_cluster.save()

            action_service = ""
            # If the admin wants to disable the service
            if not zabbix_conf.enabled:
                action_service = "stop"
            elif not old_enabled:
                # If the field enabled was True and is false: stop service
                action_service = "start"
            else:
                action_service = "restart"

            if action_service:
                result = node_or_cluster.api_request("{}/{}/".format(api_url_zabbix, action_service))
                if not isinstance(result, bool):
                    popup = result['result']
                elif not result:
                    popup = ["ERROR", "Node {} is dead.".format(node_or_cluster.name)]
            # Sleep while service is stopping/starting before get its status
            sleep(2)
    else:
        form = ZabbixAgentForm(None)
        node_or_cluster = cluster
        nodes = node_or_cluster.members

    # Get status of cluster or node if object_id
    status = node_or_cluster.api_request("{}/status/".format(api_url_zabbix))

    # Keep database data up-to-date
    for node in nodes:
        if isinstance(status, bool) and not status:
            zabbix_status[node.name] = ("DEAD", "Cannot contact node ")
            continue
        node_info = status.get(node.name) or status

        if node_info:
            try:
                # If the object Zabbix of SystemSettings is not None
                if node.system_settings.zabbix_settings:
                    # Retrieve api/status result and set-it into Mongo
                    state = node_info.get('result', ["ERROR", "Cannot get api_request results"])
                    # And send the status to the HTML template
                    zabbix_status[node.name] = state
                    if node.system_settings.zabbix_settings.enabled and state[0] == "DOWN":
                        zabbix_status[node.name] = ["DOWN", "Please check zabbix log file"]
                else:
                    state = ("NOT CONFIGURED", "Please SAVE to configure node ")
                    zabbix_status[node.name] = state
            except Exception as e:
                logger.error("Zabbix::view: Error while trying to parse zabbix status : {}".format(e))

    return render_to_response('zabbix_agent.html',
                              {'form': form, 'zabbix_status': zabbix_status, 'cluster': cluster,
                               'object_id': object_id, 'popup': popup}, context_instance=RequestContext(request))
