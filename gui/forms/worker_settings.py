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
__doc__ = 'Django forms dedicated to worker settings'

from django.forms import TextInput, CheckboxInput, BooleanField
from mongodbforms import DocumentForm

from gui.forms.forms_utils import bootstrap_tooltips
from gui.models.worker_settings import Worker


class WorkerForm(DocumentForm):
    """ Worker form representation
    """
    h2direct           = BooleanField(required=False, widget=CheckboxInput(attrs={"class": "js-switch"}))
    h2moderntlsonly    = BooleanField(required=False, widget=CheckboxInput(attrs={"class": "js-switch"}))
    h2push             = BooleanField(required=False, widget=CheckboxInput(attrs={"class": "js-switch"}))
    h2direct           = BooleanField(required=False, widget=CheckboxInput(attrs={"class": "js-switch"}))
    h2serializeheaders = BooleanField(required=False, widget=CheckboxInput(attrs={"class": "js-switch"}))
    h2upgrade          = BooleanField(required=False, widget=CheckboxInput(attrs={"class": "js-switch"}))

    def __init__(self, *args, **kwargs):
        super(WorkerForm, self).__init__(*args, **kwargs)

        self = bootstrap_tooltips(self)

    class Meta:
        document = Worker
        widgets = {
            'name': TextInput(attrs={'class': 'form-control'}),
            'gracefulshutdowntimeout': TextInput(attrs={'class': 'form-control'}),
            'maxconnectionsperchild': TextInput(attrs={'class': 'form-control'}),
            'minsparethreads': TextInput(attrs={'class': 'form-control'}),
            'maxsparethreads': TextInput(attrs={'class': 'form-control'}),
            'serverlimit': TextInput(attrs={'class': 'form-control'}),
            'threadsperchild': TextInput(attrs={'class': 'form-control'}),
            'rate_limit': TextInput(attrs={'class': 'form-control'}),
            'req_timeout_header': TextInput(attrs={'class': 'form-control'}),
            'req_timeout_body': TextInput(attrs={'class': 'form-control'}),
            'req_timeout_header_rate': TextInput(attrs={'class': 'form-control'}),
            'req_timeout_body_rate': TextInput(attrs={'class': 'form-control'}),
            'timeout': TextInput(attrs={'class': 'form-control'}),
            'maxkeepaliverequests': TextInput(attrs={'class': 'form-control'}),
            'keepalivetimeout': TextInput(attrs={'class': 'form-control'}),
            'h2maxsessionstreams': TextInput(attrs={'class': 'form-control'}),
            'h2maxworkeridleseconds': TextInput(attrs={'class': 'form-control'}),
            'h2minworkers': TextInput(attrs={'class': 'form-control'}),
            'h2maxworkers': TextInput(attrs={'class': 'form-control'}),
            'h2streammaxmemsize': TextInput(attrs={'class': 'form-control'}),
            'h2tlscooldownsecs': TextInput(attrs={'class': 'form-control'}),
            'h2tlswarmupsize': TextInput(attrs={'class': 'form-control'}),
            'h2windowsize': TextInput(attrs={'class': 'form-control'}),
        }
