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
__author__ = "Kevin Guillemot"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = 'Django forms dedicated to monitoring agents'


# Django system imports
from django.conf              import settings
from django.utils.translation import ugettext_lazy as _
from django.forms import (CheckboxInput, BooleanField, MultipleChoiceField, SelectMultiple, NumberInput, ChoiceField,
                          TextInput, Select)
from mongodbforms import DocumentForm

# Django project imports
from gui.forms.forms_utils import bootstrap_tooltips
from gui.models.agents_settings import ZabbixAgent, ENCRYPTION_TYPE
from gui.models.ssl_certificate import SSLCertificate
from gui.models.network_settings import Listener

# Required exceptions imports
from django.core.exceptions import ValidationError

# Extern modules imports
from re import search as re_search

# Logger configuration imports
import logging
logger = logging.getLogger('debug')



class ZabbixAgentForm(DocumentForm):
    """ ZabbixAgent form representation
    """
    # Override require=False in form to not cause not valid() form
    enabled = BooleanField(required=False, label=_('Enable service'),
                           widget=CheckboxInput(attrs={'class': 'js-switch'}))
    allow_root = BooleanField(required=False, label=_('Allow root'),
                              widget=CheckboxInput(attrs={'class': 'js-switch'}))
    enable_remote_commands = BooleanField(required=False, label=_('Enable remote commands'),
                                          widget=CheckboxInput(attrs={'class': 'js-switch'}))
    log_remote_commands = BooleanField(required=False, label=_('Log remote commands'),
                                       widget=CheckboxInput(attrs={'class': 'js-switch'}))
    # Do not redefine other fields because the verbose_name attribute will be override

    def __init__(self, *args, **kwargs):
        # Get extra arg 'node' to avoid "unexpected keyword argument"
        node = kwargs.pop('node', None)
        super(ZabbixAgentForm, self).__init__(*args, **kwargs)
        bootstrap_tooltips(self)

        """ Build certificate choices - field """
        # Retrieve SSLCertificates to build choices
        certificate_list = SSLCertificate.objects.filter(is_ca=False, is_trusted_ca=False, status__ne='R').only('id',
                                                                                                                'cn')
        # Set the choices retrieven
        self.fields['tls_cert'].choices = [(cert.id, cert.cn) for cert in certificate_list]

        """ Build listener choices - field """
        # Extract ListenAddress for the listener(s) selection
        listener_filter = {'is_carp': False}
        if node:
            listener_filter['related_node'] = node
        listener_list = Listener.objects.filter(**listener_filter).only('id', 'ip')
        # Build the field
        self.fields['listeners'].choices = [(listener.id, listener.ip) for listener in listener_list]

    class Meta:
        document = ZabbixAgent
        widgets = {
            'servers': TextInput(attrs={'class': 'form-control'}),
            'listeners': SelectMultiple(attrs={'class': 'form-control select2'}),
            'key_length': NumberInput(attrs={'class': 'form-control'}),
            'active_servers': TextInput(attrs={'class': 'form-control'}),
            'hostname': TextInput(attrs={'class': 'form-control'}),
            'tls_accept': Select(attrs={'class': 'form-control'}),
            'tls_connect': Select(attrs={'class': 'form-control'}),
            'tls_cert': Select(attrs={'class': 'form-control'}),
            'tls_server_subject': TextInput(attrs={'class': 'form-control'}),
            'tls_server_issuer': TextInput(attrs={'class': 'form-control'}),
            'psk_identity': TextInput(attrs={'class': 'form-control'}),
            'psk_key': TextInput(attrs={'class': 'form-control'})
        }

    def clean_psk_key(self):
        field_value = self.cleaned_data.get('psk_key', "")
        if field_value and not re_search("^[0-9a-fA-F]{32,}$", field_value):
            raise ValidationError("PSK key is too short. Minimum is 32 hex-digits.")
        return field_value

    def clean(self):
        cleaned_data = super(ZabbixAgentForm, self).clean()
        tls_cert = cleaned_data.get('tls_cert')
        psk_key = cleaned_data.get('psk_key')

        for field in ['tls_accept', 'tls_connect']:
            field_value = cleaned_data.get(field)
            if field_value == 'cert':
                if not tls_cert:
                    self.add_error(field, 'You must configure a certificate to use with "{}".'.format(field))
            elif field_value == 'psk':
                if not psk_key:
                    self.add_error(field, 'You must configure a valid PSK key to use with "{}".'.format(field))
                elif not cleaned_data.get('psk_identity'):
                    self.add_error(field, 'You must configure a PSK identity to use with "{}".'.format(field))

        for field in ['tls_server_issuer', 'tls_server_subject']:
            if cleaned_data.get(field) and not tls_cert:
                self.add_error(field, '"Server certificate subject" needs a certificate.')
