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
__doc__ = 'Django views dedicated to Vulture GUI Repository page'

import base64

from gui.forms.repository_settings import (ElasticSearchRepositoryForm, KerberosRepositoryForm, LDAPRepositoryForm,
                                           MongoDBRepositoryForm, OTPRepositoryForm, SQLRepositoryForm,
                                           RadiusRepositoryForm, SyslogRepositoryForm)
from gui.models.repository_settings import (ElasticSearchRepository, KerberosRepository, LDAPRepository,
                                            MongoDBRepository, OTPRepository, SQLRepository, RadiusRepository,
                                            SyslogRepository)
from gui.views.generic_list_views import RepositoryListView
from gui.views.generic_views import RepositoryEditView


class SQLRepositoryListView(RepositoryListView):
    def __init__(self):
        self.queryset = SQLRepository.objects.all()

    def get_context_data(self, **kwargs):
        context = super(SQLRepositoryListView, self).get_context_data(**kwargs)
        self.queryset = SQLRepository.objects.all()
        context['repository_name'] = 'SQL'
        context['global'] = False
        return context


class SyslogRepositoryEditView(RepositoryEditView):
    template_name = "repository_syslog.html"
    form = SyslogRepositoryForm
    obj = SyslogRepository
    redirect_url = '/repository/syslog/'

class SyslogRepositoryListView(RepositoryListView):
    def __init__(self):
        self.queryset = SyslogRepository.objects.all()

    def get_context_data(self, **kwargs):
        context = super(SyslogRepositoryListView, self).get_context_data(**kwargs)
        self.queryset = SyslogRepository.objects.all()
        context['repository_name'] = 'Syslog'
        context['global'] = False
        return context


class SQLRepositoryEditView(RepositoryEditView):
    template_name = "repository_sql.html"
    form = SQLRepositoryForm
    obj = SQLRepository
    redirect_url = '/repository/sql/'

class KerberosRepositoryListView(RepositoryListView):
    def __init__(self):
        self.queryset = KerberosRepository.objects.all()

    def get_context_data(self, **kwargs):
        context = super(KerberosRepositoryListView, self).get_context_data(**kwargs)
        self.queryset = KerberosRepository.objects.all()
        context['repository_name'] = 'Kerberos'
        context['global'] = False
        return context

class KerberosRepositoryEditView(RepositoryEditView):
    template_name = "repository_kerberos.html"
    form = KerberosRepositoryForm
    obj = KerberosRepository
    redirect_url = '/repository/kerberos/'

    def post(self, request, object_id):
        keytab = ''
        try:
            keytab = base64.b64encode(request.FILES['keytab2'].read())
        except Exception as e:
            pass
        # Set 'keytab' field of request.POST to create the field in the form
        request.POST.appendlist('keytab', keytab)
        return super(KerberosRepositoryEditView, self).post(request, object_id)


class LDAPRepositoryListView(RepositoryListView):
    def __init__(self):
        self.queryset = LDAPRepository.objects.all()

    def get_context_data(self, **kwargs):
        context = super(LDAPRepositoryListView, self).get_context_data(**kwargs)
        self.queryset = LDAPRepository.objects.all()
        context['repository_name'] = 'LDAP/AD'
        context['global'] = False
        return context


class LDAPRepositoryEditView(RepositoryEditView):
    template_name = "repository_ldap.html"
    form = LDAPRepositoryForm
    obj = LDAPRepository
    redirect_url = '/repository/ldap/'


class RadiusRepositoryListView(RepositoryListView):
    def __init__(self):
        self.queryset = RadiusRepository.objects.all()

    def get_context_data(self, **kwargs):
        context = super(RadiusRepositoryListView, self).get_context_data(**kwargs)
        self.queryset = RadiusRepository.objects.all()
        context['repository_name'] = 'RADIUS'
        context['global'] = False
        return context


class RadiusRepositoryEditView(RepositoryEditView):
    template_name = "repository_radius.html"
    form = RadiusRepositoryForm
    obj = RadiusRepository
    redirect_url = '/repository/radius/'


class MongoDBRepositoryListView(RepositoryListView):
    def __init__(self):
        self.queryset = MongoDBRepository.objects.all()

    def get_context_data(self, **kwargs):
        context = super(MongoDBRepositoryListView, self).get_context_data(**kwargs)
        self.queryset = MongoDBRepository.objects.all()
        context['repository_name'] = 'MongoDB'
        context['global'] = False
        return context


class MongoDBRepositoryEditView(RepositoryEditView):
    template_name = "repository_mongodb.html"
    form = MongoDBRepositoryForm
    obj = MongoDBRepository
    redirect_url = '/repository/mongodb/'


class ElasticSearchRepositoryListView(RepositoryListView):
    def __init__(self):
        self.queryset = ElasticSearchRepository.objects.all()

    def get_context_data(self, **kwargs):
        context = super(ElasticSearchRepositoryListView, self).get_context_data(**kwargs)
        self.queryset = ElasticSearchRepository.objects.all()
        context['repository_name'] = 'ElasticSearch'
        context['global'] = False
        return context


class ElasticSearchRepositoryEditView(RepositoryEditView):
    template_name = "repository_elasticsearch.html"
    form = ElasticSearchRepositoryForm
    obj = ElasticSearchRepository
    redirect_url = '/repository/elasticsearch/'


class OTPRepositoryListView(RepositoryListView):
    def __init__(self):
        self.queryset = OTPRepository.objects.all()

    def get_context_data(self, **kwargs):
        context = super(OTPRepositoryListView, self).get_context_data(**kwargs)
        context['repository_name'] = 'OTP'
        context['global'] = False
        return context


class OTPRepositoryEditView(RepositoryEditView):
    template_name = "repository_otp.html"
    form = OTPRepositoryForm
    obj = OTPRepository
    redirect_url = "/repository/otp/"