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
__doc__ = 'Django views dedicated to mod_ssl profiles'

from bson.objectid import ObjectId
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

from gui.decorators import group_required
from gui.forms.modssl_settings import ModSSLForm
from gui.models.modssl_settings import ModSSL
from gui.models.application_settings import ListenAddress
from gui.signals.gui_signals import config_modified


@group_required('administrator', 'application_manager')
def ssl_list(request):
    """ Page dedicated to show ssl profiles list
    """
    try:
        ssl_list = ModSSL.objects()
    except DoesNotExist:
        ssl_list = None

    used_list=list()
    for ssl in ssl_list:
        ssl.listeners=list()
        for listener in ListenAddress.objects():
            if listener.ssl_profile == ssl:
                ssl.listeners.append(listener)
        used_list.append(ssl)
    ssl_list=used_list

    return render_to_response('ssl.html', {'ssl_list': ssl_list}, context_instance=RequestContext(request))


@group_required('administrator', 'application_manager')
def clone(request, object_id=None):
    """ View dedicated to mod_ssl cloning
    :param object_id: MongoDB object_id of ssl profile
    :param request: Django request object
    """
    modssl = ModSSL.objects.with_id(ObjectId(object_id))
    modssl.pk = None
    modssl.name = 'Copy of ' + str(modssl.name)
    modssl.save()
    return HttpResponseRedirect('/system/ssl/')


@group_required('administrator', 'application_manager')
def edit(request, object_id=None):

    """ View dedicated to mod_ssl management

    :param object_id: MongoDB object_id of ssl profile
    :param request: Django request object
    """

    modssl = None
    # Retrieving access configuration
    if object_id:
        modssl = ModSSL.objects.with_id(ObjectId(object_id))

    form = ModSSLForm(request.POST or None, instance=modssl)

    # Saving information into database and redirect to application list
    if request.method == 'POST' and form.is_valid():
        modssl = form.save(commit=False)
        modssl.save()
        config_modified.send(sender=ModSSL, id=modssl.id)
        return HttpResponseRedirect('/system/ssl/')


    return render_to_response('ssl_edit.html',
                              {'form':form, 'object_id': object_id, 'modssl':modssl},
                              context_instance=RequestContext(request))


