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
__doc__ = 'Django forms dedicated to network settings'


from bson.objectid import ObjectId
from django.forms import TextInput, ChoiceField, CheckboxInput, NumberInput, Select, Textarea
from django.utils.translation import ugettext_lazy as _
from mongodbforms import DocumentForm

from gui.forms.forms_utils import bootstrap_tooltips
from gui.models.application_settings import Application
from gui.models.network_settings import Listener, Loadbalancer, BALANCING_CHOICES
from vulture_toolkit.network.interface import Interface as InterfaceHelper
from vulture_toolkit.network.net_utils import is_valid_ip_address

import logging


class LoadbalancerForm(DocumentForm):
    def __init__(self, *args, **kwargs):
        super(LoadbalancerForm, self).__init__(*args, **kwargs)


    def clean(self):
        super(LoadbalancerForm, self).clean()

        listener = self.cleaned_data.get('incoming_listener')
        port = self.cleaned_data.get('incoming_port')
        ip_port = "{}:{}".format(listener.ip, port)
        for app in Application.objects.all():
            listen_addresses = []
            for listener in app.listeners:
                listen_addresses.append("{}:{}".format(listener.address.ip, listener.port))

            if ip_port in listen_addresses:
                self._errors['Incoming listener & port'] = _("This IP:Port is already used in an application")
                break          

    class Meta:
        document = Loadbalancer
        widgets = {
            'name'             : TextInput(attrs={'class': 'form-control'}),
            'incoming_listener': Select(attrs={'class': 'form-control select2'}),
            'incoming_port'    : NumberInput(attrs={'class': 'form-control'}),
            'timeout_connect'  : NumberInput(attrs={'class': 'form-control'}),
            'timeout_client'   : NumberInput(attrs={'class': 'form-control'}),
            'timeout_server'   : NumberInput(attrs={'class': 'form-control'}),
            'timeout_tunnel'   : NumberInput(attrs={'class': 'form-control'}),
            'timeout_client_fin'   : NumberInput(attrs={'class': 'form-control'}),
            'maxconn'          : NumberInput(attrs={'class': 'form-control'}),
            'balance'          : Select(attrs={'class': 'form-control select2'}, choices=BALANCING_CHOICES),
            'balancing_param'  : TextInput(attrs={'class': "form-control"}),
            'listen_conf'      : Textarea(attrs={'class': "form-control"}),
            'ssl_profile'      : Select(attrs={'class': "form-control select2"}),
            'http_mode': CheckboxInput(attrs={'class': 'js-switch'}),
            'enable_tls': CheckboxInput(attrs={'class': 'js-switch'}),
            'http_keepalive': CheckboxInput(attrs={'class': 'js-switch'}),
            'http_sticky_session': CheckboxInput(attrs={'class': 'js-switch'})
        }

        exclude = {'backends'}


class InetAddressForm(DocumentForm):
    """ Listener form representation
    """

    device = ChoiceField(required=False)

    def __init__(self, custom_choices=None, selected_device=None, *args, **kwargs):
        super(InetAddressForm, self).__init__(*args, **kwargs)
        if custom_choices:
            self.fields['device'].choices = custom_choices
        if selected_device:
            self.fields['device'].initial=selected_device

        self = bootstrap_tooltips(self, exclude={'device'})


    class Meta:
        document = Listener
        widgets = {
            'alias'    : TextInput(attrs={'class':'form-control'}),
            'ip'       : TextInput(attrs={'class': 'form-control'}),
            'prefixlen': TextInput(attrs={'class': 'form-control'}),
            'is_gui'   : CheckboxInput(attrs={'class': 'js-switch'}),
            'is_carp'  : CheckboxInput(attrs={'class': 'js-switch'}),
            'carp_vhid': NumberInput(attrs={'class': 'form-control'}),
        }
        exclude = {'version', 'carp_passwd', 'carp_priority'}

        def clean_carp_vhid(self):
            """ Ensure carp_vhid is unique and a positive integer below 128

            :return:
            """
            data = self.cleaned_data.get('carp_vhid')
            is_carp = self.cleaned_data.get('is_carp')

            if is_carp:
                try:
                    data = int(data)
                    if data not in range(1, 128):
                        self._errors['carp_vhid'] = _("CARP VHID must be a positive"
                                                      " integer (below 128)")

                    """Checking if carp_vhid is not already used by an other CARP
                    listener
                    """
                    existing_vhid = Listener.objects.distinct(field='carp_vhid')
                    inet_id = self.initial.get('id')
                    #Excluding carp_vhid used by current edited listener
                    if inet_id is not None:
                        inet = Listener.objects.with_id(ObjectId(inet_id))
                        if inet.carp_vhid in existing_vhid:
                            existing_vhid.remove(inet.carp_vhid)

                    if data in existing_vhid:
                        self._errors['carp_vhid'] = _("This VHID is already used "
                                                      "for another CARP listener")

                except Exception as e:
                    logger = logging.getLogger('listeners')
                    logger.debug(str(e))
                    self._errors['carp_vhid'] = _("CARP VHID must be a positive "
                                                  "integer (below 128)")
            else:
                data = None

            return data



    def clean(self):
        """ Be sure of user input match an valid parameter for inet
         creation
        """
        super(InetAddressForm, self).clean()
        #IP Address validation
        ip_addr = self.cleaned_data.get('ip')
        if not is_valid_ip_address(ip_addr):
            self._errors['ip'] = _("Invalid IP address, please check syntax")      

        ip = InterfaceHelper.create_inet_object(self.cleaned_data)

        if ip and ip.netmask:
            self.cleaned_data['prefixlen'] = ip.netmask
            self.cleaned_data['version'] = ip.ip_address.version
        else:
            self._errors['prefixlen'] = _("Invalid prefixlen, you can only "
                                          "specify dotted-quad (x.x.x.x) or "
                                              "CIDR notation (/x)")

        return self.cleaned_data


class ManagementForm(InetAddressForm):
    def __init__(self, custom_choices=None, *args, **kwargs):
        super(InetAddressForm, self).__init__(*args, **kwargs)
        self.fields['ip'].help_text = _("Main IP Address of Node")
        self = bootstrap_tooltips(self)


    class Meta:
        document = Listener
        widgets = {
            'ip': TextInput(attrs={'class': 'form-control'}),
            'prefixlen': TextInput(attrs={'class': 'form-control'}),
        }
        fields = {'ip', 'prefixlen'}