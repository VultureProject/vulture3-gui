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
__author__ = "Jérémie Jourdin"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = 'Django views dedicated to management of Vulture listeners'

from bson.objectid import ObjectId
from django.http import JsonResponse
from django.shortcuts import loader, HttpResponse
from django.utils.translation import ugettext_lazy as _

from gui.decorators import group_required
from gui.models.application_settings import Application, ListenAddress
from gui.models.rewrite_settings import Rewrite

import json
import re
import logging
logger = logging.getLogger('debug')


@group_required('administrator', 'application_manager', 'security_manager')
def start(request, object_id=None):
    """ Start a Vulture listener on a (possibly) remote host
    :param object_id: MongoDB object_id of listener to start
    :param request: Django request object
    """
    l = ListenAddress.objects.with_id(ObjectId(object_id))

    # Populate a dict with passphrases, if any
    passphrases = None
    if request.POST:
        passphrases = dict()
        for data in request.POST:
            # Listener management
            m = re.match('keypass_([A-Fa-f0-9]{24})', data)
            if m != None:
                id_ssl_profile = m.group(1)
                passphrases["ssl_{}".format(id_ssl_profile)] = request.POST.get("keypass_{}".format(id_ssl_profile))
    else:
        # Check if there is the need to provide a pass phrase to start a listener
        need_passphrase = False
        for app in l.get_apps():
            if app.need_passphrase():
                need_passphrase = True
        if need_passphrase:
            var = loader.render_to_string('application_askpass.html', {'listener': l})
            ret = {
                'status': False,
                'need_pass': True,
                'html': var
            }
            return JsonResponse(ret)
    return start_api(request, object_id, passphrases)


@group_required('administrator', 'application_manager', 'security_manager')
def start_api(request, object_id=None, passphrases=None):
    """ Start a Vulture listener on a (possibly) remote host
    :param object_id: MongoDB object_id of listener to start
    :param request: Django request object
    """
    l      = ListenAddress.objects.with_id(ObjectId(object_id))
    node   = l.address.get_related_node()
    status = node.api_request("/api/network/listener/start/{}".format(l.id), passphrases, timeout=20)

    if status is False:
        ret = {
            'status': False,
            'errors': str(_("An error has occured"))
        }

    elif status['status'] is True:
        ret = {
            'status': True,
            'msg': str(_('Listener successfully started'))
        }
    else:
        ret = {
            'status': False,
            'errors': status.get('status')
        }
    return JsonResponse(ret)


@group_required('administrator', 'application_manager', 'security_manager')
def stop(request, object_id=None):
    """ Start a Vulture listener on a (possibly) remote host
    :param object_id: MongoDB object_id of listener to start
    :param request: Django request object
    """
    l      = ListenAddress.objects.with_id(ObjectId(object_id))
    node   = l.address.get_related_node()
    status = node.api_request("/api/network/listener/stop/%s" % (str(l.id)), timeout=20)
    
    if status is False:
        ret = {
            'status': False,
            'errors': str(_("An error has occured"))
        }

    elif status['status'] is True:
        ret = {
            'status': True,
            'msg': str(_('Listener successfully stopped'))
        }
    else:
        ret = {
            'status': False,
            'errors': status.get('status')
        }

    return JsonResponse(ret)


@group_required('administrator', 'application_manager', 'security_manager')
def reload(request, object_id=None):
    """ Build or rebuild the corresponding Apache configuration file and start or restart associated apps
    :param object_id: MongoDB object_id of listener to reload
    :param request: Django request object
    """

    listener = ListenAddress.objects.with_id(ObjectId(object_id))
    node = listener.address.get_related_node()

    # ...save the previous configuration
    logger.debug ("reload::saveConf of listener '{}'".format(listener.id))
    status = node.api_request('/api/network/listener/reloadlistener/{}'.format(str(listener.id)), timeout=20)
    if status and not status.get('status'):
        return JsonResponse({
            'status': False,
            'errors': status.get('errors')
        })

    elif not status:
        return JsonResponse({
            'status': False,
            'errors': _('An error has occurred during reload listener')
        })

    """ Update all listener that shares the same IP:port """
    listenaddress_all = ListenAddress.objects.filter(address=listener.address, port=listener.port)
    for l in listenaddress_all:
        l.is_up2date = True
        l.save()

    return JsonResponse({
        'status': True,
        'msg': str(_('Listener successfully restarted'))
    })

@group_required('administrator', 'application_manager', 'security_manager')
def reloadapp(request, object_id=None):
    """
        Reload the listener of an application
    """

    app = Application.objects.with_id(ObjectId(object_id))
    listeners = app.listeners

    results = []
    for listener in listeners:
        node = listener.address.get_related_node()
        results.append(reload(request=request, object_id=str(listener.id)))

    response = {
        'status': True,
        'msg': str(_('Application successfully restarted'))
    }
    
    for result in results:
        result = json.loads(result.content)
        if not result['status']:
            response = {
                'status': False,
                'errors': result['error']
            }

    return JsonResponse(response)

@group_required('administrator', 'application_manager', 'security_manager')
def reloadall(request):
    results, done, info = [], [], []

    for listener in ListenAddress.objects():
        node = listener.get_related_node()

        ssl = ""
        if listener.ssl_profile:
            ssl = str(listener.ssl_profile.name)

        key  = "{}:{}:{}:{}".format(str(listener.address), str(listener.port), str(node), ssl)
        if key in done:
            continue

        elif listener.is_up2date:
            logger.debug("reloadall::Listener '{}' do not need to be restarted".format(key))

        logger.debug("reloadall::Dealing with listener '{}'".format(key))
        results.append({'listener': key, 'result': json.loads(reload(request=request, object_id=str(listener.id)).content)})
        
        done.append(key)

    msg_errors = []
    for result in results:
        if not result['result']['status']:
            msg_errors.append("<b>" + result['listener'] + "</b>" + " " + result['result']['errors'])

    if msg_errors:
        return JsonResponse({
            'status': False,
            'errors': "<br/>".join(msg_errors)
        })
    
    return JsonResponse({
        'status': True,
        'msg'   : str(_('All listeners successfully restarted'))
    })


@group_required('administrator', 'application_manager', 'security_manager')
def startall(request):
    results = list()
    done=list()
    for listen_address in ListenAddress.objects.all():
        key=str(listen_address.address) + ":" + str(listen_address.port)
        if key in done:
            logger.debug ("startall::Listener '{}' already done".format (key))
            continue

        info = list()
        listener = str(listen_address.id)
        info.append(start(request=request, object_id=listener))
        info.append(str(listen_address.address) + ":" + str(listen_address.port))
        results.append(info)
        done.append(key)

    ret_final = {'status': True,
                 'msg': str(_('All listeners successfully started'))}
    for result in results:
        ret = json.loads(result[0].content)
        if not ret['status']:
            ret_final = {'status': False, 'errors': "<b>"+result[1]+"</b>" + " " + ret['errors']}
            break
    return JsonResponse(ret_final)

@group_required('administrator', 'application_manager', 'security_manager')
def stopall(request):
    results = list()
    done=list()
    for listen_address in ListenAddress.objects.all():
        key=str(listen_address.address) + ":" + str(listen_address.port)
        if key in done:
            logger.debug ("stopall::Listener '{}' already done".format (key))
            continue
        info = list()
        listener = str(listen_address.id)
        info.append(stop(request=request, object_id=listener))
        info.append(str(listen_address.address) + ":" + str(listen_address.port))
        results.append(info)
        done.append(key)

    ret_final = {'status': True,
                 'msg': str(_('All listeners successfully stopped'))}
    for result in results:
        ret = json.loads(result[0].content)
        if not ret['status']:
            ret_final = {'status': False, 'errors': "<b>"+result[1]+"</b>" + " " + ret['errors']}
            break
    return JsonResponse(ret_final)

@group_required('administrator', 'application_manager', 'security_manager')
def download(request, object_id=None):

    """ Returns the corresponding Apache configuration file
    :param object_id: MongoDB object_id of listener
    :param request: Django request object
    """
    rewrite_rules = Rewrite.objects()
    listener = ListenAddress.objects.with_id(ObjectId(object_id))
    new_conf = ""

    conf = listener.getConf(rewrite_rules)

    config = conf['config']
    error = conf['error']

    if error:
        return HttpResponse(error)

    new_conf += "# CONFIGURATION FOR LISTENER " + str(listener.address.ip) + ":" + str (listener.port) + "\n" + config + "\n"
    return HttpResponse(new_conf, content_type='text/plain; charset=utf-8')


def status(request, object_id):
    app = Application.objects.with_id(ObjectId(object_id))
    if app:
        if not app.enabled:
            return JsonResponse({'status': 'down'})

        running = 'down'
        for l in app.listeners:
            node = l.get_related_node()
            status = node.api_request("/api/network/listener/status/{}".format(l.id))
            if status["status"] == 'run':
                running = "run"
                break

        return JsonResponse({
            'status': running
        })

    return JsonResponse({'status': 'Error'})

def statusfull(request, object_id):
    l = ListenAddress.objects.with_id(ObjectId(object_id))
    if l:
        node = l.get_related_node()
        status = node.api_request("/api/network/listener/statusfull/%s" % (str(l.id)))
        """ Status may be False if api request failed or timeout """
        if status:
            return JsonResponse(status)

    return JsonResponse({'status': 'Error'})