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
__doc__ = 'Django views dedicated to firewall access control'

import re

from bson.objectid import ObjectId
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render_to_response
from django.template import RequestContext

from gui.decorators import group_required
from gui.forms.modaccess_settings import ModAccessForm
from gui.models.modaccess_settings import ModAccess, AccessRule
from gui.signals.gui_signals import config_modified
from gui.models.repository_settings import LDAPRepository


@group_required('administrator', 'security_manager')
def access_list(request):
    """ Page dedicated to show access list
    """
    try:
        accesses = ModAccess.objects()
    except ModAccess.DoesNotExist:
        accesses = None

    lst=list()
    for access in accesses:
        access.showconf=access.getConf(1)
        if access.user_list:
            access.user_list=access.user_list.replace('|','<br/>')
        if access.group_list:
            access.group_list=access.group_list.replace('|','<br/>')
        lst.append (access)

    accesses=lst

    return render_to_response('access.html', {'accesses': accesses}, context_instance=RequestContext(request))


@group_required('administrator', 'security_manager')
def clone(request, object_id=None):

    """ View dedicated to access cloning
    :param object_id: MongoDB object_id of configuration
    :param request: Django request object
    """
    #Retrieve access configuration
    access = ModAccess.objects.with_id(ObjectId(object_id))
    access.name = 'Copy of ' + str (access.name)
    access.pk = None
    access.save()
    return HttpResponseRedirect('/firewall/access/')



@group_required('administrator', 'security_manager')
def fetch_ldap_user(request, object_id=None):

    if object_id:
        backend=LDAPRepository.objects.with_id(object_id).get_backend()
        ret = backend.enumerate_users()
        user_dn=ret.pop(0)
        ret.pop(0)

        retg = backend.enumerate_groups()
        group_dn=retg.pop(0)
        base_dn=retg.pop(0)
        return JsonResponse({'status':True, 'user_dn':user_dn, 'group_dn':group_dn,'base_dn':base_dn,'list_user':ret,'list_group':retg})
    else:
        return JsonResponse({'status':False})


@group_required('administrator', 'security_manager')
def edit(request, object_id=None):

    """ View dedicated to access management

    :param object_id: MongoDB object_id of access list
    :param request: Django request object
    """

    modaccess = None
    #Retrieving access configuration
    if object_id:
        modaccess = ModAccess.objects.with_id(ObjectId(object_id))
        access_list = modaccess.access_list
    else:
        access_list = ""

    form = ModAccessForm(request.POST or None, instance=modaccess)

    #Check if request are valid - and populate arrays with form values
    if request.method == 'POST':
        dataPosted      = request.POST
        dataPostedRaw   = str(request.body).split("&")
        access_list     = ""
        for data in dataPostedRaw:
            #Access rule management
            m = re.match('element_(\d+)',data)
            if m != None:
                id_ = m.group(1)

                #Force harmless default values to prevent any injection or jQuery problem
                element = 'all-denied'
                isnot = ''
                expected = ''

                try:
                    element       = dataPosted['element_' + id_]
                except:
                    continue

                try:
                    isnot         = dataPosted['element_not_' + id_]
                    expected      = dataPosted['expected_' + id_]
                except:
                    pass

                access_list = access_list + str(element) + '|||' + str (isnot) + '|||' + str (expected) + '\n'


    #We need to transform the access_list text to a list of access rules
    access_rules=list()
    for r in access_list.split('\n'):
        elt = r.split('|||')
        try:
            rule=AccessRule()
            rule.element = elt[0]
            rule.isnot = elt[1]
            rule.expected = elt[2]
            access_rules.append(rule)
        except:
            pass

    # Saving information into database and redirect to application list
    if request.method == 'POST' and form.is_valid():
        modaccess = form.save(commit=False)
        modaccess.access_list = access_list
        modaccess.save()
        config_modified.send(sender=ModAccess, id=modaccess.id)
        return HttpResponseRedirect('/firewall/access/')


    return render_to_response('access_edit.html',
                              {'form':form, 'object_id': object_id, 'modaccess':modaccess,'access_rules':access_rules},
                              context_instance=RequestContext(request))


