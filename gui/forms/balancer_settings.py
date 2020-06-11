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
__doc__ = 'Django forms dedicated to Proxy Balancer settings'

from django.forms import TextInput, Select, ChoiceField
from mongodbforms import DocumentForm

from gui.forms.forms_utils import bootstrap_tooltips
from gui.models.application_settings import ProxyBalancer


class ProxyBalancerForm(DocumentForm):
    """ Proxy Balancer form representation
    """


    def __init__(self, *args, **kwargs):
        super(ProxyBalancerForm, self).__init__(*args, **kwargs)
        
        HC_METHODS = (
            ('None', 'No dynamic health checking done'),
            ('TCP', 'Check that a socket to the backend can be created: e.g. "are you up"'),
            ('OPTIONS', 'Send an HTTP OPTIONS request to the backend'),
            ('HEAD', 'Send an HTTP HEAD request to the backend'),
            ('GET', 'Send an HTTP GET request to the backend')
        )

        HC_EXPR = (
            ('{%{REQUEST_STATUS} =~ /^[234]/}', 'HTTP status code is 2XX, 3XX or 4XX'),
            ('{%{REQUEST_STATUS} =~ /^[5]/}', 'HTTP status code is 5XX'),
            ('hc(\'body\') !~', 'BODY does not contains'),
            ('hc(\'body\') =~', 'BODY contains'),
        )

        self.fields['hcmethod'] = ChoiceField(choices=HC_METHODS, required=False, widget=Select(attrs={'class': 'form-control'}))
        self.fields['hcexpr'] = ChoiceField(choices=HC_EXPR, required=False, widget=Select(attrs={'class': 'form-control'}))

        self = bootstrap_tooltips(self)

    class Meta:
        document = ProxyBalancer
        widgets = {
            'name'            : TextInput(attrs={'class':'form-control'}),
            'stickysession'   : TextInput(attrs={'class':'form-control'}),
            'stickysessionsep': TextInput(attrs={'class':'form-control'}),
            'config'          : TextInput(attrs={'class':'form-control'}),
            'hcpasses'        : TextInput(attrs={'class':'form-control'}),
            'hcfails'         : TextInput(attrs={'class':'form-control'}),
            'hcinterval'      : TextInput(attrs={'class':'form-control'}),
            'hcuri'           : TextInput(attrs={'class':'form-control'}),
            # 'hcexpr'          : Select(attrs={'class': 'form-control'}),
            'hcexpr_data'     : TextInput(attrs={'class':'form-control'})
        }
