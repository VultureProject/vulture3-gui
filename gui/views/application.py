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
__doc__ = 'Django views dedicated to application configuration'


import sys
sys.path.append("/home/vlt-gui/vulture")

# Django system imports
from django.http import HttpResponseRedirect, HttpResponseForbidden, JsonResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.crypto import get_random_string

# Django project imports
from gui.forms.application_settings import ApplicationForm
from gui.models.application_settings import Application, ContentRule, HeaderIn, HeaderOut, ListenAddress, ProxyBalancer
from gui.models.dataset_settings import SVM
from gui.models.modsec_settings import ModSecRulesSet, ModSec, ModSecSpecificRulesSet
from gui.models.modssl_settings import ModSSL
from gui.models.network_settings import Listener
from gui.models.repository_settings import LDAPRepository
from vulture_toolkit.system.http_utils import fetch_forms
from gui.decorators import group_required

# Extern modules imports
from bson.objectid import ObjectId
import re
import json
import os
import ssl
from re import search as re_search
from robobrowser.forms.fields import Checkbox

# Logger configuration imports
import logging
#logging.config.dictConfig(settings.LOG_SETTINGS)
logger = logging.getLogger('debug')


@group_required('administrator', 'application_manager', 'security_manager')
def application_list(request):
    """ Page dedicated to show application list
    """

    l_list = dict()
    new_list = {}

    #FIXME: We should display ListenAddress instead of Listeners
    """ Build the list of listeners
        Reminder:   A listener is associated to an APP and refers to a ListenAddress
                    There may have many listeners for a given ListenAddress
                    Here, the listener list is used to display the PLAY / PAUSE / RELOAD buttons
                    We build a dictionary indexed on IP:PORT
                        => We need to be carefull and display listeners that needs to be reloaded

    """
    listeners = ListenAddress.objects()
    for l in listeners:
        lst = str(l.address) + ': ' + str(l.port)
        node_name = l.get_related_node().name

        if node_name not in new_list.keys():
            new_list[node_name] = []

        """ Need to be reloaded => add it ! """
        if l.is_up2date is False:
            l_list[lst] = l
            new_list[node_name].append(l)
        else:
            if not l_list.get(lst):
                new_list[node_name].append(l)
                l_list[lst] = l

    return render_to_response('application.html', {
        'listeners'    : l_list, 
        'apps'         :Application.objects(),
        'new_listeners': new_list
    }, context_instance=RequestContext(request))

@group_required('administrator', 'application_manager', 'security_manager')
def ssotest(request):
    """ View dedicated to create a JSON structure for SSO Forward
    ;param uri: URL where the login form is
    ;param sso_vulture_agent: If set to "true", use internal Vulture user-agent instead of the one send by the user browser
    """
    if request.method == 'POST':
        try:
            uri                    = request.POST.get('uri')
            sso_vulture_agent      = request.POST.get('sso_vulture_agent')
            ssl_protocol           = request.POST.get('ssl_protocol')
            ssl_verify_certificate = request.POST.get('ssl_verify_certificate')
            ssl_client_certificate = request.POST.get('ssl_client_certificate')
            ssl_cipher             = request.POST.get('ssl_cipher')
            type                   = request.POST.get('type')
            private_uri            = request.POST.get('private_uri')
            proxy_balancer = None

            proxy_balancer_id = request.POST.get('proxy_balancer')
            if proxy_balancer_id:
                proxy_balancer = ProxyBalancer.objects.get(pk=proxy_balancer_id)

        except:
            return HttpResponseForbidden()

        headers = list()
        for h in request.POST:
            m = re.match('headers\[([0-9]+)\]\[(.*)\]', h)
            if m is not None:
                name = m.group(2)
                value = request.POST[h]
                headers.append(HeaderIn(name=name, value=value, action="set"))

    else:
        return HttpResponseForbidden()

    ssl_context = None
    if ssl_protocol not in ('', 'None', None):
        ssl_context = ssl.SSLContext(int(ssl_protocol))
        if ssl_verify_certificate == 'on':
            ssl_context.verify_mode = ssl.CERT_REQUIRED
        else:
            ssl_context.verify_mode = ssl.CERT_NONE

        if ssl_cipher:
            ssl_context.set_ciphers(ssl_cipher)

    if not ssl_client_certificate:
        ssl_client_certificate = None

    """ Transform uri as list - to test multiple uris in case of balanced app """
    uris = []
    if type != "balanced":
        if "[]" in uri:
            uri = uri.replace("[]", private_uri).replace("\[", '[').replace("\]", ']')
        else:
            uri = uri.replace("\[", '[').replace("\]", ']')
        uris.append(uri)
    else:
        if "[]" not in uri:
            uris.append(uri.replace("\[", '[').replace("\]", ']'))
        else:
            for proxybalancer_member in proxy_balancer.members:
                # Concatenate scheme and uri, and remove public dir but keep port
                backend_uri = "{}://{}".format(proxybalancer_member.uri_type, proxybalancer_member.uri.split('/')[0])
                uri_tmp = uri.replace('[]', backend_uri)
                uri_tmp = uri_tmp.replace('\[', "[").replace('\]', ']')
                uris.append(uri_tmp)

    forms, final_uri, response, response_body = fetch_forms(logger, uris, request, sso_vulture_agent,
                                                            ssl_context=ssl_context, headers_in=headers,
                                                            proxy_client_side_certificate=ssl_client_certificate)
    if not forms:
        logger.error("SSOTEST::No form could be retrieved.")

    try:
        form_list = list()
        i = 0

        # Retrieve attributes from robobrowser.Form objects
        for f in forms:
            if str(f.method).upper() == "POST":
                control_list = list()
                for field_name, field in f.fields.items():
                    if isinstance(field._parsed, list):
                        tag = field._parsed[0]
                    else:
                        tag = field._parsed
                    # field is a robobrowser.forms.fields.Input object
                    # field._parsed is a bs4.element.Tag object
                    control_list.append({'name': tag.attrs.get('name', ""), 'id': tag.attrs.get('id', ""),
                                         'type': tag.attrs.get('type'), 'value': tag.attrs.get('value', "")})
                form_list.append({'name': f.parsed.get('name', ""), 'id': i, 'controls': control_list})
                i += 1
        response = {'status': 'ok', 'forms': json.dumps(form_list)}
    except TypeError as error:
        logger.exception(error)
        response = {'error': "No form detected in uri(s) {}".format(uris)}
    except Exception as error:
        logger.exception(error)
        response = {'error': str(error)}

    return JsonResponse(response)

@group_required('administrator', 'application_manager', 'security_manager')
def clone(request, object_id=None):

    """ View dedicated to application cloning
    :param object_id: MongoDB object_id of application
    :param request: Django request object
    """
    # Retrieve application configuration
    application = Application.objects.with_id(ObjectId(object_id))
    incoming_headers = application.headers_in
    outgoing_headers = application.headers_out
    content_rules    = application.content_rules
    listeners        = application.listeners

    # Clone incoming headers
    incoming_headers_list = list()
    for h in incoming_headers:
        h.pk = None
        h.save()
        incoming_headers_list.append(h)

    # Clone outgoing headers
    outgoing_headers_list = list()
    for h in outgoing_headers:
        h.pk = None
        h.save()
        outgoing_headers_list.append(h)

    # Clone content rules
    content_rules_list=list()
    for r in content_rules:
        r.pk=None
        r.save()
        content_rules_list.append(r)

    # Clone listeners
    listeners_list=list()
    for l in listeners:
        l.pk=None
        l.is_up2date=False
        l.save()
        listeners_list.append(l)

    #Clone application
    application.pk = None
    application.name = 'Copy Of ' + str(application.name) + '#' + get_random_string(4)
    application.headers_in = incoming_headers_list
    application.headers_out = outgoing_headers_list
    application.content_rules = content_rules_list
    application.listeners = listeners_list

    modsec_wl_bl = ModSecRulesSet(name="{} whitelist/blacklist".format(application.name), type_rule="wlbl")
    modsec_wl_bl.save()
    modsec_wl_bl.conf = modsec_wl_bl.get_conf()
    modsec_wl_bl.save()

    application.wl_bl_rules = modsec_wl_bl


    application.save()

    return HttpResponseRedirect('/application/')


@group_required('administrator', 'application_manager', 'security_manager')
def edit(request, object_id=None):

    """ View dedicated to application management

    :param object_id: MongoDB object_id of application
    :param request: Django request object
    """
    # Retrieving application configuration
    application = Application.objects.with_id(ObjectId(object_id))

    specific_rules_set = []
    incoming_headers   = []
    outgoing_headers   = []
    content_rules      = []
    listeners          = []
    listeners_ips      = []
    svms               = []
    activated_svms     = []

    # Application doesn"'t exist ==> We want to create a new one
    # Fix some default values
    if not application and request.method != 'POST':
        application = Application(name="My App", type="http", public_name="www.example.com", public_alias="www.ex_1.fr", public_dir="/", private_uri="https://192.168.1.1/owa/")
        # Fix default security rules
        incoming_headers.append(HeaderOut(True, 'unset', '^X-Forwarded-', '', '', 'always', ''))
        # outgoing_headers.append(HeaderOut ('set', 'Content-Security-Policy', 'default-src \'self\'', '', 'always', ''))
        outgoing_headers.append(HeaderOut(True, 'set', 'X-Frame-Options', 'SAMEORIGIN', '', 'always', ''))
        outgoing_headers.append(HeaderOut(True, 'set', 'X-Content-Type-Options', 'nosniff', '', 'always', ''))
        outgoing_headers.append(HeaderOut(True, 'set', 'X-XSS-Protection', '1; mode=block', '', 'always', ''))
        application.headers_in = incoming_headers
        application.headers_out = outgoing_headers

    # Check if request are valid - and populate arrays with form values
    if request.method == 'POST':
        dataPosted = request.POST
        dataPostedRaw = str(request.body).split("&")

        has_listener = False
        dataPosted_length = len(dataPostedRaw)

        if application and not "enabled=on" in dataPostedRaw:
            application.delete_listeners()

        for data in dataPostedRaw:
            if data.startswith("address_"):
                # Listener management
                for cpt in range(dataPosted_length):
                    if data.startswith("address_"+str(cpt) + "="):

                        inet = None
                        port = None
                        redirect_port = None

                        try:
                            listener_id = dataPosted['address_' + str(cpt)]
                            inet = Listener.objects.with_id(ObjectId(listener_id))
                        except Exception as e:
                            pass

                        try:
                            port = dataPosted['port_' + str(cpt)]
                        except Exception as e:
                            pass

                        try:
                            redirect_port = dataPosted['redirect_port_' + str(cpt)]
                        except Exception as e:
                            pass

                        try:
                            ssl_profile = ModSSL.objects.with_id(ObjectId(dataPosted['ssl_profile_' + str(cpt)]))
                        except Exception as e:
                            ssl_profile = None
                            pass

                        if (inet and port):

                            address = ListenAddress(address=inet, port=port, ssl_profile=ssl_profile, redirect_port=redirect_port)
                            """ Add '1' because we don't want to save yet the listener """
                            address.related_node = address.get_related_node(1)
                            listeners.append(address)
                            listeners_ips.append((address.related_node, inet.ip, port))
                            has_listener = True

                        dataPosted_length -= 4


            if data.startswith("SpecificRS_url_"):
                for cpt in range(dataPosted_length):
                    if data.startswith("SpecificRS_url_"+str(cpt) + "="):

                        # Force default values to prevent injection or any problem
                        specific_rs_url = dataPosted.get('SpecificRS_url_' + str(cpt), '/login/')
                        try:
                            specific_rs_rs = ModSecRulesSet.objects.with_id(ObjectId(dataPosted.get('modsec_specific_rs_select' + str(cpt), None)))
                        except:
                            specific_rs_rs  = ModSecRulesSet.objects.first()

                        specific_rs = ModSecSpecificRulesSet(url=specific_rs_url, rs=specific_rs_rs)
                        specific_rules_set.append(specific_rs)

                        cpt -= 2

            # Incoming header management
            if data.startswith("header_action_"):
                for cpt in range(dataPosted_length):
                    if data.startswith("header_action_"+str(cpt) + "="):

                        # Force harmless default values to prevent any injection or jQuery problem
                        header_enable       = (dataPosted.get('header_enable_'+str(cpt), 'off') == 'on')
                        header_action       = dataPosted.get('header_action_' + str(cpt), 'add')
                        header_name         = dataPosted.get('header_name_' + str(cpt), 'Vulture')
                        header_value        = dataPosted.get('header_value_' + str(cpt), '')
                        header_replacement  = dataPosted.get('header_replacement_' + str(cpt), '')
                        header_condition    = dataPosted.get('header_condition_' + str(cpt), 'always')
                        header_condition_v  = dataPosted.get('header_condition_v_' + str(cpt), '')

                        # FIXME: Coherence control
                        header = HeaderIn(header_enable, header_action, header_name, header_value, header_replacement, header_condition, header_condition_v)
                        incoming_headers.append(header)

                        dataPosted_length -= 7

            # Outgoing header management
            if data.startswith("header_out_action_"):
                for cpt in range(dataPosted_length):
                    if data.startswith("header_out_action_" + str(cpt) + "="):

                        # Force harmless default values to prevent any injection or jQuery problem
                        header_enable       = (dataPosted.get('header_out_enable_'+str(cpt), 'off') == 'on')
                        header_action       = dataPosted.get('header_out_action_' + str(cpt), 'add')
                        header_name         = dataPosted.get('header_out_name_' + str(cpt), 'Vulture')
                        header_value        = dataPosted.get('header_out_value_' + str(cpt), '')
                        header_replacement  = dataPosted.get('header_out_replacement_' + str(cpt), '')
                        header_condition    = dataPosted.get('header_out_condition_' + str(cpt), 'always')
                        header_condition_v  = dataPosted.get('header_out_condition_v_' + str(cpt), '')

                        # FIXME: Coherence control
                        header = HeaderOut(header_enable, header_action, header_name, header_value, header_replacement, header_condition, header_condition_v)
                        outgoing_headers.append(header)

                        dataPosted_length -= 7

            # # Content rules management
            if data.startswith("content_types_"):
                for cpt in range(dataPosted_length):
                    if data.startswith("content_types_" + str(cpt) + "="):

                        # Force harmless default values to prevent any injection
                        # or jQuery problem
                        content_enable            = True if dataPosted.get('content_enable_'+str(cpt),    'off') == 'on' else False
                        content_types             = dataPosted.get('content_types_'+str(cpt),             'text/html')
                        content_condition         = dataPosted.get('condition_'+str(cpt),                 '')
                        content_deflate           = True if dataPosted.get('content_deflate_'+str(cpt),   'off') == 'on' else False
                        content_inflate           = True if dataPosted.get('content_inflate_'+str(cpt),   'off') == 'on' else False
                        content_pattern           = dataPosted.get('content_pattern_'+str(cpt),           '')
                        content_replacement       = dataPosted.get('content_replacement_'+str(cpt),       '')
                        content_replacement_flags = dataPosted.get('content_replacement_flags_'+str(cpt), '')

                        # FIXME: Coherence control
                        rule = ContentRule(content_enable, content_types, content_condition,
                                           content_deflate, content_inflate,
                                           content_pattern, content_replacement,
                                           content_replacement_flags)
                        content_rules.append(rule)

                        dataPosted_length -= 8


            # SVMs management
            if data.startswith("checkbox_chart_uri_analysis_"):
                m = re.match('checkbox_chart_uri_analysis_([0-9|a-f]+)', data)
                if m:
                    dataset_id_ = m.group(1)

                    # Force harmless default values to prevent any injection or jQuery problem
                    svm_enable = False
                    try:
                        svm_enable = True if dataPosted.get('checkbox_chart_uri_analysis_' + dataset_id_) == 'on' else False
                        if svm_enable:
                            svm = SVM.objects(dataset_used=dataset_id_, algo_used="Levenstein")[0]
                            activated_svms.append(str(svm.id))
                            logger.debug("Activated SVM with id '{}' for application saved".format(str(svm.id)))
                    except KeyError:
                        pass
                    except Exception as e:
                        logger.error("Unable to retrieve activated SVM - Dataset_id:{}, algo_used:Levenstein - Exception: {}".format(dataset_id_, str(e)))


            if data.startswith("checkbox_chart_uri_analysis_2_"):
                m = re.match('checkbox_chart_uri_analysis_2_([0-9|a-f]+)', data)
                if m:
                    dataset_id_ = m.group(1)

                    # Force harmless default values to prevent any injection or jQuery problem
                    svm_enable = False
                    try:
                        svm_enable = True if dataPosted.get('checkbox_chart_uri_analysis_2_' + dataset_id_) == 'on' else False
                        if svm_enable:
                            svm = SVM.objects(dataset_used=dataset_id_, algo_used="Levenstein2")[0]
                            activated_svms.append(str(svm.id))
                            logger.debug("Activated SVM with id '{}' for application saved".format(str(svm.id)))
                    except KeyError:
                        pass
                    except Exception as e:
                        logger.error("Unable to retrieve activated SVM - Dataset_id:{}, algo_used:Levenstein2 - Exception: {}".format(dataset_id_, str(e)))

            if data.startswith("checkbox_chart_bytes_received_"):
                m = re.match('checkbox_chart_bytes_received_([0-9|a-f]+)', data)
                if m:
                    dataset_id_ = m.group(1)

                    # Force harmless default values to prevent any injection or jQuery problem
                    svm_enable = False
                    try:
                        svm_enable = True if dataPosted.get('checkbox_chart_bytes_received_' + dataset_id_) == 'on' else False
                        if svm_enable:
                            svm = SVM.objects(dataset_used=dataset_id_, algo_used="HTTPcode_bytes_received")[0]
                            activated_svms.append(str(svm.id))
                            logger.debug("Activated SVM with id '{}' for application saved".format(str(svm.id)))
                    except KeyError:
                        pass
                    except Exception as e:
                        logger.error("Unable to retrieve activated SVM - Dataset_id:{}, algo_used:HTTPcode_bytes_received - Exception: {}".format(dataset_id_, str(e)))

            if data.startswith("checkbox_chart_ratio_"):
                m = re.match('checkbox_chart_ratio_([0-9|a-f]+)', data)
                if m:
                    dataset_id_ = m.group(1)

                    # Force harmless default values to prevent any injection or jQuery problem
                    svm_enable = False
                    try:
                        svm_enable = True if dataPosted.get('checkbox_chart_ratio_' + dataset_id_) == 'on' else False
                        if svm_enable:
                            svm = SVM.objects(dataset_used=dataset_id_, algo_used="Ratio")[0]
                            activated_svms.append(str(svm.id))
                            logger.debug("Activated SVM with id '{}' for application saved".format(str(svm.id)))
                    except KeyError:
                        pass
                    except Exception as e:
                        logger.error("Unable to retrieve activated SVM - Dataset_id:{}, algo_used:Ratio - Exception: {}".format(dataset_id_, str(e)))

        form = ApplicationForm(request.POST, instance=application, listeners=listeners)
    else:

        if not object_id:
            try:
                rulesset_vulture = [ModSecRulesSet.objects.get(name="Vulture RS").id]
            except ModSecRulesSet.DoesNotExist:
                rulesset_vulture = []

            form = ApplicationForm(initial={"rules_set": rulesset_vulture, "modsec_policy": ModSec.objects.get(name="Default Policy")}, instance=application)
        else:
            form = ApplicationForm(initial={'rules_set': [x.id for x in application.rules_set]}, instance=application)

        incoming_headers   = application.headers_in
        outgoing_headers   = application.headers_out
        content_rules      = application.content_rules

        specific_rules_set = list()
        for i in application.specific_rules_set:
            specific_rules_set.append(ModSecSpecificRulesSet(url=re.sub('^' + application.public_dir, '', i.url), rs=i.rs))

        # We replace '\' by '\\' in strings because they're interpreted by templates
        for tmp_rule in content_rules:
            tmp_rule.pattern = tmp_rule.pattern.replace("\\", "\\\\")
            tmp_rule.replacement = tmp_rule.replacement.replace("\\", "\\\\")

        listeners = application.listeners

        svms = [SVM.objects(id=ObjectId(svm_id)).no_dereference().only('dataset_used', 'algo_used', 'id').first() for svm_id in
                application.activated_svms]


    # Saving information into database and redirect to application list
    if request.method == 'POST' and form.is_valid():

        # Listener is mandatory
        if has_listener:
            old_app = Application.objects.with_id(ObjectId(object_id))

            # 1) Remove old listeners, headers and content rules
            if old_app and old_app.listeners:
                for listener in old_app.listeners:
                    ip=listener.address.ip
                    port=listener.port
                    n=listener.related_node

                    """ Stop the listener if there is only this app running on it """
                    if (n,ip,port) not in listeners_ips :
                        logger.info ("Stopping listener {}:{}".format (ip, port))
                        listener.stop()

                    listener.delete()



            if old_app and old_app.headers_in:
                for header in old_app.headers_in:
                    header.delete()

            if old_app and old_app.headers_out:
                for header in old_app.headers_out:
                    header.delete()

            if old_app and old_app.content_rules:
                for rule in old_app.content_rules:
                    rule.delete()

            if old_app and old_app.specific_rules_set:
                for ruleset in old_app.specific_rules_set:
                    ruleset.delete()

            old_cookie_encryption = False
            old_cookie_cipher = None
            if old_app:
                application.wl_bl_rules = old_app.wl_bl_rules

                old_cookie_encryption = old_app.cookie_encryption
                old_cookie_cipher = old_app.cookie_cipher
                old_cookie_cipher_key = old_app.cookie_cipher_key
                old_cookie_cipher_iv = old_app.cookie_cipher_iv

            # 2) Create new listeners, headers and content rules
            for listener in listeners:
                listener.save()
            for header in incoming_headers:
                header.save()
            for header in outgoing_headers:
                header.save()
            for rule in content_rules:
                rule.save()

            # 3) Assign listeners, headers and content rules
            auth_backend = form.cleaned_data.get('auth_backend')
            auth_backend_fallbacks = form.cleaned_data.get('auth_backend_fallbacks')
            application = form.save(commit=False)

            if auth_backend:
                application.auth_backend = auth_backend
            else:
                application.auth_backend = None
            if auth_backend_fallbacks:
                application.auth_backend_fallbacks = auth_backend_fallbacks
            else:
                application.auth_backend_fallbacks = None

            application.listeners = listeners
            application.headers_in = incoming_headers
            application.headers_out = outgoing_headers
            application.specific_rules_set = specific_rules_set
            application.content_rules = content_rules
            application.activated_svms = activated_svms

            if application.cookie_encryption:
                if not old_cookie_encryption or not old_cookie_cipher or application.cookie_cipher != old_cookie_cipher:
                    application.cookie_cipher_key = get_random_string(32) if application.cookie_cipher == 'aes256' else get_random_string(16)
                    application.cookie_cipher_iv = get_random_string(32) if application.cookie_cipher == 'aes256' else get_random_string(16)

                else:
                    application.cookie_cipher_key = old_cookie_cipher_key
                    application.cookie_cipher_iv = old_cookie_cipher_iv

            # 4) Save application
            if not application.public_dir.endswith('/'):
                application.public_dir += '/'
            if application.auth_portal and not application.auth_portal.endswith('/'):
                application.auth_portal += '/'
            if application.private_uri and not application.private_uri.endswith('/'):
                application.private_uri += '/'

            for ruleset in specific_rules_set:
                ruleset.url = os.path.normpath(str(application.public_dir) + '/' + str(ruleset.url))
                ruleset.save()

            if not object_id:
                # Create BlackList/WhiteList ModSecRuleSet
                modsec_wl_bl = ModSecRulesSet(name="{} whitelist/blacklist".format(application.name), type_rule="wlbl")
                modsec_wl_bl.save()
                modsec_wl_bl.conf = modsec_wl_bl.get_conf()
                modsec_wl_bl.save()

                application.wl_bl_rules = modsec_wl_bl

            else:
                # If the application is modified, modify the name of the RS references
                application.wl_bl_rules.name = "{} whitelist/blacklist".format(form.cleaned_data.get('name'))
                application.wl_bl_rules.save()
                for modsec_ruleset in ModSecRulesSet.objects.filter(name="Learning {} WL"):
                    modsec_ruleset.name = form.cleaned_data.get('name')
                    modsec_ruleset.save()

            if application.type == "balanced":
                application.private_uri = "{}://{}".format(application.proxy_balancer.members[0].uri_type, application.proxy_balancer.members[0].uri)

            if application.sso_enabled:
                if application.sso_forward == "basic":
                    application.sso_profile = json.dumps([{'type': "learn", 'name': "basic_username;vlt;", 'asked_name': "username"},
                                {'type': "learn_secret", 'name': "basic_password;vlt;", 'asked_name': "password"}])
                elif application.sso_forward == "kerberos":
                    application.sso_profile = json.dumps([{'type': "learn", 'name': "kerberos_username;vlt;", 'asked_name': "username"},
                                {'type': "learn_secret", 'name': "kerberos_password;vlt;", 'asked_name': "password"}])

            # Check if api_call to reload rsyslogd is needed
            if old_app:
                if application.log_custom != old_app.log_custom or application.log_level != old_app.log_level or application.learning != old_app.learning:
                    application.save()
                else:
                    application.save(no_apicall=True)
            else:
                application.save()

            return HttpResponseRedirect('/application/')


    inets = Listener.objects()
    address_list = list()
    vhid_list = list()
    # List and categorize inet (carp or not) to render them in template
    for inet in inets:
        listener = dict()
        if inet.is_carp:
            listener['inet'] = inet
            listener['id'] = getattr(inet, 'id')
            vhid_list.append(inet.carp_vhid)

        elif inet.carp_vhid in vhid_list:
            continue

        else:
            listener['inet'] = inet
            listener['id'] = getattr(inet, 'id')

        address_list.append(listener)

    ssl_profile_list = ModSSL.objects()

    rules_set_list = ModSecRulesSet.objects.filter(type_rule__in=['crs', 'trustwave', 'vulture', 'custom'])

    return render_to_response('application_edit.html',
                              {'form': form, 'object_id': object_id,
                               'headers_in': incoming_headers, 'headers_out': outgoing_headers,
                               'content_rules': content_rules, 'listeners': listeners, 'address_list': address_list,
                               'ssl_profile_list': ssl_profile_list, 'application': application, 'svms': svms,
                               'rules_set_list': rules_set_list, 'specific_rules_set': specific_rules_set},
                              context_instance=RequestContext(request))


@group_required('administrator', 'security_manager')
def fetch_ldap_groups(request, object_id=None):
    if object_id:
        try:
            backend  = LDAPRepository.objects.with_id(object_id).get_backend()
            retg     = backend.enumerate_groups()
            logger.info(retg)
            group_dn = retg.pop(0)
            base_dn  = retg.pop(0)
            return JsonResponse({'status':True, 'group_dn':group_dn, 'base_dn':base_dn, 'list_group':retg})
        except:
            pass
    return JsonResponse({'status':False})
