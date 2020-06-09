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
__author__ = "Olivier de Régis"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = 'Django views dedicated to Proxy Balancer rules'

from django.shortcuts import render_to_response
from django.template import RequestContext

from gui.decorators import group_required
from gui.models.system_settings import Cluster
from gui.signals.gui_signals import config_modified


@group_required('administrator', 'system_manager')
def topology(request):
    cluster = Cluster.objects.get()
    global_settings = cluster.system_settings.global_settings
    reload_apps = False # Reload the applications when a field is modified

    if request.method == "POST":
        remote_ip_internal_proxy                 = request.POST['remote_ip_internal_proxy'].split(',')
        reload_apps                              = (global_settings.remote_ip_internal_proxy != remote_ip_internal_proxy)
        global_settings.remote_ip_internal_proxy = remote_ip_internal_proxy
        cluster.system_settings.global_settings  = global_settings
        cluster.save()
        if reload_apps:
            config_modified.send(sender=Cluster, id=None)

    return render_to_response('topology.html', {
        'remote_ip_internal_proxy': ','.join(global_settings.remote_ip_internal_proxy),
        'reload_apps':reload_apps}, context_instance=RequestContext(request))

