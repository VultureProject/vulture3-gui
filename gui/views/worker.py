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
__doc__ = 'Django views dedicated to worker configuration'

from bson.objectid import ObjectId
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

from gui.decorators import group_required
from gui.forms.worker_settings import WorkerForm
from gui.models.application_settings import Application
from gui.models.worker_settings import Worker
from gui.signals.gui_signals import config_modified


@group_required('administrator', 'application_manager')
def worker_list(request):
    """ Page dedicated to show worker list
    """
    try:
        workers = Worker.objects()
    except Worker.DoesNotExist:
        workers = None

    worker_list = list()
    for worker in workers:
        worker.applist = list()
        for app in Application.objects():
            if app.worker == worker:
                worker.applist.append(app)
        worker_list.append(worker)
    workers=worker_list

    return render_to_response('worker.html', {'workers': workers}, context_instance=RequestContext(request))

@group_required('administrator', 'application_manager')
def clone(request, object_id=None):
    """ View dedicated to worker cloning
    :param object_id: MongoDB object_id of worker
    :param request: Django request object
    """
    # Retrieving worker configuration
    worker = Worker.objects.with_id(ObjectId(object_id))
    worker.pk = None
    worker.name = 'Copy of ' + str(worker.name)
    worker.save()
    return HttpResponseRedirect('/system/worker/')


@group_required('administrator', 'application_manager')
def edit(request, object_id=None):

    """ View dedicated to worker management

    :param object_id: MongoDB object_id of worker
    :param request: Django request object
    """
    # Retrieving worker configuration
    worker = Worker.objects.with_id(ObjectId(object_id))

    # Worker doesn't exist ==> create it
    if not worker:
        worker = Worker(name="My Vulture Worker")

    form = WorkerForm(request.POST or None, instance=worker)

    # Saving information into database and redirect to worker list
    if request.method == 'POST' and form.is_valid():

        worker = form.save(commit=False)
        worker.save()
        config_modified.send(sender=Worker, id=worker.id)


        return HttpResponseRedirect('/system/worker/')


    return render_to_response('worker_edit.html',
                              {'form':form, 'object_id': object_id,
                               'workername':worker.name},
                              context_instance=RequestContext(request))


