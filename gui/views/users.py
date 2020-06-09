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
__doc__ = 'Django views dedicated to Vulture GUI admin page'

from bson.objectid import ObjectId
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

from gui.decorators import group_required
from gui.forms.user_document import VultureUserForm, VultureNewUserForm
from gui.models.user_document import VultureUser


@group_required('administrator')
def user_list(request):
    all_user = VultureUser.objects.all()
    return render_to_response('user_list.html',
                              {'users': all_user},
                              context_instance=RequestContext(request))

@group_required('administrator')
def user_edit(request, object_id=None):
    user = VultureUser.objects.with_id(ObjectId(object_id)) if object_id else None
    if user:
        form = VultureUserForm(request.POST or None, instance=user)
    else:
        form = VultureNewUserForm(request.POST or None)
    if request.POST:
        if form.is_valid():
            form.save()
            return HttpResponseRedirect("/system/users/")
    return render_to_response('user_edit.html',
                              {'form': form, 'object_id': object_id},
                              context_instance=RequestContext(request))
