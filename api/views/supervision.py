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
__doc__ = 'Django views dedicated to Vulture Service API'

import datetime
import logging
import re
from collections import OrderedDict

import maxminddb
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from gui.models.system_settings import Cluster
from portal.system.redis_sessions import REDISBase
from vulture_toolkit.monitor.utils import MonitorUtils
from vulture_toolkit.system.mongodb import MongoDB
from vulture_toolkit.system.ntp import NTP
from vulture_toolkit.system.pf import PF
from vulture_toolkit.system.redis_svc import RedisSvc
from vulture_toolkit.system.ssh import SSH
from vulture_toolkit.system.syslog import Rsyslogd
from vulture_toolkit.system.vlthaproxy import VLTHAProxy
from vulture_toolkit.system.ipsec import IPSEC
from vulture_toolkit.system.zabbix_agent import ZABBIX

logger = logging.getLogger('supervision_api')

@csrf_exempt
def realtime(request):
    try:
        node  = Cluster.objects.get().get_current_node()
        monit = MonitorUtils()

        return JsonResponse({
            'node': str(node.id),
            'boot': monit.boot_time,
            'cpu' : monit.cpu_percent,
            'mem' : monit.mem_percent,
            'swap': monit.swap_percent
        })
    except Exception as e:
        logger.error(e)
        raise

@csrf_exempt
def process_info(request):
    """ API call used to retrieve information about status of running Services, listeners and sessions

    :param request: Django request object
    :return: Json response with services status, running and stopped listeners, token sessions , application sessions and portal sessions
    """
    results = OrderedDict()
    services = (NTP, SSH, MongoDB, RedisSvc, PF, VLTHAProxy, Rsyslogd, IPSEC, ZABBIX)
    for svc in services:
        svc_instance = svc()
        svc_name = svc_instance.service_name
        tmp=svc_instance.status()
        if isinstance(tmp,tuple):
            results["Service "+svc_name] = tmp[0]
        else:
            results["Service "+svc_name] = tmp

    cluster = Cluster.objects.get()
    node = cluster.get_current_node()
    apps, apps_running, l_list, l_list_running = node.get_applications(both=True)
    nb_apps = len(apps)
    nb_running = len(apps_running)
    nb_l=len(l_list)
    nb_l_running=len(l_list_running)
    results['Running applications'] = str(nb_running)+" / "+str(nb_apps)
    results['Running listeners'] = str(nb_l_running)+" / "+str(nb_l)

    app_se = 0
    port_se = 0
    oauth2_se = 0
    pass_se = 0
    tok = 0
    ua = 0

    try:
        r = REDISBase()
        for key in r.r.scan_iter("*"):

            #Vulture key are 'huge', others are modSecurity or mailtrail ones
            if (len(key) < 40 or ":" in key or key.startswith("ctx_") or key.endswith("_rqs") or key.endswith("_limit")) and not key.startswith("col_"):
                continue

            elif key.startswith("col_ua:"):
                    """ User-Agent entries """
                    ua += 1

            elif key.startswith("oauth2_"):
                    """ This is an OAuth2 session """
                    oauth2_se += 1
            elif key.startswith("password_reset_"):
                    """ This is a Password reset temporary token """
                    pass_se += 1
            else:
                m = re.search('[a-z0-9]{64}', key)
                if m:

                    """ Temporary mod_vulture Token """
                    if r.get(key):
                        tok += 1
                    else:
                        """ This is an application session """
                        app_se += 1
                else:
                    """ This is a portal session """
                    port_se += 1
    except Exception as e:
        results['Reputation'] = " Redis Problem: {}".format(str(e))

    try:
        reader = maxminddb.open_database('/var/db/loganalyzer/ip-reputation.mmdb')
        results['Reputation'] = reader.metadata().node_count
        reader.close()
    except Exception as e:
        results['Reputation'] = "Not loaded !"

    results['Application Tokens'] = app_se
    results['Portal Tokens'] = port_se
    results['OAuth2 Tokens'] = oauth2_se
    results['Password Tokens'] = pass_se
    results['Temporary Tokens'] = tok
    results['UA Entries'] = ua

    return JsonResponse(results)


@csrf_exempt
def system_time_info(request):
    """
    Return the current system time
    :param request: Django request object
    :return:
    """
    try:
        now = datetime.datetime.now()
        response = {'status': True, 'time': now.strftime("%Y-%m-%dT%H:%M:%SZ")}
    except:
        response = {'status': False}

    return JsonResponse(response)
