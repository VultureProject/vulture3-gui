#!/usr/bin/python
#-*- coding: utf-8 -*-
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
__doc__ = 'Django views dedicated to Vulture GUI Cluster page'

from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.generic import ListView

from gui.decorators import group_required
from gui.models import repository_settings


class RepositoryListView(ListView):
    template_name = 'repository_list.html'
    context_object_name = 'repositories'
    def __init__(self):
        self.queryset = repository_settings.BaseAbstractRepository.get_repositories()

    @method_decorator(group_required('administrator', 'system_manager'))
    def dispatch(self, *args, **kwargs):
        return super(RepositoryListView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(RepositoryListView, self).get_context_data(**kwargs)
        context['repository_name'] = _('Repositories')
        context['global'] = True
        return context