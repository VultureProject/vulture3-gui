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
__doc__ = 'Django forms dedicated to mod_rewrite settings'

from django.forms import TextInput, MultipleChoiceField, CheckboxInput, SelectMultiple, BooleanField
from mongodbforms import DocumentForm

from gui.forms.forms_utils import bootstrap_tooltips
from gui.models.application_settings import Application
from gui.models.rewrite_settings import Rewrite


class RewriteForm(DocumentForm):
    """ mod_rewrite form representation
    """

    application = MultipleChoiceField(required=False, widget=SelectMultiple(attrs={'class': 'form-control'}))
    is_template = BooleanField(required=False, initial=False, widget=CheckboxInput(attrs={'class': 'js-switch'}))

    def __init__(self, *args, **kwargs):
        super(RewriteForm, self).__init__(*args, **kwargs)
        self = bootstrap_tooltips(self)

        # Extract le choices for the certificate selection
        app_list = Application.objects.all().only('id', 'name')
        app_choices = list()
        for app in app_list:
            app_choices.append((app.id, app.name))

        # Set the choices extracted and set the initial value
        self.fields['application'].choices = app_choices
        rewrite = kwargs.pop('instance')
        id_list = list()
        for app in rewrite.application:
            id_list.append(app.id)
        if rewrite:
            self.initial['application'] = id_list

    def clean(self):
        super(RewriteForm, self).clean()

        # Uses the Applications id to get the object and store it in ReferenceField
        application = self.cleaned_data.get('application')
        app_list = list()
        for app_id in application:
            app = Application.objects.with_id(app_id)
            app_list.append(app)
        self.cleaned_data['application'] = app_list

        return self.cleaned_data

    class Meta:
        document = Rewrite
        widgets = {
            'name': TextInput(attrs={'class': 'form-control'}),
        }



