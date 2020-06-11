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
__doc__ = 'Django views dedicated to log files (mod_log_config)'

from bson.objectid import ObjectId
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

from gui.decorators import group_required
from gui.forms.modlog_settings import ModLogForm
from gui.models.modlog_settings import ModLog
from gui.signals.gui_signals import config_modified


@group_required('administrator', 'application_manager')
def log_list(request):
    """ Page dedicated to show log format list
    """
    try:
        logs = ModLog.objects()
    except ModLog.DoesNotExist:
        logs = None

    return render_to_response('log.html', {'logs': logs}, context_instance=RequestContext(request))


@group_required('administrator', 'application_manager')
def edit(request, object_id=None):

    """ View dedicated to mod_log management

    :param object_id: MongoDB object_id of log format
    :param request: Django request object
    """
    modlog = None
    repository_syslog = None
    # Retrieving access configuration
    if object_id:
        modlog = ModLog.objects.with_id(ObjectId(object_id))

    form = ModLogForm(request.POST or None, instance=modlog)
    # Saving information into database and redirect to application list
    if request.method == 'POST' and form.is_valid():
        data_repository = form.cleaned_data.get('data_repository')
        syslog_repository = form.cleaned_data.get('syslog_repository')

        modlog = form.save(commit=False)
        modlog.data_repository = data_repository
        modlog.syslog_repository = syslog_repository
        modlog.save()
        config_modified.send(sender=ModLog, id=modlog.id)

        return HttpResponseRedirect('/system/log/')


    return render_to_response('log_edit.html',
                              {'form': form, 'object_id': object_id, 'modlog': modlog},
                              context_instance=RequestContext(request))