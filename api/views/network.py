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
__author__ = "Florian Hagniel"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = 'Django views dedicated to Vulture Network API'

import logging
import json

from bson.objectid import ObjectId
from django.http import HttpResponseForbidden, JsonResponse
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_exempt

from gui.models.application_settings import ListenAddress
from gui.models.network_settings import Interface, Listener
from gui.models.rewrite_settings import Rewrite
from gui.models.system_settings import Cluster, Node
from vulture_toolkit.network import net_utils
logger = logging.getLogger('local_listeners')


def running(request, listener_id, port):
    """ View dedicated to check if there is a process listening on the specified interface:port

        :param request: Django request object
        :param listener_id: Listener id

    """
    l = Listener.objects.with_id(ObjectId(listener_id))
    status = net_utils.is_running(l.ip, port)
    response = {'status': status}
    return JsonResponse(response)


def reloadListener(request, listenaddress_id):
    rewrite_rules = Rewrite.objects()
    listenaddress = ListenAddress.objects.with_id(ObjectId(listenaddress_id))

    try:
        ## Saving previous configuration
        if not listenaddress.saveConf():
            return JsonResponse({'status': False, 'errors': str(_('An error has occurred during backup of previous configuration'))})

        ## Build the new configuration
        conf = listenaddress.getConf(rewrite_rules)
        if conf.get('error', False):
            logger.error("An error occured during creation of new configuration : {}".format(conf.get('error')))
            return JsonResponse({'status': False, 'errors': str(_("An error has occurred during creation of new configuration : {}".format("</br>"+conf.get('error'))))})

        if not listenaddress.buildConf(conf['config']):
            logger.error("An error occured during creation of new configuration : buildConf has failed")
            return JsonResponse({'status': False, 'errors': str(_("An error has occurred during creation of new configuration"))})

        ## Perform graceful of the listener only if it is running
        if not net_utils.is_running(listenaddress.address.ip, listenaddress.port):
            return JsonResponse({'status': True})

        status = listenaddress.graceful()
        if not status.get('status'):
            listenaddress.restoreConf()
            return JsonResponse({'status': False, 'errors': str(status.get('error'))})
    
    except Exception as e:
        logger.error("Error while trying to reload Listener : ")
        logger.exception(e)
        return JsonResponse({
            'status': False,
            'errors': str(e)
        })

    return JsonResponse({'status': status.get('status'), 'errors': False})


def restoreConf(request, listenaddress_id):
    listenaddress = ListenAddress.objects.with_id(ObjectId(listenaddress_id))
    status = listenaddress.restoreConf()
    response = {'status': status}
    return JsonResponse(response)


def need_restart(request, listenaddress_id):
    listenaddress = ListenAddress.objects.with_id(ObjectId(listenaddress_id))
    status = listenaddress.need_restart()
    response = {'status': status}
    return JsonResponse(response)


@csrf_exempt
def start(request, listenaddress_id):
    """ View dedicated to start an Apache process on the specified listener
        :param request: Django request object
        :param listenaddress_id: ListenAddress id

    """
    passphrases = {}
    if request.method == 'POST':
        try:
            passphrases = json.loads(request.body)
        except Exception as e:
            logger.error("Failed to parse request body trying to start listener '{}' : {}".format(listenaddress_id, e))
    l = ListenAddress.objects.with_id(ObjectId(listenaddress_id))
    status = l.start(passphrases)
    response = {'status': status}
    return JsonResponse(response)


def stop(request, listenaddress_id):
    """ View dedicated to stop an Apache process on the specified listener
        :param request: Django request object
        :param listener_id: Listener id
    """
    l = ListenAddress.objects.with_id(ObjectId(listenaddress_id))
    status = l.stop()
    response = {'status': status}
    return JsonResponse(response)



def status(request, listenaddress_id):
    l = ListenAddress.objects.with_id(ObjectId(listenaddress_id))
    status = net_utils.is_running(l.address.ip, l.port)
    if not status:
        response = {'status': 'stop'}
    else:
        response = {'status': 'run'}

    return JsonResponse(response)

def statusfull(request, listenaddress_id):
    l = ListenAddress.objects.with_id(ObjectId(listenaddress_id))
    status = net_utils.is_running(l.address.ip, l.port)
    if not status:
        response = {'status': 'stop'}
    else:
        response = {'status': 'run'}

    is_up2date = l.is_up2date
    if is_up2date is False:
        response['need_restart'] = 'true'
    else:
        response['need_restart'] = 'false'

    return JsonResponse(response)

def up(request, inet_id):
    """ API call used to start an network interface

    :return:
    """
    cluster = Cluster.objects.get()
    current_node = cluster.get_current_node()
    # Retrieving inet and intf objects which need update
    inet = Listener.objects.with_id(ObjectId(inet_id))
    intf = Interface.objects.get(inet_addresses=inet)
    node = Node.objects.get(interfaces=intf)

    previous_conf = inet.get_previous_inet()

    # Ensure intf object correspond to current node
    if current_node == node:
        logger.info("Starting inet " + inet.alias + " (" + inet.ip + ") on node " + current_node.name)
        inet_helper = inet.as_inet_helper()
        status, error = inet_helper.up(intf.device)
        response = {'status': status, 'error': error}
    else:
        logger.error("Node are not corresponding. Current node is : {}. Inet is located on".format(current_node, node))
        return HttpResponseForbidden()
    return JsonResponse(response)


def down(request, inet_id):
    """ API call used to stop an network interface

    :return:
    """
    cluster = Cluster.objects.get()
    current_node = cluster.get_current_node()

    # Retrieving inet and intf objects which need update
    inet = Listener.objects.with_id(ObjectId(inet_id))

    # Retrieving previous inet configuration to shut down it
    previous_conf = inet.get_previous_inet()
    if previous_conf is not None:
        inet, intf, node = previous_conf
    else:
        intf = Interface.objects.get(inet_addresses=inet)
        node = Node.objects.get(interfaces=intf)

    # Ensure intf object correspond to current node
    if current_node == node:
        logger.info("Stopping inet " + inet.alias + " (" + inet.ip + ") on node " + current_node.name)
        inet_helper = inet.as_inet_helper()
        status, error = inet_helper.down(intf.device)
        response = {'status': status, 'error': error}
    else:
        logger.error("Node are not corresponding. Current node is : {}. Inet is located on".format(current_node, node))
        return HttpResponseForbidden()

    return JsonResponse(response)
