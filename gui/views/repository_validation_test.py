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
__author__ = "Florian Hagniel, Jérémie Jourdin"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = 'Django views dedicated to Vulture GUI status pages'

import json
import socket
from requests import Request, Session, RequestException
from base64 import b64encode

from django.http import JsonResponse

from gui.decorators import group_required
from gui.forms.repository_settings import LDAPRepositoryForm, RadiusRepositoryForm, SQLRepositoryForm, KerberosRepositoryForm, MongoDBRepositoryForm, ElasticSearchRepositoryForm, SyslogRepositoryForm
from vulture_toolkit.auth.kerberos_client import KerberosClient
from vulture_toolkit.auth.mongodb_client import MongoDBClient
from vulture_toolkit.auth.sql_client import SQLClient


@group_required('administrator', 'system_manager')
def ldap_connection_test(request):
    """

    :param request:
    :return:
    """
    from vulture_toolkit.auth.ldap_client import LDAPClient
    form = LDAPRepositoryForm(request.POST)
    if form.connection_is_valid():
        settings = form.save(commit=False)
        ldap_client = LDAPClient(settings)
        status = ldap_client.test_ldap_connection()
    else:
        status = {
            'status': False,
            'reason': "some required fields are missing",
            'form_errors': form.errors
        }

    return JsonResponse(status)


@group_required('administrator', 'system_manager')
def ldap_user_search_test(request):
    from vulture_toolkit.auth.ldap_client import LDAPClient
    # TODO SECURITY CLEAN FOR USERNAME AND PASSWORD, to prevent LDAP Injection
    username = request.POST.get('username')
    password = request.POST.get('password')
    form = LDAPRepositoryForm(request.POST)
    if form.is_valid():
        settings = form.save(commit=False)
        ldap_client = LDAPClient(settings)
        status = ldap_client.test_user_connection(username, password)
    else:
        status = {
            'status': False,
            'reason': "some required fields are missing",
            'form_errors': form.errors
        }

    return JsonResponse(status)


@group_required('administrator', 'system_manager')
def ldap_group_search_test(request):
    from vulture_toolkit.auth.ldap_client import LDAPClient
    group_name = request.POST.get('group_name')
    form = LDAPRepositoryForm(request.POST)
    if form.is_valid():
        settings = form.save(commit=False)
        ldap_client = LDAPClient(settings)
        status = ldap_client.test_group_search(group_name)
    else:
        status = {
            'status': False,
            'reason': "some required fields are missing",
            'form_errors': form.errors
        }

    return JsonResponse(status)


@group_required('administrator', 'system_manager')
def radius_user_search_test(request):
    from vulture_toolkit.auth.radius_client import RadiusClient
    username = request.POST.get('username')
    password = request.POST.get('password')
    form = RadiusRepositoryForm(request.POST)
    if form.is_valid():
        settings = form.save(commit=False)
        radius_client = RadiusClient(settings)
        status = radius_client.test_user_connection(username, password)
    else:
        status = {
            'status': False,
            'reason': "some required fields are missing",
            'form_errors': form.errors
        }

    return JsonResponse(status)


@group_required('administrator', 'system_manager')
def sql_connection_test(request):
    """

    :param request:
    :return:
    """
    """ We need to fake these data because they are not mandatory to try database connexion """
    post_data = request.POST.copy()
    post_data ['db_table']="test"
    post_data ['db_user_column']="test"
    post_data ['db_password_column']="test"
    post_data ['db_password_hash_algo']="plain"
    form = SQLRepositoryForm(post_data)
    if form.is_valid():
        settings = form.save(commit=False)
        sql_client = SQLClient(settings)
        status = sql_client.test_sql_connection()
    else:
        status = {
            'status': False,
            'reason': "some required fields are missing",
            'form_errors': form.errors
        }

    return JsonResponse(status)


@group_required('administrator', 'application_manager')
def sql_user_search_test(request):
    username = request.POST.get('username')
    password = request.POST.get('password')
    form = SQLRepositoryForm(request.POST)
    if form.is_valid():
        settings = form.save(commit=False)
        sql_client = SQLClient(settings)
        # We use raw POST values, but username is cleaned in SQLClient object
        # and password is not used in query
        status = sql_client.test_user_connection(username, password)
    else:
        status = {
            'status': False,
            'reason': "some required fields are missing",
            'form_errors': form.errors
        }

    return JsonResponse(status)


@group_required('administrator', 'system_manager')
def syslog_connection_test(request):
    """

    :param request:
    :return:
    """
    """ We need to fake these data because they are not mandatory to try database connexion """
    form = SyslogRepositoryForm(request.POST)
    if form.is_valid():
        settings = form.save(commit=False)

        try:
            host = request.POST.get('syslog_host')
            port = int(request.POST.get('syslog_port'))
            
            socket_type = socket.AF_INET
            if ":" in host:
                socket_type = socket.AF_INET6

            if request.POST.get('syslog_protocol') == 'TCP':
                s = socket.socket(socket_type, socket.SOCK_STREAM)
            else:
                s = socket.socket(socket_type, socket.SOCK_DGRAM)

            s.connect((host,port))
            s.sendall(b"Vulture test")
            s.close()
            status={'status': True}
        except Exception as e:
            status = {
                'status': False,
                'reason': "Error when connecting to server : {}".format(e),
                'form_errors': form.errors
            }
    else:
        status = {
            'status': False,
            'reason': "some required fields are missing",
            'form_errors': form.errors
        }

    return JsonResponse(status)

@group_required('administrator', 'application_manager')
def kerberos_user_search_test(request):
    username = request.POST.get('username')
    password = request.POST.get('password')
    form = KerberosRepositoryForm(request.POST)
    if form.is_valid(test=True):
        settings = form.save(commit=False)
        kerberos_client = KerberosClient(settings)
        # We use raw POST values, but username / password are cleaned in KerberosClient object
        status = kerberos_client.test_user_connection(username, password)
    else:
        status = {
            'status': False,
            'reason': "some required fields are missing",
            'form_errors': form.errors
        }

    return JsonResponse(status)


@group_required('administrator', 'system_manager')
def elasticsearch_connection_test(request):
    """

    :param request
    : return
    """
    form = ElasticSearchRepositoryForm(request.POST)
    if form.is_valid(connection_test=True):
        settings = form.save(commit=False)
        try:
            data = settings.test_connection()

            return JsonResponse({
                'status': True,
                'data': data
            })

        except RequestException as e:
            return JsonResponse({
                'status'     : False,
                'reason'     : str(e),
                'form_errors': form.errors
            })

        except ValueError as e:
            return JsonResponse({
                'status'     : False,            
                'reason'     : "Not an ElasticSearch Node. Check the port.",
                'form_errors': form.errors
            })

        except Exception as e:
            return JsonResponse({
                'status'     : False,            
                'reason'     : "An error occurred: {}".format(str(e)),
                'form_errors': form.errors
            })

    else:
        return JsonResponse({
            'status'     : False,
            'reason'     : "some required fields are missing",
            'form_errors': form.errors
        })


@group_required('administrator', 'system_manager')
def mongodb_connection_test(request):
    """

    :param request:
    :return:
    """
    form = MongoDBRepositoryForm(request.POST)
    if form.is_valid(connection_test=True):
        settings = form.save(commit=False)
        mongodb_client = MongoDBClient(settings)
        status = mongodb_client.test_mongodb_connection()
    else:
        status = {
            'status': False,
            'reason': "some required fields are missing",
            'form_errors': form.errors
        }
    return JsonResponse(status)


@group_required('administrator', 'system_manager')
def mongodb_user_search_test(request):
    # FIXME SECURITY CLEAN FOR USERNAME (Password is not passed to MongoDB)
    username = request.POST.get('username')
    password = request.POST.get('password')
    form = MongoDBRepositoryForm(request.POST)
    if form.is_valid():
        settings = form.save(commit=False)
        mongodb_client = MongoDBClient(settings)
        status = mongodb_client.test_user_connection(username, password)
    else:
        status = {
            'status': False,
            'reason': "some required fields are missing",
            'form_errors': form.errors
        }

    return JsonResponse(status)