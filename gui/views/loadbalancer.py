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

import json

from bson.objectid import ObjectId
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

from gui.decorators import group_required
from gui.forms.network_settings import LoadbalancerForm
from gui.models.network_settings import Loadbalancer, LoadbalancerBackend, Listener


@group_required('administrator', 'system_manager')
def loadbalancer(request):
    # List and categorize inet (carp or not) to render them in template
    loadbalancers = Loadbalancer.objects.all()
    return render_to_response('loadbalancer.html', {
        'loadbalancers': loadbalancers
    }, context_instance=RequestContext(request))


@group_required('administrator', 'system_manager')
def edit_loadbalancer(request, object_id=None):
    loadbalancer = None
    if object_id:
        loadbalancer = Loadbalancer.objects.with_id(ObjectId(object_id))

    form = LoadbalancerForm(request.POST or None, instance=loadbalancer)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)

        """ HA-PROXY dislikes whitespace """
        obj.name = obj.name.replace(" ","_")
        obj.backends = []

        if object_id:
            for backend in loadbalancer.backends:
                backend.delete()

        backends = json.loads(request.POST['backends'])

        for backend in backends:
            try:
                port=int(backend['port'])
            except:
                port=80

            try:
                weight=int(backend['weight'])
            except:
                weight=1

            b = LoadbalancerBackend(
                host=backend['host'].replace(" ","_"),
                ip=backend['ip'],
                port=port,
                weight=weight,
                tls=backend['tls'],
                send_proxy=backend.get('send_proxy', "off") == "on"
            )

            b.save()
            obj.backends.append(b)

        obj.save()

        return HttpResponseRedirect("/network/loadbalancer/")

    listeners, vhid_list = [], []
    for inet in Listener.objects():
        listener = dict()
        if inet.is_carp and inet.carp_vhid not in vhid_list:
            nodes = list()
            intfs = inet.get_related_carp_intfs()
            for intf in intfs:
                nodes.append(intf.get_related_node())

            listener['node'] = nodes
            listener['intf'] = intfs
            listener['inet'] = inet
            vhid_list.append(inet.carp_vhid)

        elif inet.carp_vhid in vhid_list:
            continue

        else:
            listener['node'] = inet.get_related_node()
            listener['intf'] = inet.get_related_interface()
            listener['inet'] = inet
        
        listeners.append(listener)

    backends = []
    try:
        for backend in loadbalancer.backends:
            backends.append({
                'host'  : backend.host,
                'ip'    : backend.ip,
                'port'  : backend.port,
                'weight': backend.weight,
                'tls': backend.tls,
                'send_proxy': backend.send_proxy
            })
    except AttributeError:
        pass

    return render_to_response('loadbalancer_edit.html', {
        'form'        : form,
        'listeners'   : listeners,
        'loadbalancer': loadbalancer,
        'backends'    : json.dumps(backends)
    },context_instance=RequestContext(request))

