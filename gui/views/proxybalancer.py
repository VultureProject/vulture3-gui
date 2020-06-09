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
__doc__ = 'Django views dedicated to Proxy Balancer rules'


import re

from bson.objectid import ObjectId
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

from gui.decorators import group_required
from gui.forms.forms_utils import DivErrorList
from gui.forms.balancer_settings import ProxyBalancerForm
from gui.models.application_settings import ProxyBalancer, ProxyBalancerMember
from gui.signals.gui_signals import config_modified

@group_required('administrator', 'application_manager')
def balancer_list(request):
    """ Page dedicated to show balancer list
    """
    try:
        balancers = ProxyBalancer.objects()
    except DoesNotExist:
        balancers = None

    return render_to_response('proxybalancer.html', {'balancers': balancers}, context_instance=RequestContext(request))


@group_required('administrator', 'application_manager')
def clone(request, object_id=None):

    """ View dedicated to proxy balancer cloning

    :param object_id: MongoDB object_id of a proxybalancer
    :param request: Django request object
    """
    #Retrieving rewriting configuration
    balancer = ProxyBalancer.objects.with_id(ObjectId(object_id))

    members = balancer.members
    members_list = list()
    for member in members:
        member.pk=None
        member.save()
        members_list.append(member)

    balancer.pk = None
    balancer.name = 'Copy of ' + str (balancer.name)
    balancer.members = members_list
    balancer.save()

    return HttpResponseRedirect('/network/proxybalancer/')


@group_required('administrator', 'application_manager')
def edit(request, object_id=None):

    """ View dedicated to proxy balancer management

    :param object_id: MongoDB object_id of a proxybalancer
    :param request: Django request object
    """
    # Retrieving rewriting configuration
    balancer = ProxyBalancer.objects.with_id(ObjectId(object_id))

    # ProxyBalancer doesn't exist ==> create it
    if not balancer:
        balancer = ProxyBalancer(name="My Proxy Balancer")


    form = ProxyBalancerForm(request.POST or None, instance=balancer, error_class=DivErrorList)

    members = []
    if request.method == 'POST':
        dataPosted      = request.POST
        dataPostedRaw   = str(request.body).split("&")
        for data in dataPostedRaw:

            # Members management
            m = re.match('uri_type_(\d+)',data)
            if m is not None:
                id_ = m.group(1)

                # Force harmless default values to prevent any injection or jQuery problem
                uri_type        = dataPosted.get('uri_type_' + id_, "http")
                uri             = dataPosted.get('uri_' + id_, '192.168.1.1')
                # Boolean fields
                disablereuse = True if dataPosted.get('disablereuse_' + id_) else False
                keepalive =  True if dataPosted.get('keepalive_' + id_) else False
                lbset           = dataPosted.get('lbset_' + id_, 0)
                retry           = dataPosted.get('retry_' + id_, 60)
                route           = dataPosted.get('route_' + id_, "")
                timeout         = dataPosted.get('timeout_' + id_, 60)
                ttl             = dataPosted.get('ttl_' + id_, "")
                config          = dataPosted.get('config_' + id_, "")

                #FIXME: Coherence control
                member = ProxyBalancerMember(uri_type, uri, disablereuse, keepalive, lbset, retry, route, timeout, ttl, config)
                members.append(member)
    else:
        members = balancer.members

    # Saving information into database and redirect to balancer list
    if request.method == 'POST' and form.is_valid():

        # Verify coherence of backends type
        member_type = ""
        for member in members:
            if member_type and member.uri_type != member_type:
                form.add_error('members', "You cannot set different types of backend.")
                break
            else:
                member_type = member.uri_type

        if form.errors:
            return render_to_response('proxybalancer_edit.html',
                                      {'form': form, 'object_id': object_id, 'balancername': balancer.name,
                                       'members': members},
                                      context_instance=RequestContext(request))

        #1) Remove old members
        old_balancer = ProxyBalancer.objects.with_id(ObjectId(object_id))
        if old_balancer and old_balancer.members:
            for member in old_balancer.members:
                member.delete()


        #2) Create new members
        for member in members:
            member.save()


        #3) Assign members
        balancer = form.save(commit=False)
        balancer.members = members

        #4) Save balancer
        balancer.save()
        config_modified.send(sender=ProxyBalancer, id=balancer.id)

        return HttpResponseRedirect('/network/proxybalancer/#reload')

    return render_to_response('proxybalancer_edit.html',
                              {'form':form, 'object_id': object_id,'balancername':balancer.name, 'members':members},
                              context_instance=RequestContext(request))


