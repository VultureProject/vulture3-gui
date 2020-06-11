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
__author__ = "Florian Hagniel"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = 'Django views dedicated to network configuration'

import logging
import re

import ipaddress
from bson.objectid import ObjectId
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.crypto import get_random_string
from django.utils.translation import ugettext_lazy as _

from gui.decorators import group_required
from gui.forms.network_settings import InetAddressForm
from gui.models.network_settings import Listener, Interface
from gui.models.system_settings import Cluster, Node

logger = logging.getLogger('listeners')


@group_required('administrator', 'system_manager')
def inet_list(request):
    """ Page dedicated to show inet list for a cluster's nodes
    """

    inets = Listener.objects()
    listeners = list()
    vhid_list = list()
    # List and categorize inet (carp or not) to render them in template
    for inet in inets:
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


    return render_to_response('network.html',
                              {'listeners': listeners},
                              context_instance=RequestContext(request))


@group_required('administrator', 'system_manager')
def edit_inet(request, object_id=None):
    """
    """
    inet         = None
    intf         = None
    carp_inets   = None
    inet_save    = None
    was_carp     = False
    cluster      = Cluster.objects.get()
    INTF_CHOICES = cluster.get_interface_choices()

    # Editing existing inet: retrieving it
    if object_id:
        inet      = Listener.objects.with_id(ObjectId(object_id))
        inet_save = dict(inet.to_mongo())
        intf      = Interface.objects.get(inet_addresses__in=[inet])

        was_carp = inet.is_carp
        if inet.is_carp:
            carp_inets = inet.get_related_carp_inets_detailed()

        form = InetAddressForm(INTF_CHOICES, intf.id, request.POST or None, instance=inet)
    else:
        form = InetAddressForm(INTF_CHOICES, None, request.POST or None, instance=inet)

    # Saving information into database
    if request.method == 'POST' and form.is_valid():
        inet_obj = form.save(commit=False)
        inet_obj.version=str(ipaddress.ip_address(inet_obj.ip).version)

        try:
            """ Check if configuration has changed
                and save previous config so that we can shutdown the old interface via ifconfig
            """
            if inet_save == dict(inet_obj.to_mongo()):
                logger.info("Same configuration for inet {}: passing.....".format(inet_obj))
                return HttpResponseRedirect("/network/listeners/")
            else:
                inet_obj.previous_inet=inet_save

        except AttributeError:
            ## Object is created
            pass

        if not object_id:
            ip_addr = form.cleaned_data.get('ip')
            for listener in Listener.objects():
                if listener.ip == ip_addr:
                    form.errors['ip'] = _("This IP address is already used")
                    return render_to_response('network_edit.html',
                              {'form': form,
                               'nodes': cluster.members,
                               'carp_inets': carp_inets},
                              context_instance=RequestContext(request))

        device = form.cleaned_data['device']
        reg = re.compile("^[A-Fa-f0-9]{24}$")

        # NO-CARP device
        if reg.match(device) and not inet_obj.is_carp:
            ### Important, save the listener before add it to the Interface
            inet_obj.save(bootstrap=True)

            selected_intf = Interface.objects.with_id(ObjectId(device))
            # intf not defined, it's a new listener
            if not intf:
                selected_intf.inet_addresses.append(inet_obj)

            # intf selected differs from intf saved in database
            elif intf != selected_intf:
                logger.info("Switching listener {} from {} to {}".format(str(inet_obj), str(intf), str(selected_intf)))
                intf.inet_addresses.remove(inet_obj)
                """ bootstrap is true because rc_conf refresh is done by hand """
                intf.save(bootstrap=True)
                # Adding listener to its new interface
                selected_intf.inet_addresses.append(inet_obj)


            """ bootstrap is true because rc_conf refresh is done by deploy_inet() """
            selected_intf.save(bootstrap=True)

            if inet_obj.deploy_inet():
                logger.info("Listener {} successfuly created on {}".format(str(inet_obj), str(selected_intf)))
            else:
                logger.error("Unable to create listener {} on {}".format(str(inet_obj), str(selected_intf)))

        # Handle CARP listener
        else:
            # Retrieving CARP interface information from POST data
            carp_intfs = dict()
            for field_name, priority_value in request.POST.items():
                reg = re.compile("^carp_priority_([A-Fa-f0-9]{24})$")
                res = reg.match(field_name)
                if res is not None:
                    carp_intf_id = res.groups()[0]
                    carp_intf = Interface.objects.with_id(ObjectId(carp_intf_id))
                    try:
                        priority_value = int(priority_value)
                    except ValueError:
                        priority_value = 1
                        pass
                    carp_intfs[carp_intf] = priority_value


            # new carp listener
            if not object_id or not was_carp:
                create_carp_inets(carp_intfs, inet_obj, was_carp)
            else:
                update_carp_inets(carp_intfs, inet_obj)

            logger.info("Deploying CARP listener")
            inet_obj.deploy_carp()
            logger.info("CARP deployed")

        return HttpResponseRedirect("/network/listeners/")

    return render_to_response('network_edit.html', {
                            'form'      : form,
                            'object_id' : object_id,
                            'nodes'     : cluster.members,
                            'carp_inets': carp_inets},
                            context_instance=RequestContext(request))


def create_carp_inets(carp_intfs, inet_obj, was_carp):
    """ Create carp listener for interfaces provided in carp_intfs

    :param carp_intfs: Dict with Interface object as key and carp priority as
    value
    :param inet_obj: Listener object representing params of listener (ip,
     netmask, name...)
    :param: was_carp: Boolean which indicate if listener was CARP
    """
    logger.info("Creating CARP listener")
    inet_obj_values = inet_obj.to_mongo()
    carp_passwd = get_random_string(20)
    for carp_intf, priority_value in carp_intfs.items():
        # Creating CARP inet on this interface
        carp_inet = Listener(**inet_obj_values)
        carp_inet.carp_priority = priority_value
        carp_inet.carp_passwd = carp_passwd
        carp_inet.related_node=carp_intf.get_related_node()
        carp_inet.save(bootstrap=True)
        carp_intf.inet_addresses.append(carp_inet)
        carp_intf.save(bootstrap=True)

    #FIXME-NETWORK

    logger.info("CARP listener successfully created")


def update_carp_inets(carp_intfs, inet_obj):
    """ Update Carp listener for interfaces provided in carp_intfs

    :param carp_intfs: Dict with Interface object as key and carp priority as
    value
    :param inet_obj: Listener object representing params of listener (ip,
     netmask, name...)
    """
    logger.info("Editing CARP listener on {}".format(str(inet_obj)))
    inet_obj_values = inet_obj.to_mongo()
    # Retrieving data about CARP inets
    db_carp_intfs = inet_obj.get_related_carp_intfs()
    db_carp_inets = inet_obj.get_related_carp_inets_detailed()

    """Browsing list of new CARP interface and checking if they correspond to
    interfaces saved into database
    """
    for carp_intf, priority_value in carp_intfs.items():
        logger.debug("Looking if {} is a new CARP interface".format(str(carp_intf)))
        if carp_intf not in db_carp_intfs:
            logger.info("Creating new CARP listener on {}".format(str(carp_intf)))
            carp_inet = Listener(**inet_obj_values)
            carp_inet.carp_priority = priority_value
            carp_inet.related_node = carp_intf.get_related_node()
            carp_inet.save(bootstrap=True)
            carp_intf.inet_addresses.append(carp_inet)

            #Save config but not send listener_modified signal, as it is managed by Listener.deploy() later
            carp_intf.save(bootstrap=True)
        # Existing Intf, remove it from list (used to detect removed Intf
        else:
            db_carp_intfs.remove(carp_intf)

    """Looking if configuration in database corresponds to submitted
    configuration. Configuration items are ip, prefixlen, alias, vhid_priority.
    inet : data from db | inet_obj : data from form
    """
    for listener in db_carp_inets:
        inet = listener['inet']
        intf = listener['intf']
        attr_lst = ('ip','prefixlen','alias')
        for attr in attr_lst:
            if getattr(inet, attr) != getattr(inet_obj, attr):
                setattr(inet, attr, getattr(inet_obj, attr))
        if carp_intfs.get(intf) is not None and inet.carp_priority != carp_intfs.get(intf):
            inet.carp_priority = carp_intfs[intf]
        inet.save(bootstrap=True)


    """Make deleted listener outdated, they are going to be shut down and
    deleted later
    """
    for intf in db_carp_intfs:
        inet = intf.find_carp_inet(inet_obj)
        logger.info("Deleting listener {}".format(str(inet)))
        inet.delete()

    logger.info("CARP listeners successfully updated")


