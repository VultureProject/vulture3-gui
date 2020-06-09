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
__doc__ = 'Django forms dedicated to mod_log and log management settings'

from django.forms import TextInput, ChoiceField, Select, CheckboxInput, BooleanField
from mongodbforms import DocumentForm

from gui.forms.forms_utils import bootstrap_tooltips
from gui.models.modlog_settings import ModLog
from gui.models.repository_settings import BaseAbstractRepository


class ModLogForm(DocumentForm):
    """ Mod Log form representation
    """
    buffered = BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super(ModLogForm, self).__init__(*args, **kwargs)
        self = bootstrap_tooltips(self, exclude='repository_choices')

        repo_lst = BaseAbstractRepository.get_data_repositories()
        data_repo_lst = list()
        for rep in repo_lst:
            data_repo_lst.append((rep.id, rep.repo_name,))

        self.fields['repository_choices'] = ChoiceField(choices=data_repo_lst, required=False)

        repo_lst = BaseAbstractRepository.get_syslog_repositories()
        syslog_repo_lst = list()
        syslog_repo_lst.append(("",""))
        for rep in repo_lst:
            syslog_repo_lst.append((rep.id, rep.repo_name,))

        self.fields['repository_syslog'] = ChoiceField(choices=syslog_repo_lst, required=False)


    def clean_repository_choices(self):
        data = self.cleaned_data.get('repository_choices')
        self.cleaned_data['data_repository'] = data
        return data

    def clean_repository_syslog(self):
        data = self.cleaned_data.get('repository_syslog')
        if data:
            self.cleaned_data['syslog_repository'] = data
        return data

    class Meta:
        document = ModLog
        widgets = {
            'name'    : TextInput(attrs={'class':'form-control'}),
            'format'  : TextInput(attrs={'class': 'form-control'}),
        }






