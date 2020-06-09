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
__doc__ = 'Django forms dedicated to cluster and system settings'

from django import forms
from django.core.exceptions import ValidationError
from django.forms import TextInput, CheckboxInput, ChoiceField, Textarea, Select, NumberInput
from django.forms.utils import ErrorList
from django.utils.translation import ugettext_lazy as _
from mongodbforms import DocumentForm

from gui.forms.forms_utils import bootstrap_tooltips, DivErrorList
from gui.models.repository_settings import BaseAbstractRepository
from gui.models.system_settings import (DNSSettings, GLOBALSettings, IPSECSettings, LogAnalyserSettings, Node,
                                        NTPSettings, PFSettings, SMTPSettings, SSHSettings)
from vulture_toolkit.network.net_utils import is_resolvable_hostname, is_valid_hostname, is_valid_ip_address
import re


class NTPSettingsForm(DocumentForm):
    """ Django form used to handle NTP Settings
    """

    def __init__(self, *args, **kwargs):
        super(NTPSettingsForm, self).__init__(*args, **kwargs)
        self = bootstrap_tooltips(self)

    class Meta:
        document = NTPSettings
        widgets = {
            'server_address_1': TextInput(attrs={'class': 'form-control'}),
            'server_address_2': TextInput(attrs={'class': 'form-control'}),
            'server_address_3': TextInput(attrs={'class': 'form-control'}),
            'server_address_4': TextInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        """ Be sure of user input match an valid hostname 
        This function check hostname syntax and DNS resolution 
        """
        super(NTPSettingsForm, self).clean()
        for nb in range(1,4):
            strNb = str(nb)
            hostname = self.cleaned_data.get('server_address_'+strNb)
            error_msg = list()
            if not hostname:
                continue
            # Hostname syntax check
            if not is_valid_hostname(hostname):
                error_msg.append(hostname +" : invalid hostname, please check syntax")
            # Hostname DNS check
            elif not is_resolvable_hostname(hostname):
                error_msg.append(hostname +" is unresolvable by DNS")
            #FIXME ??
            #NTP server availability check
            #elif not NTP.ntp_server_is_up(hostname):
            #    error_msg.append(hostname +" didn't answer to NTP request")
            if error_msg:
                self._errors['server_address_'+strNb] = ErrorList(error_msg)
                del self.cleaned_data['server_address_'+strNb]

        return self.cleaned_data


class DNSSettingsForm(DocumentForm):
    """ Django form used to handle DNS Settings
    """
    def __init__(self, *args, **kwargs):
        super(DNSSettingsForm, self).__init__(*args, **kwargs)
        self = bootstrap_tooltips(self)

    class Meta:
        document = DNSSettings
        widgets = {
            'dns_domain': TextInput(attrs={'class': 'form-control'}),
            'server_address_1': TextInput(attrs={'class': 'form-control'}),
            'server_address_2': TextInput(attrs={'class': 'form-control'}),
            'server_address_3': TextInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        """ Be sure of user input match an valid hostname 
        This function check hostname syntax and DNS resolution 
        """
        cleaned_data = super(DNSSettingsForm, self).clean()
        for nb in range(1, 3):
            field_name = "server_address_{}".format(nb)
            ip_addr = cleaned_data.get(field_name)
            if not ip_addr:
                continue
            #IP Address syntax check
            if not is_valid_ip_address(ip_addr):
                self.add_error(field_name, "{} : invalid IP address, please check syntax".format(ip_addr))


class NodeForm(DocumentForm):
    """ Cluster form representation
    """
    def __init__(self, *args, **kwargs):
        super(NodeForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        # Node name is read only if we edit an existing Node instance
        if instance and type(instance.pk) is not property:
            self.fields['name'].widget.attrs['readonly'] = True
        self = bootstrap_tooltips(self)

    def clean_default_ipv4_gw(self):
        """ Ensure Default Gateway is an IP Address
        """
        ipv4_addr = self.cleaned_data.get('default_ipv4_gw')
        if ipv4_addr and not is_valid_ip_address(ipv4_addr):
            self._errors['default_ipv4_gw'] = _("Invalid IPV4 address, please check syntax")
        return ipv4_addr

    def clean_default_ipv6_gw(self):
        """ Ensure Default Gateway is an IP Address
        """
        ipv6_addr = self.cleaned_data.get('default_ipv6_gw')
        if ipv6_addr and not is_valid_ip_address(ipv6_addr):
            self._errors['default_ipv6_gw'] = _("Invalid IPV6 address, please check syntax")
        return ipv6_addr

    def clean_name(self):
        """ Clean Node name. User can't change node name if it's already set

        """
        instance = getattr(self, 'instance', None)
        if instance and type(instance.pk) is not property:
            return instance.name
        else:
            return self.cleaned_data['name']

    class Meta:
        document = Node
        widgets = {
            'name': TextInput(attrs={'class': 'form-control'}),
            'default_ipv4_gw': TextInput(attrs={'class': 'form-control'}),
            'default_ipv6_gw': TextInput(attrs={'class': 'form-control'}),
            'static_route': Textarea(attrs={'class': 'form-control'}),
        }
        fields = {
            'name', 'default_ipv4_gw', 
            'name', 'default_ipv6_gw', 
            'name', 'static_route'
        }
        exclude = ['temporary_key']


class NewNodeForm(NodeForm):
    class Meta(NodeForm.Meta):
        fields = ('name')


class SMTPSettingsForm(DocumentForm):
    """

    """
    def __init__(self, *args, **kwargs):
        super(SMTPSettingsForm, self).__init__(*args, **kwargs)
        self = bootstrap_tooltips(self)

    class Meta:
        document = SMTPSettings
        widgets = {
            'domain_name': TextInput(attrs={'class': 'form-control'}),
            #'origin_name': TextInput(attrs={'class': 'form-control'}),
            #'relay_host': TextInput(attrs={'class': 'form-control'}),
            'smtp_server': TextInput(attrs={'class': 'form-control'}),
        }


class IPSECSettingsForm(DocumentForm):
    """

    """
    def __init__(self, *args, **kwargs):
        super(IPSECSettingsForm, self).__init__(*args, **kwargs)
        self = bootstrap_tooltips(self)

        KEYEXCHANGE = (
            ('ikev2', 'IKE version 2'),
        )
        DPD = (
            ('none', 'None'),
            ('clear', 'Clear'),
            ('hold', 'Hold'),
            ('restart', 'Restart'),
        )
        AUTHBY = (
            ('secret', 'PSK Authentication'),
        )

        self.fields['ipsec_keyexchange'] = ChoiceField(choices=KEYEXCHANGE, required=True, widget=Select(attrs={'class': 'form-control'}))
        self.fields['ipsec_dpdaction'] = ChoiceField(choices=DPD, required=True, widget=Select(attrs={'class': 'form-control'}))
        self.fields['ipsec_authby'] = ChoiceField(choices=AUTHBY, required=True, widget=Select(attrs={'class': 'form-control'}))

    class Meta:
        document = IPSECSettings
        widgets = {
            'enabled': CheckboxInput(attrs={'class': 'js-switch'}),
            'ipsec_type': TextInput(attrs={'class': 'form-control'}),
            'ipsec_authby': TextInput(attrs={'class': 'form-control'}),
            'ipsec_psk': TextInput(attrs={'class': 'form-control'}),
            'ipsec_ike': TextInput(attrs={'class': 'form-control'}),
            'ipsec_esp': TextInput(attrs={'class': 'form-control'}),
            'ipsec_dpdaction': TextInput(attrs={'class': 'form-control'}),
            'ipsec_dpddelay': TextInput(attrs={'class': 'form-control'}),
            'ipsec_ikelifetime': TextInput(attrs={'class': 'form-control'}),
            'ipsec_keylife': TextInput(attrs={'class': 'form-control'}),
            'ipsec_right': TextInput(attrs={'class': 'form-control'}),
            'ipsec_rightsubnet': TextInput(attrs={'class': 'form-control'}),
            'ipsec_leftsubnet': TextInput(attrs={'class': 'form-control'}),
            'ipsec_leftid': TextInput(attrs={'class': 'form-control'}),
            'ipsec_fragmentation': CheckboxInput(attrs={'class': 'js-switch'}),
            'ipsec_forceencaps': CheckboxInput(attrs={'class': 'js-switch'}),
            'ipsec_rekey': CheckboxInput(attrs={'class': 'js-switch'}),
        }



class GLOBALSettingsForm(DocumentForm):
    """

    """
    def __init__(self, *args, **kwargs):
        super(GLOBALSettingsForm, self).__init__(*args, **kwargs)
        self = bootstrap_tooltips(self)
        repo_lst = BaseAbstractRepository.get_data_repositories()
        data_repo_lst = [(repo.id, repo.repo_name) for repo in repo_lst]
        try:
            self.fields['logs_repository'] = ChoiceField(choices=data_repo_lst, required=True,
                                            widget=Select(attrs={'class': 'form-control'}))
        except:
            pass


    def clean_logs_repository(self):
        data = self.cleaned_data.get('logs_repository')
        self.cleaned_data['logs_repository'] = data
        return data


    def clean_owasp_crs_url(self):
        field_name = "owasp_crs_url"
        field_value = self.cleaned_data.get(field_name, "")
        owasp_regex = 'https://github\.com/SpiderLabs/owasp-modsecurity-crs/archive/v([0-9|\.]+)/master\.zip'
        owasp_regex_cpl = re.compile(owasp_regex)
        if not owasp_regex_cpl.match(field_value):
            raise ValidationError("This field must match the regex : {}".format(owasp_regex))

        # Always return a value to use as the new cleaned data, even if
        # this method didn't change it.
        return field_value


    class Meta:
        document = GLOBALSettings
        exclude  =  ['remote_ip_internal_proxy']
        widgets = {
            'owasp_crs_url': TextInput(attrs={'class': 'form-control'}),
            'trustwave_url': TextInput(attrs={'class': 'form-control'}),
            'trustwave_user': TextInput(attrs={'class': 'form-control'}),
            'portal_cookie' : TextInput(attrs={'class': 'form-control'}),
            'app_cookie' : TextInput(attrs={'class': 'form-control'}),
            'public_token' : TextInput(attrs={'class': 'form-control'}),
            'city_name' : TextInput(attrs={'class': 'form-control'}),
            'latitude' : TextInput(attrs={'class': 'form-control'}),
            'longitude' : TextInput(attrs={'class': 'form-control'}),
            'gui_timeout': TextInput(attrs={'class': 'form-control'}),
            'source_branch': TextInput(attrs={'class': 'form-control'}),
            'x_vlt_token': TextInput(attrs={'class': 'form-control'}),
        }


class SSHSettingsForm(DocumentForm):
    """

    """
    def __init__(self, *args, **kwargs):
        super(SSHSettingsForm, self).__init__(*args, **kwargs)
        self = bootstrap_tooltips(self)

    class Meta:
        document = SSHSettings
        widgets = {
            'enabled': CheckboxInput(attrs={'class': 'js-switch'}),
        }


class PFSettingsForm(DocumentForm):
    """

    """
    def __init__(self, *args, **kwargs):
        super(PFSettingsForm, self).__init__(*args, **kwargs)
        self = bootstrap_tooltips(self, exclude='repository_choices')

        repo_lst = BaseAbstractRepository.get_data_repositories()
        data_repo_lst = list()
        for rep in repo_lst:
            data_repo_lst.append((rep.id, rep.repo_name))

        self.fields['repository_choices'] = ChoiceField(choices=data_repo_lst, required=False,
                                         widget=Select(attrs={'class': 'form-control'}))

        repo_lst = BaseAbstractRepository.get_syslog_repositories()
        syslog_repo_lst = list()
        syslog_repo_lst.append(("",""))
        for rep in repo_lst:
            syslog_repo_lst.append((rep.id, rep.repo_name))

        self.fields['repository_syslog'] = ChoiceField(choices=syslog_repo_lst, required=False,
                                         widget=Select(attrs={'class': 'form-control'}))

        self.fields['repository_type'] = ChoiceField(choices=PFSettings.TYPE_REPO, required=True, 
                                        widget=Select(attrs={'class': 'form-control'}))

    def clean_repository_choices(self):
        data = self.cleaned_data.get('repository_choices')
        self.cleaned_data['data_repository'] = data
        return data

    def clean_repository_syslog(self):
        data = self.cleaned_data.get('repository_syslog')
        if data:
            self.cleaned_data['syslog_repository'] = data
        return data

    def clean_repository_type(self):
        data = self.cleaned_data.get('repository_type')
        self.cleaned_data['repository_type'] = data
        return data

    class Meta:
        document = PFSettings
        widgets = {
            'enabled': CheckboxInput(attrs={'class': 'form-control'}),
            'pf_blacklist': Textarea(attrs={'class': 'form-control'}),
            'pf_whitelist': Textarea(attrs={'class': 'form-control'}),
            'pf_rules_text': Textarea(attrs={'class': 'form-control'}),
            'pf_limit_states': NumberInput(attrs={'class': 'form-control'}),
            'pf_limit_frags': NumberInput(attrs={'class': 'form-control'}),
            'pf_limit_src': NumberInput(attrs={'class': 'form-control'}),
        }

    def clean_pf_rules(self):
        pf_rules = self.cleaned_data.get('pf_rules')
        return pf_rules.replace("\r", '')


class MigrationForm(forms.Form):
    """

    """
    def __init__(self, *args, **kwargs):
        super(MigrationForm, self).__init__(*args, **kwargs)
        self = bootstrap_tooltips(self)

    file = forms.FileField(required=True, label='Selectionner un fichier')


class LogAnalyserSettingsForm(DocumentForm):

    class Meta:
        document = LogAnalyserSettings


