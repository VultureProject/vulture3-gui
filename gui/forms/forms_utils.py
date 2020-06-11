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
__doc__ = ''

from django.forms.utils import ErrorList

def bootstrap_tooltips(self, *args, **kwargs):
    """ Add bootstrap properties used to display help tooltips based on
    help_text field

    :param exclude: list of field which doesnt need tooltip
    :param kwargs:
    :return:
    """
    excluded_fields = kwargs.get('exclude', [])
    for field in self.fields:
        help_text = self.fields[field].help_text
        self.fields[field].help_text = None
        if help_text != '' and field not in excluded_fields:
            try:
                class_attr = self.fields[field].widget.attrs["class"]
            except:
                class_attr = 'form-control'

            self.fields[field].widget.attrs.update({
                'class': class_attr,
                'data-toggle': 'tooltip',
                'title': help_text,
                'data-placement': 'right'})
    return self


class DivErrorList(ErrorList):
    def __str__(self):
        return self.as_ul()

    def as_ul(self):
        if not self:
            return ''
        return '<div class="custom_error">%s</div>' % super(DivErrorList, self).as_ul()

