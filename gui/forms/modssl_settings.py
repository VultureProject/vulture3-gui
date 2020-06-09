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

from django.forms import BooleanField, ChoiceField, Select, TextInput
from mongodbforms import DocumentForm

from gui.forms.forms_utils import bootstrap_tooltips
from gui.models.modssl_settings import ModSSL
from gui.models.ssl_certificate import SSLCertificate
from vulture_toolkit.system.ssl_utils import get_openssl_engines


class ModSSLForm(DocumentForm):
    """ ModSSL form representation
    """

    VERIFY_LIST = (
        ('none', 'Not required'),
        ('optional', 'Optional, but need to be valid'),
        ('require', 'Required'),
        ('optional_no_ca', 'Optional, and do not need to be valid')
    )

    VERIFY_CRL_LIST = (
        ('none', 'Do not check'),
        ('leaf', 'Only check end-entity cert'),
        ('chain', 'Check all chain certs')
    )

    PROTOCOL_LIST = (
        ('+SSLv3 +TLSv1 +TLSv1.1 +TLSv1.2', 'SSL Version 3 (INSECURE) minimum'),
        ('+TLSv1 +TLSv1.1 +TLSv1.2', 'TLS version 1 minimum'),
        ('+TLSv1.1 +TLSv1.2', 'TLS version 1.1 minimum'),
        ('+TLSv1.2', 'TLS version 1.2 minimum'),
    )
    ENGINE_LIST = get_openssl_engines()

    protocols                   = ChoiceField(required=True, choices=PROTOCOL_LIST)
    engine                      = ChoiceField(required=False, choices=ENGINE_LIST)
    verifyclient                = ChoiceField(required=False, choices=VERIFY_LIST)
    verify_crl                  = ChoiceField(required=True, choices=VERIFY_CRL_LIST)
    certificate                 = ChoiceField(required=True)
    honorcipherorder            = BooleanField(required=False)
    ocsp_responder_enable       = BooleanField(required=False)
    ocsp_responder_override     = BooleanField(required=False)
    hpkp_enable                 = BooleanField(required=False)
    enable_ocsp_stapling        = BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super(ModSSLForm, self).__init__(*args, **kwargs)
        self = bootstrap_tooltips(self)

        # Extract le choices for the certificate selection
        certificate_list = SSLCertificate.objects.filter(is_trusted_ca__ne=True, status__ne='R').only('id', 'cn')
        certificate_choices = list()
        for cert in certificate_list:
            certificate_choices.append((cert.id, cert.cn))

        # Set the choices extracted and set the initial value
        self.fields['certificate'].choices = certificate_choices
        modssl = kwargs.pop('instance')
        if modssl:
            self.initial['certificate'] = modssl.certificate.id

    class Meta:
        document = ModSSL
        widgets = {
            'name'                   : TextInput(attrs={'class': 'form-control'}),
            'ciphers'                : TextInput(attrs={'class': 'form-control'}),
            'redirect_no_cert'       : TextInput(attrs={'class': 'form-control'}),
            'engine'                 : Select(attrs={'class': 'form-control'}),
            'hpkp_other'             : TextInput(attrs={'class': 'form-control'}),
        }

    def clean(self):

        # Uses the certificate id to get the object to store it in ReferenceField
        cert_id = self.cleaned_data.get('certificate')
        cert = SSLCertificate.objects.with_id(cert_id)
        self.cleaned_data['certificate'] = cert

        super(ModSSLForm, self).clean()

        return self.cleaned_data
