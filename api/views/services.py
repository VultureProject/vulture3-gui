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
__author__ = "Jérémie Jourdin"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = 'Django views dedicated to Vulture Service API'

from django.http import HttpResponseForbidden, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from gui.models.system_settings import Cluster
from vulture_toolkit.system.exceptions import ServiceError

""" These import are needed for
  class_name = service_name.upper()
  cls = globals().get(class_name)
"""
from vulture_toolkit.system.ssh import SSH
from vulture_toolkit.system.ntp import NTP
from vulture_toolkit.system.pf import PF
from vulture_toolkit.system.dns import DNS
from vulture_toolkit.system.ipsec import IPSEC
from vulture_toolkit.system.zabbix_agent import ZABBIX
from vulture_toolkit.system.smtp import SMTP

authorized_services = ('ntp', 'smtp', 'dns', 'ssh', 'pf', 'ipsec', 'zabbix')

import logging
logger = logging.getLogger('services_events')


@csrf_exempt
def start(request, service_name):
    """ Start service call

    :param request: Django request object
    :param service_name: Name of service to start (must be in authorized_services)
    """
    if service_name not in authorized_services:
        return HttpResponseForbidden()

    # Trying to retrieve service configuration from node settings
    cluster = Cluster.objects.get()
    node = cluster.get_current_node()
    settings_name = service_name + '_settings'
    # If the node has a service settings and it's not a "cluster_based_conf"
    if getattr(node.system_settings, settings_name, None) is not None and \
            not getattr(getattr(node.system_settings, settings_name), "cluster_based_conf", False):
        # Use the node configuration
        settings = getattr(node.system_settings, settings_name)
    else:
        # Otherwise, use cluster settings for configuration
        settings = getattr(cluster.system_settings, settings_name)

    if settings is not None:
        settings = settings.to_template()

    """Service class instantiation
    """
    class_name = service_name.upper()
    cls = globals().get(class_name)
    if cls is not None:
        service_inst = cls()
        try:
            service_inst.write_configuration(settings)
            # Return result of command
            response = {'result': service_inst.start_service()}
        except ServiceError as e:
            # In case of error, return the error message
            response = {'result': ('ERROR', "Failed to {} service {}: {}".format(e.trying_to, service_name,
                                                                                 e.message))}
        return JsonResponse(response)
    else:
        return HttpResponseForbidden()


@csrf_exempt
def stop(request, service_name):
    """ Stop service call

    :param request: Django request object
    :param service_name: Name of service to start (must be in authorized_services)
    """
    if service_name not in authorized_services:
        return HttpResponseForbidden()

    """Service class instantiation
    """
    class_name = service_name.upper()
    cls = globals().get(class_name)
    if cls is not None:
        service_inst = cls()
        try:
            # Return result of command
            response = {'result': service_inst.stop_service()}
        except ServiceError as e:
            # In case of error, return the error message
            response = {'result': ('ERROR', "Failed to {} service {}: {}".format(e.trying_to, service_name,
                                                                                 e.message))}
        return JsonResponse(response)
    else:
        return HttpResponseForbidden()


@csrf_exempt
def restart(request, service_name):
    """ Start service call

    :param request: Django request object
    :param service_name: Name of service to start (must be in authorized_services)
    """
    if service_name not in authorized_services:
        return HttpResponseForbidden()

    # Trying to retrieve service configuration from node settings
    cluster = Cluster.objects.get()
    node = cluster.get_current_node()
    settings_name = service_name + '_settings'
    # If the node has a service settings and it's not a "cluster_based_conf"
    if getattr(node.system_settings, settings_name, None) is not None and \
            not getattr(getattr(node.system_settings, settings_name), "cluster_based_conf", False):
        # Use the node configuration
        settings = getattr(node.system_settings, settings_name)
    else:
        # Otherwise, use cluster settings for configuration
        settings = getattr(cluster.system_settings, settings_name)

    if settings is not None:
        settings = settings.to_template()

    class_name = service_name.upper()
    cls = globals().get(class_name)
    if cls is not None:
        service_inst = cls()
        try:
            service_inst.write_configuration(settings)
            # Return result of command
            response = {'result': service_inst.restart_service()}
        except ServiceError as e:
            logger.exception(e)
            # In case of error, return the error message
            response = {'result': ('ERROR', "Failed to {} service {}: {}".format(e.trying_to, service_name,
                                                                                 e.message))}
        return JsonResponse(response)
    else:
        return HttpResponseForbidden()


@csrf_exempt
def status(request, service_name):
    """ Status service call

    :param request: Django request object
    :param service_name: Name of service to start (must be in authorized_services)
    """
    if service_name not in authorized_services:
        return HttpResponseForbidden()

    # Trying to retrieve service configuration from node settings
    cluster = Cluster.objects.get()
    node = cluster.get_current_node()
    settings_name = service_name + '_settings'
    # If the node has a service settings and it's not a "cluster_based_conf"
    if getattr(node.system_settings, settings_name, None) is not None and \
            not getattr(getattr(node.system_settings, settings_name), "cluster_based_conf", False):
        # Use the node configuration
        settings = getattr(node.system_settings, settings_name)
    else:
        # Otherwise, use cluster settings for configuration
        settings = getattr(cluster.system_settings, settings_name)

    if settings is not None:
        settings = settings.to_template()

    class_name = service_name.upper()
    cls = globals().get(class_name)
    if cls is not None:
        service_inst = cls()
        try:
            response = {'result': service_inst.status(settings)}
        except ServiceError as e:
            # In case of error, return the error message
            logger.exception(e)
            response = {'result': ('ERROR', "Failed to {} service {}: {}".format(e.trying_to, service_name,
                                                                                 e.message))}
        return JsonResponse(response)
    else:
        return HttpResponseForbidden()


@csrf_exempt
def redis_master(request):
    from vulture_toolkit.system.redis_svc import RedisSvc
    redis = RedisSvc()
    response = {
        'master_ip': redis.get_master_ip()
    }
    return JsonResponse(response)
