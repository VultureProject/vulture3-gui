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
__doc__ = 'Django forms dedicated to repository settings'


# Django system imports
from django.core.validators import validate_ipv46_address, RegexValidator
from django.forms import TextInput, ChoiceField, CheckboxInput, NumberInput, PasswordInput
from django.utils.translation import ugettext_lazy as _
from mongodbforms import DocumentForm

# Django project imports
from gui.forms.forms_utils import bootstrap_tooltips
from gui.models.repository_settings import (ElasticSearchRepository, KerberosRepository, LDAPRepository,
                                            MongoDBRepository, OTPRepository, SQLRepository, RadiusRepository,
                                            SyslogRepository, PASSWORD_SALT_POSITION)
from vulture_toolkit.auth.kerberos_client import test_keytab

# Required exceptions imports
from django.core.exceptions import ValidationError

# Extern modules imports
from re import match as re_match


class SQLRepositoryForm(DocumentForm):
    def __init__(self, *args, **kwargs):
        super(SQLRepositoryForm, self).__init__(*args, **kwargs)
        self = bootstrap_tooltips(self)

    def clean_db_host(self):
        data = self.cleaned_data['db_host']
        RegexValidator('^[A-Za-z0-9-.]*$', data)
        return data

    def clean(self):
        super(SQLRepositoryForm, self).clean()
        return self.cleaned_data


    class Meta:
        document = SQLRepository
        widgets = {
            'repo_name': TextInput(attrs={'class': 'form-control'}),
            'db_host': TextInput(attrs={'class': 'form-control'}),
            'db_port': TextInput(attrs={'class': 'form-control'}),
            'db_name': TextInput(attrs={'class': 'form-control'}),
            'db_user': TextInput(attrs={'class': 'form-control'}),
            'db_password': PasswordInput(render_value=True,
                                         attrs={'class': 'form-control'}),
            'db_table': TextInput(attrs={'class': 'form-control'}),
            'db_user_column': TextInput(attrs={'class': 'form-control'}),
            'db_password_column': TextInput(attrs={'class': 'form-control'}),
            'db_password_salt': TextInput(attrs={'class': 'form-control'}),
            'db_change_pass_column': TextInput(attrs={'class': 'form-control'}),
            'db_change_pass_value': TextInput(attrs={'class': 'form-control'}),
            'db_locked_column': TextInput(attrs={'class': 'form-control'}),
            'db_locked_value': TextInput(attrs={'class': 'form-control'}),
            'db_user_phone_column': TextInput(attrs={'class': 'form-control'}),
            'db_user_email_column': TextInput(attrs={'class': 'form-control'}),
            'oauth2_attributes': TextInput(attrs={'class': 'form-control'}),
            'enable_oauth2': CheckboxInput(attrs={'class': 'js-switch'})
        }

class SyslogRepositoryForm(DocumentForm):

    def __init__(self, *args, **kwargs):
        super(SyslogRepositoryForm, self).__init__(*args, **kwargs)
        self = bootstrap_tooltips(self)

        PROTO = (
            ('UDP', 'UDP'),
            ('TCP', 'TCP'),
        )

        self.fields['syslog_protocol'] = ChoiceField(choices=PROTO, required=True)

    def clean_syslog_host(self):
        data = self.cleaned_data['syslog_host']
        validate_ipv46_address(data)
        return data

    class Meta:
        document = SyslogRepository
        widgets = {
            'repo_name': TextInput(attrs={'class': 'form-control'}),
            'syslog_host': TextInput(attrs={'class': 'form-control'}),
            'syslog_port': TextInput(attrs={'class': 'form-control'}),
            'syslog_facility': TextInput(attrs={'class': 'form-control'}),
            'syslog_security': TextInput(attrs={'class': 'form-control'}),
        }




class KerberosRepositoryForm(DocumentForm):

    def __init__(self, *args, **kwargs):
        super(KerberosRepositoryForm, self).__init__(*args, **kwargs)
        self = bootstrap_tooltips(self)

    class Meta:
        document = KerberosRepository
        widgets = {
            'repo_name': TextInput(attrs={'class': 'form-control'}),
            'realm': TextInput(attrs={'class': 'form-control'}),
            'domain_realm': TextInput(attrs={'class': 'form-control'}),
            'kdc': TextInput(attrs={'class': 'form-control'}),
            'admin_server': TextInput(attrs={'class': 'form-control'}),
            'krb5_service': TextInput(attrs={'class': 'form-control'}),
            'keytab' : TextInput(attrs={'class': 'form-control'})
            }

    def is_valid(self, test=False):
        if not test:
            keytab = self.data['keytab']
            if keytab:
                valid = test_keytab(keytab)
                if not valid['status']:
                    self.add_error('keytab', valid['reason'])
                    return False
                elif self.data['krb5_service'] not in valid['reason']:
                    self.add_error('keytab', "Keytab does not match with service name.")
                    return False
        return super(KerberosRepositoryForm, self).is_valid()



class LDAPRepositoryForm(DocumentForm):
    def __init__(self, *args, **kwargs):
        super(LDAPRepositoryForm, self).__init__(*args, **kwargs)
        self = bootstrap_tooltips(self)

    def clean_ldap_host(self):
        data = self.cleaned_data['ldap_host']
        RegexValidator('^[A-Za-z0-9-.]*$', data)
        return data

    def clean_ldap_filter(self, field_name):
        """ Function used to validate LDAP filter
        validation condition: need to have leading and trailing parentheses

        :param field_name: Name of field to clean
        :return: Cleaned data
        """
        data = self.cleaned_data[field_name]
        err_msg = "This field requires leading and trailing parentheses."
        if data and not re_match('^\(.*\)$', data):
            self._errors[field_name] = [str(_(err_msg))]
        return data

    def clean_ldap_user_filter(self):
        return self.clean_ldap_filter('ldap_user_filter')

    def clean_ldap_user_account_locked_attr(self):
        return self.clean_ldap_filter('ldap_user_account_locked_attr')

    def clean_ldap_user_change_password_attr(self):
        return self.clean_ldap_filter('ldap_user_change_password_attr')

    def clean_ldap_group_filter(self):
        return self.clean_ldap_filter('ldap_group_filter')

    def connection_is_valid(self):
        form_fields = (
            "ldap_host",
            "ldap_password",
            "ldap_port",
            "ldap_connection_dn",
            "ldap_protocol",
            "ldap_encryption_scheme"
        )
        for fieldname, value in self.fields.items():
            if fieldname not in form_fields:
                del self.fields[fieldname]
        return self.is_valid()

    def user_search_is_valid(self):

        form_fields = (
            "ldap_user_scope",
            "ldap_user_ou",
            "ldap_user_attr",
            "ldap_user_filter",
            "ldap_user_account_locked_attr",
            "ldap_user_change_password_attr",
            "ldap_user_mobile_attr",
            "ldap_user_email_attr",
        )
        for fieldname, value in self.fields.items():
            if fieldname not in form_fields:
                del self.fields[fieldname]
        return self.is_valid()

    def clean(self):
        super(LDAPRepositoryForm, self).clean()
        return self.cleaned_data


    class Meta:
        document = LDAPRepository
        widgets = {
            'repo_name': TextInput(attrs={'class': 'form-control'}),
            'ldap_host': TextInput(attrs={'class': 'form-control'}),
            'ldap_port': TextInput(attrs={'class': 'form-control'}),
            'ldap_connection_dn': TextInput(attrs={'class': 'form-control'}),
            'ldap_password': PasswordInput(render_value=True, attrs={'class': 'form-control'}),
            'ldap_base_dn': TextInput(attrs={'class': 'form-control'}),
            'ldap_user_dn': TextInput(attrs={'class': 'form-control'}),
            'ldap_user_attr': TextInput(attrs={'class': 'form-control'}),
            'ldap_user_filter': TextInput(attrs={'class': 'form-control'}),
            'ldap_user_account_locked_attr': TextInput(attrs={'class': 'form-control'}),
            'ldap_user_change_password_attr': TextInput(attrs={'class': 'form-control'}),
            'ldap_user_groups_attr': TextInput(attrs={'class': 'form-control'}),
            'ldap_user_mobile_attr': TextInput(attrs={'class': 'form-control'}),
            'ldap_user_email_attr': TextInput(attrs={'class': 'form-control'}),
            'ldap_group_dn': TextInput(attrs={'class': 'form-control'}),
            'ldap_group_attr': TextInput(attrs={'class': 'form-control'}),
            'ldap_group_filter': TextInput(attrs={'class': 'form-control'}),
            'ldap_group_member_attr': TextInput(attrs={'class': 'form-control'}),
            'oauth2_attributes': TextInput(attrs={'class': 'form-control'}),
            'enable_oauth2': CheckboxInput(attrs={'class': 'js-switch'})
        }


class MongoDBRepositoryForm(DocumentForm):
    REPO_TYPE = [
        ('data', 'Data'),
        ('auth', 'Authentication'),
    ]

    def __init__(self, *args, **kwargs):
        super(MongoDBRepositoryForm, self).__init__(*args, **kwargs)
        self = bootstrap_tooltips(self)
        self.fields['repo_type'] = ChoiceField(choices=self.REPO_TYPE)
        self.fields['db_password_salt_position'] = ChoiceField(choices=PASSWORD_SALT_POSITION, required=False)
        self.fields['db_password_salt_position'].empty_label = None

    def is_valid(self, connection_test=False, user_search=False, **kwargs):
        """
        form_fields = [
            "db_host",
            "repo_name",
            "repo_type",
            "db_user",
            "db_password",
            "db_port",
            "db_name",
        ]
        if not connection_test and self.data.get('repo_type') == 'data':
            additionnal_fields = [
                'db_access_collection_name',
                'db_security_collection_name',
            ]
            form_fields.extend(additionnal_fields)

        for fieldname, value in self.fields.items():
            if fieldname not in form_fields:
                del self.fields[fieldname]
        """
        return super(MongoDBRepositoryForm, self).is_valid()

    def clean(self):
        super(MongoDBRepositoryForm, self).clean()
        return self.cleaned_data

    class Meta:
        document = MongoDBRepository
        exclude = 'is_internal'
        widgets = {
            'repo_name': TextInput(attrs={'class': 'form-control'}),
            'db_host': TextInput(attrs={'class': 'form-control'}),
            'db_port': TextInput(attrs={'class': 'form-control'}),
            'db_name': TextInput(attrs={'class': 'form-control'}),
            'db_user': TextInput(attrs={'class': 'form-control'}),
            'db_password': PasswordInput(render_value=True,
                                         attrs={'class': 'form-control'}),
            'db_user_column': TextInput(attrs={'class': 'form-control'}),
            'db_password_column': TextInput(attrs={'class': 'form-control'}),
            'db_collection_name': TextInput(attrs={'class': 'form-control'}),
            'db_password_salt': TextInput(attrs={'class': 'form-control'}),
            'db_password_salt': TextInput(attrs={'class': 'form-control'}),
            'db_change_pass_column': TextInput(attrs={'class': 'form-control'}),
            'db_change_pass_value': TextInput(attrs={'class': 'form-control'}),
            'db_user_phone_column': TextInput(attrs={'class': 'form-control'}),
            'db_user_email_column': TextInput(attrs={'class': 'form-control'}),
            'db_access_collection_name': TextInput(attrs={'class': 'form-control'}),
            'db_packetfilter_collection_name': TextInput(attrs={'class': 'form-control'}),
            'db_diagnostic_collection_name': TextInput(attrs={'class': 'form-control'}),
            'db_vulturelogs_collection_name': TextInput(attrs={'class': 'form-control'}),
            'oauth2_attributes': TextInput(attrs={'class': 'form-control'}),
            'replicaset': TextInput(attrs={'class': 'form-control'}),
            'enable_oauth2': CheckboxInput(attrs={'class': 'js-switch'})
        }


class ElasticSearchRepositoryForm(DocumentForm):

    def __init__(self, *args, **kwargs):
        super(ElasticSearchRepositoryForm, self).__init__(*args, **kwargs)
        self = bootstrap_tooltips(self)

    def is_valid(self, connection_test=False, **kwargs):
        """
        form_fields = [
            "es_host",
            "repo_name",
            "es_user",
            "es_password",
        ]
        if not connection_test and self.data.get('repo_type') == 'data':
            additionnal_fields = [
                'es_access_collection_name',
                'es_security_collection_name',
            ]
            form_fields.extend(additionnal_fields)

        for fieldname, value in self.fields.items():
            if fieldname not in form_fields:
                del self.fields[fieldname]
        """
        return super(ElasticSearchRepositoryForm, self).is_valid()

    def clean_es_host(self):
        field_name = "es_host"
        field_value = self.cleaned_data.get(field_name, "")
        for host in field_value.split(','):
            if host.startswith('https://'):
                raise ValidationError("Vulture does not handle HTTPS connection on ElasticSearch cluster.")

        # Always return a value to use as the new cleaned data, even if
        # this method didn't change it.
        return field_value


    class Meta:
        document = ElasticSearchRepository
        widgets = {
            'repo_name': TextInput(attrs={'class': 'form-control'}),
            'es_host': TextInput(attrs={'class': 'form-control'}),
            'es_user': TextInput(attrs={'class': 'form-control'}),
            'es_password': PasswordInput(attrs={'class': 'form-control'}),
            'es_access_index_name': TextInput(attrs={'class': 'form-control'}),
            'es_access_type_name': TextInput(attrs={'class': 'form-control'}),
            'es_packetfilter_index_name': TextInput(attrs={'class': 'form-control'}),
            'es_packetfilter_type_name': TextInput(attrs={'class': 'form-control'}),
            'es_diagnostic_index_name': TextInput(attrs={'class': 'form-control'}),
            'es_diagnostic_type_name': TextInput(attrs={'class': 'form-control'}),
            'es_vulturelogs_index_name': TextInput(attrs={'class': 'form-control'}),
            'es_vulturelogs_type_name': TextInput(attrs={'class': 'form-control'}),
            'es_dateformat': TextInput(attrs={'class': 'form-control'}),
            'oauth2_attributes': TextInput(attrs={'class': 'form-control'})
        }


class OTPRepositoryForm(DocumentForm):
    def __init__(self, *args, **kwargs):
        super(OTPRepositoryForm, self).__init__(*args, **kwargs)
        self = bootstrap_tooltips(self)

    def clean(self):
        super(OTPRepositoryForm, self).clean()

        if self.cleaned_data.get('otp_type') == 'email' and \
                        self.cleaned_data.get('otp_mail_service') == '':
            self._errors['otp_mail_service'] = 'This field is required'
        if self.cleaned_data.get('otp_type') == 'phone' and \
                        self.cleaned_data.get('otp_phone_service') == '':
            self._errors['otp_phone_service'] = 'This field is required'
        if self.cleaned_data.get('otp_type') == 'onetouch' and \
                        self.cleaned_data.get('otp_phone_service') == '':
            self._errors['otp_phone_service'] = 'This field is required'
        if self.cleaned_data.get('otp_type') == "totp" and \
                not self.cleaned_data.get('otp_label'):
            self._errors['otp_label'] = "This field is required"

        return self.cleaned_data

    class Meta:
        document = OTPRepository
        widgets = {
            'repo_name': TextInput(attrs={'class': 'form-control'}),
            'api_key': TextInput(attrs={'class': 'form-control'}),
            'key_length': NumberInput(attrs={'class': 'form-control'}),
            'otp_label': TextInput(attrs={'class': 'form-control'}),
        }


class RadiusRepositoryForm(DocumentForm):
    def __init__(self, *args, **kwargs):
        super(RadiusRepositoryForm, self).__init__(*args, **kwargs)
        self = bootstrap_tooltips(self)

    class Meta:
        document = RadiusRepository
        widgets = {
            'repo_name': TextInput(attrs={'class': 'form-control'}),
            'radius_host': TextInput(attrs={'class': 'form-control'}),
            'radius_port': TextInput(attrs={'class': 'form-control'}),
            'radius_nas_id': TextInput(attrs={'class': 'form-control'}),
            'radius_secret': TextInput(attrs={'class': 'form-control'}),
            'radius_retry': TextInput(attrs={'class': 'form-control'}),
            'radius_timeout': TextInput(attrs={'class': 'form-control'}),
        }