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
__doc__ = 'Django forms dedicated to application settings'

from bson.objectid import ObjectId
from django.conf import settings
from django.forms import TextInput, MultipleChoiceField, ChoiceField, Select, HiddenInput, CharField, Textarea, SelectMultiple, CheckboxInput, BooleanField
from django.utils.translation import ugettext_lazy as _
from mongodbforms import DocumentForm

from gui.forms.forms_utils import bootstrap_tooltips
from gui.kerberos_backend import KerberosBackend
from gui.models.application_settings import Application, SSL_PROTOCOLS
from gui.models.dataset_settings import Dataset
from gui.models.modsec_settings import ModSecRulesSet
from gui.models.network_settings import Loadbalancer
from gui.models.repository_settings import BaseAbstractRepository, LDAPRepository
from gui.models.ssl_certificate import SSLCertificate
from gui.models.system_settings import Cluster
from gui.models.template_settings import portalTemplate


class ApplicationForm(DocumentForm):
    """ Application form representation
    """
    proxy_add_header                   = BooleanField(required=False, widget=CheckboxInput(attrs={'class': 'js-switch'}))
    enabled                            = BooleanField(required=False, widget=CheckboxInput(attrs={'class': 'js-switch'}))
    is_model                           = BooleanField(required=False, widget=CheckboxInput(attrs={'class': 'js-switch'}), help_text="Application template used to generate new ones")
    learning                           = BooleanField(required=False, widget=CheckboxInput(attrs={'class': 'js-switch'}))
    learning_block                     = BooleanField(required=False, widget=CheckboxInput(attrs={'class': 'js-switch'}))
    force_tls                          = BooleanField(required=False, widget=CheckboxInput(attrs={'class': 'js-switch'}))
    enable_h2                          = BooleanField(required=False, widget=CheckboxInput(attrs={'class': 'js-switch'}))
    enable_rpc                         = BooleanField(required=False, widget=CheckboxInput(attrs={'class': 'js-switch'}))
    need_auth                          = BooleanField(required=False, widget=CheckboxInput(attrs={'class': 'js-switch'}))
    enable_registration                = BooleanField(required=False, widget=CheckboxInput(attrs={'class': 'js-switch'}))
    update_group_registration          = BooleanField(required=False, widget=CheckboxInput(attrs={'class': 'js-switch'}))
    enable_oauth2                      = BooleanField(required=False, widget=CheckboxInput(attrs={'class': 'js-switch'}))
    enable_stateless_oauth2            = BooleanField(required=False, widget=CheckboxInput(attrs={'class': 'js-switch'}))
    enable_ws                          = BooleanField(required=False, widget=CheckboxInput(attrs={'class': 'js-switch'}))
    tracking                           = BooleanField(required=False, widget=CheckboxInput(attrs={'class': 'js-switch'}))
    auth_timeout_restart               = BooleanField(required=False, widget=CheckboxInput(attrs={'class': 'js-switch'}))
    auth_captcha                       = BooleanField(required=False, widget=CheckboxInput(attrs={'class': 'js-switch'}))
    sso_enabled                        = BooleanField(required=False, widget=CheckboxInput(attrs={'class': 'js-switch'}))
    sso_forward_only_login             = BooleanField(required=False, widget=CheckboxInput(attrs={'class': 'js-switch'}))
    app_display_logout_message         = BooleanField(required=False, widget=CheckboxInput(attrs={'class': 'js-switch'}))
    app_disconnect_portal              = BooleanField(required=False, widget=CheckboxInput(attrs={'class': 'js-switch'}))
    sso_forward_follow_redirect_before = BooleanField(required=False, widget=CheckboxInput(attrs={'class': 'js-switch'}))
    sso_forward_follow_redirect        = BooleanField(required=False, widget=CheckboxInput(attrs={'class': 'js-switch'}))
    sso_forward_return_post            = BooleanField(required=False, widget=CheckboxInput(attrs={'class': 'js-switch'}))
    sso_vulture_agent                  = BooleanField(required=False, widget=CheckboxInput(attrs={'class': 'js-switch'}))
    sso_capture_content_enabled        = BooleanField(required=False, widget=CheckboxInput(attrs={'class': 'js-switch'}))
    sso_replace_content_enabled        = BooleanField(required=False, widget=CheckboxInput(attrs={'class': 'js-switch'}))
    sso_after_post_request_enabled     = BooleanField(required=False, widget=CheckboxInput(attrs={'class': 'js-switch'}))
    ssl_verify_certificate             = BooleanField(required=False, widget=CheckboxInput(attrs={'class': 'js-switch'}))
    ssl_verify_certificate_name        = BooleanField(required=False, widget=CheckboxInput(attrs={'class': 'js-switch'}))
    ssl_verify_certificate_expired     = BooleanField(required=False, widget=CheckboxInput(attrs={'class': 'js-switch'}))
    override_error                     = BooleanField(required=False, widget=CheckboxInput(attrs={'class': 'js-switch'}))
    rewrite_cookie_path                = BooleanField(required=False, widget=CheckboxInput(attrs={'class': 'js-switch'}))
    disablereuse                       = BooleanField(required=False, widget=CheckboxInput(attrs={'class': 'js-switch'}))
    keepalive                          = BooleanField(required=False, widget=CheckboxInput(attrs={'class': 'js-switch'}))
    preserve_host                      = BooleanField(required=False, widget=CheckboxInput(attrs={'class': 'js-switch'}))
    geoip                              = BooleanField(required=False, widget=CheckboxInput(attrs={'class': 'js-switch'}))
    geoip_city                         = BooleanField(required=False, widget=CheckboxInput(attrs={'class': 'js-switch'}))
    reputation                         = BooleanField(required=False, widget=CheckboxInput(attrs={'class': 'js-switch'}))
    cookie_encryption                  = BooleanField(required=False, widget=CheckboxInput(attrs={'class': 'js-switch'}))
    forward_x509_fields                = BooleanField(required=False, widget=CheckboxInput(attrs={'class': 'js-switch'}))
    enable_proxy_protocol              = BooleanField(required=False, widget=CheckboxInput(attrs={'class': 'js-switch'}))

    def __init__(self, *args, **kwargs):
        try:
            self.listeners = kwargs.pop('listeners')
        except KeyError:
            pass

        super(ApplicationForm, self).__init__(*args, **kwargs)

        self = bootstrap_tooltips(self)
        repo_lst = BaseAbstractRepository.get_auth_repositories()
        auth_repo_lst = list()
        for rep in repo_lst:
            auth_repo_lst.append((ObjectId(rep.id), rep.repo_name,))

        mod_sec_choices = list()
        for rule in ModSecRulesSet.objects(type_rule__nin=('wlbl',)):
            mod_sec_choices.append((ObjectId(rule.id), rule.name))

        dataset_list = list()
        dataset_list.append(((None), "------------------------------"))
        for dataset in Dataset.objects(svm_built=True).only('name', 'id'):
            dataset_list.append((ObjectId(dataset.id), dataset.name))

        client_certificate = [('', '---------')]
        for cert in SSLCertificate.objects(is_trusted_ca__ne=True).only('id', 'cn'):
            client_certificate.append(("%sSSLProxyCertificateFile-%s.txt" % (settings.CONF_DIR, cert.id), cert.cn))

        COOCKIE_CIPHER = (
            ('rc4', 'RC4 (128 bits)'),
            ('aes128', 'AES 128 (128 bits)'),
            ('aes256', 'AES 256 (256 bits)'),
        )

        IP_REPUTATION = []
        loganalyser_rules = Cluster.objects.get().system_settings.loganalyser_settings.loganalyser_rules
        for rule in loganalyser_rules:
            tags = rule.tags.split(',')

            for tag in tags:
                IP_REPUTATION.append((tag, tag.capitalize()))

        GEOIP=[]
        for tag in ["AF","AX","AL","DZ","AS","AD","AO","AI","AQ","AG","AR","AM","AW","AU","AT","AZ","BS","BH","BD","BB","BY","BE","BZ","BJ","BM","BT","BO","BQ","BA","BW","BV","BR","IO","BN","BG","BF","BI","KH","CM","CA","CV","KY","CF","TD","CL","CN","CX","CC","CO","KM","CG","CD","CK","CR","CI","HR","CU","CW","CY","CZ","DK","DJ","DM","DO","EC","EG","SV","GQ","ER","EE","ET","FK","FO","FJ","FI","FR","GF","PF","TF","GA","GM","GE","DE","GH","GI","GR","GL","GD","GP","GU","GT","GG","GN","GW","GY","HT","HM","VA","HN","HK","HU","IS","IN","ID","IR","IQ","IE","IM","IL","IT","JM","JP","JE","JO","KZ","KE","KI","KP","KR","KW","KG","LA","LV","LB","LS","LR","LY","LI","LT","LU","MO","MK","MG","MW","MY","MV","ML","MT","MH","MQ","MR","MU","YT","MX","FM","MD","MC","MN","ME","MS","MA","MZ","MM","NA","NR","NP","NL","NC","NZ","NI","NE","NG","NU","NF","MP","NO","OM","PK","PW","PS","PA","PG","PY","PE","PH","PN","PL","PT","PR","QA","RE","RO","RU","RW","BL","SH","KN","LC","MF","PM","VC","WS","SM","ST","SA","SN","RS","SC","SL","SG","SX","SK","SI","SB","SO","ZA","GS","SS","ES","LK","SD","SR","SJ","SZ","SE","CH","SY","TW","TJ","TZ","TH","TL","TG","TK","TO","TT","TN","TR","TM","TC","TV","UG","UA","AE","GB","US","UM","UY","UZ","VU","VE","VN","VG","VI","WF","EH","YE","ZM","ZW"]:
            GEOIP.append((tag,tag))

        self.fields['block_reputation'] = MultipleChoiceField(required=False, choices=set(IP_REPUTATION), widget=SelectMultiple(attrs={'class': 'form-control select2'}))
        self.fields['block_geoip'] = MultipleChoiceField(required=False, choices=set(GEOIP), widget=SelectMultiple(attrs={'class': 'form-control select2'}))
        self.fields['allow_geoip'] = MultipleChoiceField(required=False, choices=set(GEOIP), widget=SelectMultiple(attrs={'class': 'form-control select2'}))

        self.fields['template'].queryset = portalTemplate.objects.filter()
        self.fields['auth_backend'] = ChoiceField(choices=auth_repo_lst, required=False, widget=Select(attrs={'class': 'form-control'}))
        self.fields['auth_backend_fallbacks'] = MultipleChoiceField(choices=auth_repo_lst, required=False, widget=SelectMultiple(attrs={'class': 'form-control select2'}))
        self.fields['redirect_uri'] = CharField(required=False, widget=Textarea(attrs={'cols':80, 'rows':1, 'class': 'form-control'}))
        self.fields['sso_capture_content'] = CharField(required=False, widget=Textarea(attrs={'cols':80, 'rows':2, 'class': 'form-control'}))
        self.fields['sso_replace_pattern'] = CharField(required=False, widget=Textarea(attrs={'cols':40, 'rows':2, 'class': 'form-control'}))
        self.fields['sso_replace_content'] = CharField(required=False, widget=Textarea(attrs={'cols':40, 'rows':2, 'class': 'form-control'}))
        self.fields['sso_after_post_request'] = CharField(required=False, widget=Textarea(attrs={'cols':80, 'rows':2, 'class': 'form-control'}))
        self.fields['rules_set'] = MultipleChoiceField(choices=mod_sec_choices, required=False, widget=SelectMultiple(attrs={'class': 'form-control'}))
        self.fields['datasets'] = ChoiceField(choices=dataset_list, required=False, widget=Select(attrs={'class': 'form-control'}))
        self.fields['ssl_protocol'] = ChoiceField(choices=SSL_PROTOCOLS, required=False, widget=Select(attrs={'class': 'form-control'}))
        self.fields['ssl_client_certificate'] = ChoiceField(choices=client_certificate, required=False, widget=Select(attrs={'class': 'form-control'}))

        self.fields['custom_vhost'] = CharField(required=False, widget=Textarea(attrs={'cols': 80, 'rows': 15, 'class': 'form-control'}))
        self.fields['custom_location'] = CharField(required=False, widget=Textarea(attrs={'cols':80, 'rows':15, 'class': 'form-control'}))
        self.fields['custom_proxy'] = CharField(required=False, widget=Textarea(attrs={'cols': 80, 'rows': 15, 'class': 'form-control'}))

        self.fields['cookie_cipher'] = ChoiceField(choices=COOCKIE_CIPHER, required=False, widget=Select(attrs={'class': 'form-control'}))

        if self.initial.get("auth_backend"):
            repo = BaseAbstractRepository.search_repository(self.initial.get('auth_backend'))
            if isinstance(repo, LDAPRepository):
                try:
                    groups = [(x, x) for x in repo.get_backend().enumerate_groups()]
                except:
                    groups = []
                finally:
                    self.fields['group_registration'] = ChoiceField(choices=groups, required=False, widget=Select(attrs={'class': 'form-control'}))


    def clean_name(self):
        data = self.cleaned_data.get('name')
        if '"' in data:
            self._errors['name'] = "Application name can't contain following character: \""
        return data


    def is_valid(self):
        if type(self.data['public_dir']) != str or ' ' in self.data['public_dir']:
            return False
        else:
            return super(ApplicationForm, self).is_valid()


    def clean(self):
        super(ApplicationForm, self).clean()

        if self.cleaned_data.get('type') == 'balanced' \
                and not self.cleaned_data.get('proxy_balancer'):
            self.add_error('proxy_balancer', 'Please choose a proxy balancer')

        if self.cleaned_data.get('need_auth') and self.cleaned_data.get('auth_type') == "form" and not self.cleaned_data.get('template'):
            self.add_error('template', 'Please choose a template for authentication forms')

        if self.cleaned_data.get('public_name') and '/' in self.cleaned_data.get('public_name'):
            self.add_error('public_name', 'Public FQDN cannot contain "/"')

        if self.cleaned_data.get('public_alias') and '/' in self.cleaned_data.get('public_alias'):
            self.add_error('public_alias', 'Public FQDN cannot contain "/"')

        if ' ' in self.cleaned_data.get('public_dir'):
            self.add_error('public_dir', 'Public dir must not contain space')

        if self.cleaned_data.get('auth_type') != 'form':
            self.cleaned_data['otp_repository'] = None

        # It is not possible to set auth_type AND sso_type to 'kerberos'
        if self.cleaned_data.get('auth_type') == 'kerberos' and self.cleaned_data.get('sso_forward') == 'kerberos':
            self.add_error('auth_type', " You cannot set authentication type AND sso forward type to 'kerberos'")
            self.add_error('sso_forward', " You cannot set authentication type AND sso forward type to 'kerberos'")

        loadbalancers = ["{}:{}".format(lb.incoming_listener.ip, lb.incoming_port) for lb in Loadbalancer.objects.all()]
        for listener in self.listeners:
            if "{}:{}".format(listener.address.ip, listener.port) in loadbalancers:
                self.add_error('Network', " An haproxy configuration is currently using this port with this Listener")

        # If sso_forward == "kerberos" -> verify if auth_backend(fallback) is a KerberosRepository
        error = True
        if self.cleaned_data.get('sso_forward') == 'kerberos':
            for repo in BaseAbstractRepository.get_auth_repositories():
                if str(self.cleaned_data.get('auth_backend')) == str(repo.id) and isinstance(repo.get_backend(), KerberosBackend) :
                    error = False
                    break
                elif str(self.cleaned_data.get('auth_backend_fallback')) == str(repo.id) and isinstance(repo.get_backend(), KerberosBackend):
                    error = False
                    break
            if error:
                self.add_error('sso_forward', "If sso_forward = 'Kerberos', you must have a kerberos backend")

        auth_type = [x[0] for x in Application().AUTH_TYPE]
        if self.cleaned_data.get('sso_enabled') and self.cleaned_data.get('auth_type') not in auth_type:
            self.add_error('auth_type', "Please select a forward type for the SSO Forward configuration")

        # If there is a modsec rulesSet selected
        if self.cleaned_data.get('rules_set', None):
            # And a ModSecPolicy with 'body_inspection' if Off
            modsec_policy = self.cleaned_data.get('modsec_policy', None)
            if not hasattr(modsec_policy, 'seccontentinjection') or not modsec_policy.seccontentinjection:
                self.add_error('rules_set', 'The ModSec Policy must have "Content injection" to On to activate ModSec RulesSet')

        self.cleaned_data["custom_location"] = self.cleaned_data.get('custom_location', "").replace("\r", "")
        self.cleaned_data["custom_vhost"] = self.cleaned_data.get('custom_vhost', "").replace("\r", "")
        self.cleaned_data["custom_proxy"] = self.cleaned_data.get('custom_proxy', "").replace("\r", "")

        return self.cleaned_data


    class Meta:
        document = Application
        widgets = {
            'name': TextInput(attrs={'class': 'form-control'}),
            'tags': TextInput(attrs={'class': 'form-control'}),
            'public_name': TextInput(attrs={'class': 'form-control'}),
            'public_alias': TextInput(attrs={'class': 'form-control'}),
            'public_dir': TextInput(attrs={'class': 'form-control'}),
            'private_uri': TextInput(attrs={'class': 'form-control'}),
            'auth_timeout': TextInput(attrs={'class': 'form-control'}),
            'auth_portal': TextInput(attrs={'class': 'form-control'}),
            'sso_url': TextInput(attrs={'class': 'form-control'}),
            'app_krb_service': TextInput(attrs={'class': 'form-control'}),
            'app_disconnect_url': TextInput(attrs={'class': 'form-control'}),
            'sso_forward_basic_url': TextInput(attrs={'class': 'form-control'}),
            'sso_profile': HiddenInput(attrs={'class': 'form-control'}),
            'sso_after_post_request': TextInput(attrs={'class': 'form-control'}),
            'rules_set': SelectMultiple(attrs={'class': 'form-control'}),
            'whitelist_ips': TextInput(attrs={'class': 'form-control'}),
            'ssl_cipher': TextInput(attrs={'class': 'form-control'}),
            'datasets': SelectMultiple(attrs={'class': 'form-control'}),
            'timeout': TextInput(attrs={'class': 'form-control'}),
            'ttl': TextInput(attrs={'class': 'form-control'}),
            'sso_direct_post': CheckboxInput(attrs={'class': 'js-switch'}),
            'sso_forward_get_method': CheckboxInput(attrs={'class': 'js-switch'}),
            'pw_min_len': TextInput(attrs={'class': 'form-control'}),
            'pw_min_upper': TextInput(attrs={'class': 'form-control'}),
            'pw_min_lower': TextInput(attrs={'class': 'form-control'}),
            'pw_min_number': TextInput(attrs={'class': 'form-control'}),
            'pw_min_symbol': TextInput(attrs={'class': 'form-control'}),
            'group_registration': Select()
        }
