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
__doc__ = 'Django forms dedicated to mod_ssl'

from django import forms
from django.forms import TextInput, CheckboxInput, BooleanField
from django.utils.translation import ugettext_lazy as _
from mongodbforms import DocumentForm

from gui.forms.forms_utils import bootstrap_tooltips
from gui.models.modsec_settings import ModSec, ModSecRulesSet


class ModSecForm(DocumentForm):
    """ ModSecurity policy form representation
    """
    def __init__(self, *args, **kwargs):
        super(ModSecForm, self).__init__(*args, **kwargs)
        self = bootstrap_tooltips(self)

    class Meta:
        document = ModSec
        widgets = {
            'defender_enable': CheckboxInput(attrs={'class': 'js-switch'}),
            'secbodyinspection': CheckboxInput(attrs={'class': 'js-switch'}),
            'seccontentinjection': CheckboxInput(attrs={'class': 'js-switch'}),
            'secdisablebackendcompression': CheckboxInput(attrs={'class': 'js-switch'}),
            'crs_validate_utf8_encoding': CheckboxInput(attrs={'class': 'js-switch'}),
            'xml_enable': CheckboxInput(attrs={'class': 'js-switch'}),
            'reqbody_error_enable': CheckboxInput(attrs={'class': 'js-switch'}),
            'defender_libinjection_sql_enable': CheckboxInput(attrs={'class': 'js-switch'}),
            'defender_libinjection_xss_enable': CheckboxInput(attrs={'class': 'js-switch'}),
            'block_desktops_ua': CheckboxInput(attrs={'class': 'js-switch'}),
            'block_crawlers_ua': CheckboxInput(attrs={'class': 'js-switch'}),
            'block_suspicious_ua': CheckboxInput(attrs={'class': 'js-switch'}),
            'dos_enable_rule': CheckboxInput(attrs={'class': 'js-switch'}),

            'name': TextInput(attrs={'class':'form-control'}),
            'engine_version': TextInput(attrs={'class':'form-control', 'readonly': 'readonly'}),
            'secauditlogrelevantstatus': TextInput(attrs={'class':'form-control'}),
            'secargumentseparator': TextInput(attrs={'class':'form-control'}),
            'seccollectiontimeout': TextInput(attrs={'class':'form-control'}),
            'seccookiev0separator': TextInput(attrs={'class':'form-control'}),
            'critical_anomaly_score': TextInput(attrs={'class':'form-control'}),
            'security_level' : TextInput(attrs={'class':'form-control'}),
            'error_anomaly_score': TextInput(attrs={'class':'form-control'}),
            'warning_anomaly_score': TextInput(attrs={'class':'form-control'}),
            'notice_anomaly_score': TextInput(attrs={'class':'form-control'}),

            # 'vlt_injection': TextInput(attrs={'class':'form-control'}),
            # 'vlt_xss': TextInput(attrs={'class':'form-control'}),
            # 'vlt_rfi': TextInput(attrs={'class':'form-control'}),
            # 'vlt_lfi': TextInput(attrs={'class':'form-control'}),
            # 'vlt_rce': TextInput(attrs={'class':'form-control'}),
            # 'vlt_leak': TextInput(attrs={'class':'form-control'}),
            # 'vlt_protocol': TextInput(attrs={'class':'form-control'}),
            # 'vlt_session': TextInput(attrs={'class':'form-control'}),
            # 'vlt_csrf': TextInput(attrs={'class':'form-control'}),
            # 'vlt_evade': TextInput(attrs={'class':'form-control'}),
            # 'vlt_suspicious': TextInput(attrs={'class':'form-control'}),

            'inbound_anomaly_score_threshold': TextInput(attrs={'class':'form-control'}),
            'outbound_anomaly_score_threshold': TextInput(attrs={'class':'form-control'}),
            'max_num_args': TextInput(attrs={'class':'form-control'}),
            'arg_name_length': TextInput(attrs={'class':'form-control'}),
            'arg_length': TextInput(attrs={'class':'form-control'}),
            'total_arg_length': TextInput(attrs={'class':'form-control'}),
            'max_file_size': TextInput(attrs={'class':'form-control'}),
            'combined_file_sizes': TextInput(attrs={'class':'form-control'}),
            'allowed_request_content_type': TextInput(attrs={'class':'form-control'}),
            'allowed_http_versions': TextInput(attrs={'class':'form-control'}),
            'restricted_extensions': TextInput(attrs={'class':'form-control'}),
            'restricted_headers': TextInput(attrs={'class':'form-control'}),
            'dos_burst_time_slice': TextInput(attrs={'class':'form-control'}),
            'dos_counter_threshold': TextInput(attrs={'class':'form-control'}),
            'dos_block_timeout': TextInput(attrs={'class':'form-control'}),
            'defender_request_body_limit': TextInput(attrs={'class': 'form-control'})
        }

    def clean(self):
        super(ModSecForm, self).clean()
        error_msg = list()


        return self.cleaned_data

class ModSecScanForm(forms.Form):
    """ ModSecurity XML Scan Report upload form representation
    """

    SCAN_TYPE = (
        ('acunetix_9',  'XML - Acunetix v9'),
        ('qualys',      'XML - Qualysguard WAS'),
        ('zap',         'XML - OWASP Zed Attack Proxy'),
    )

    def __init__(self, *args, **kwargs):
        super(ModSecScanForm, self).__init__(*args, **kwargs)
        self = bootstrap_tooltips(self)


    type = forms.ChoiceField(required=True, choices=SCAN_TYPE, help_text=_('Please select the report file format'))
    file = forms.FileField(required=True)





class ModSecRulesSetForm(DocumentForm):
    """ ModSecurity RulesSet form representation
    """


    def __init__(self, *args, **kwargs):
        super(ModSecRulesSetForm, self).__init__(*args, **kwargs)
        self = bootstrap_tooltips(self)


    class Meta:
        document = ModSecRulesSet
        widgets = {
            'name': TextInput(attrs={'class':'form-control'}),
        }




