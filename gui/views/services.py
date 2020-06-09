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
__author__ = "Florian Hagniel, Kevin Guillemot"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = 'Django views dedicated to Vulture GUI home page'


# Django system imports
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render_to_response
from django.template import RequestContext

# Django project imports
from gui.decorators import group_required
from gui.forms.system_settings import (DNSSettingsForm, GLOBALSettingsForm, IPSECSettingsForm, LogAnalyserSettingsForm,
                                       NTPSettingsForm, PFSettingsForm, SSHSettingsForm, SMTPSettingsForm)
from gui.models.network_settings import Interface
from gui.models.repository_settings import MongoDBRepository
from gui.models.system_settings import Cluster, Node, PfRules, LogAnalyserRules
from gui.signals.gui_signals import config_modified
from gui.forms.forms_utils import bootstrap_tooltips, DivErrorList

# Required exceptions imports
from bson.errors import InvalidId

# Extern modules imports
from bson.objectid import ObjectId
from email.mime.text import MIMEText
import ipaddress
import json
import maxminddb
import smtplib
from time import sleep

# Logger configuration imports
import logging
logger = logging.getLogger('services_events')


@group_required('administrator', 'system_manager')
def ntp_view(request, object_id=None):
    """ """
    # Retrieving cluster configuration
    cluster = Cluster.objects.get()
    ntp_status = {}

    # Object_id is defined => we are configuring a Node
    if object_id is not None:
        try:
            node = Node.objects.with_id(ObjectId(object_id))
            if not node:
                raise InvalidId()
        except InvalidId:
            return HttpResponseForbidden("Injection detected.")
        system_settings = node.system_settings
        status = node.api_request("/api/services/ntp/status/")
        if isinstance(status, bool) and not status:
            # API Request returned False
            ntp_status[node.name] = ("ERROR", "Error on node {}.".format(node.name))
    # We are configuring Cluster
    else:
        system_settings = cluster.system_settings
        cluster_api_status = cluster.api_request("/api/services/ntp/status/")
        for node in cluster.members:
            # If node is down, result = False
            node_res = (cluster_api_status.get(node.name, {}) or {}).get('result', False)
            if isinstance(node_res, bool) and not node_res:
                ntp_status[node.name] = ("ERROR", "Cannot contact node")
            else:
                ntp_status[node.name] = node_res

    # Instantiate form
    form = NTPSettingsForm(request.POST or None,
                           instance=system_settings.ntp_settings)

    # form validation
    if request.method == 'POST' and form.is_valid():
        ntp_conf = form.save(commit=False)
        system_settings.ntp_settings = ntp_conf
        # We are configuring Node
        if object_id:
            # Node will use Cluster settings
            if ntp_conf.cluster_based_conf:
                node.system_settings.ntp_settings = None
            node.save()
        else:
            cluster.save()

    return render_to_response('ntp.html',
                              {'form': form, 'ntp_status': ntp_status,
                               'cluster': cluster, 'object_id': object_id},
                              context_instance=RequestContext(request))


@group_required('administrator', 'system_manager')
def restart_ntp(request, object_id=None):
    """ View dedicated to restart NTP service, it sends restart request to
    selected node or to all cluster's node

    :param request: Django request object
    """
    # Object_id is provided, restart NTP service only on related Node
    if object_id:
        node = Node.objects.with_id(ObjectId(object_id))
        response = node.api_request("/api/services/ntp/restart/")
    # Restart NTP service on all nodes
    else:
        cluster = Cluster.objects.get()
        response = cluster.api_request("/api/services/ntp/restart/")
    return JsonResponse(response)


@group_required('administrator', 'system_manager')
def dns_view(request, object_id=None):
    """ """

    # Retrieving cluster configuration
    cluster = Cluster.objects.get()
    # Object_id is defined => we are configuring a Node
    if object_id:
        try:
            node = Node.objects.with_id(ObjectId(object_id))
            if not node:
                raise InvalidId()
        except InvalidId:
            return HttpResponseForbidden("Injection detected")
        system_settings = node.system_settings
    # We are configuring Cluster
    else:
        system_settings = cluster.system_settings

    # Instantiate form
    form = DNSSettingsForm(request.POST or None, instance=system_settings.dns_settings,
                           error_class=DivErrorList)

    popup = ""
    api_url_dns = "/api/services/dns"
    # form validation
    if request.method == 'POST' and form.is_valid():
        dns_conf = form.save(commit=False)
        system_settings.dns_settings = dns_conf
        # We are configuring Node
        if object_id:
            # Node will use Cluster settings
            if dns_conf.cluster_based_conf:
                node.system_settings.dns_settings = None
            node.save()
            #
            restart_res = node.api_request("{}/restart/".format(api_url_dns))
            if not isinstance(restart_res, bool):
                try:
                    popup = restart_res['result']
                except:
                    popup = ['ERROR', "Cannot retrieve service results"]
            elif not restart_res:
                popup = ["ERROR", "Cannot contact node".format(node.name)]
            else:
                popup = ["UP", "Configuration applied"]
        else:
            cluster.save()
            restart_cluster_res = cluster.api_request("/api/services/dns/restart/")
            for node in cluster.members:
                restart_res = restart_cluster_res.get(node.name)
                if not isinstance(restart_res, bool):
                    try:
                        popup = restart_res.get('result')
                    except:
                        popup = ['ERROR', "Cannot retrieve service results"]
                        break
                elif not restart_res:
                    popup = ["ERROR", "Cannot contact node ".format(node.name)]
                    break
                else:
                    popup = ["UP", "Configuration applied"]

    return render_to_response('dns.html',
                              {'form': form, 'cluster': cluster, 'popup': popup,
                               'object_id': object_id},
                              context_instance=RequestContext(request))


@group_required('administrator', 'system_manager')
def global_view(request):
    """

    :param request:
    :return:
    """
    cluster = Cluster.objects.get()
    reload_apps = False # Reload the applications when a field is modified

    # Instantiate form
    global_settings = cluster.system_settings.global_settings

    form = GLOBALSettingsForm(request.POST or None, instance=global_settings, error_class=DivErrorList)

    # A quoi ça sert CA ?!
    for repo in MongoDBRepository.objects.all():
        if repo.is_internal:
            break

    # form validation
    if request.method == 'POST':
        old_portal_cookie = global_settings.portal_cookie
        old_app_cookie = global_settings.app_cookie
        old_public_token = global_settings.public_token
        if form.is_valid():
            global_conf = form.save(commit=False)
            global_conf['logs_repository'] = form.cleaned_data.get('logs_repository')
            global_conf['vulture_status_ip_allowed'] = request.POST.get('vulture_status_ip_allowed').split(',')
            reload_apps = (old_portal_cookie != global_conf.portal_cookie) or (
                old_app_cookie != global_conf.app_cookie) or (
                old_public_token != global_conf.public_token)
            cluster.system_settings.global_settings = global_conf
            cluster.save()

    if reload_apps:
        config_modified.send(sender=Cluster, id=None)

    return render_to_response('global.html', {
            'form'         : form,
            'apache_status': ",".join(global_settings.vulture_status_ip_allowed),
            'repo_interne' : str(repo.id),
            'reload_apps'  : reload_apps
        }, context_instance=RequestContext(request))


@group_required('administrator', 'system_manager')
def smtp_view(request, object_id=None):
    """

    :param request:
    :return:
    """
    # Retrieving cluster configuration
    cluster = Cluster.objects.get()
    # Object_id is defined => we are configuring a Node
    if object_id is not None:
        try:
            node = Node.objects.with_id(ObjectId(object_id))
            if not node:
                raise InvalidId()
        except InvalidId:
            return HttpResponseForbidden("Injection detected.")
        system_settings = node.system_settings
    # We are configuring Cluster
    else:
        system_settings = cluster.system_settings

    # Instantiate form
    form = SMTPSettingsForm(request.POST or None,
                            instance=system_settings.smtp_settings)

    def perform_api_res(res, node_name):
        if isinstance(res, bool) and not res:
            return "ERROR", "Error on node {}.".format(node_name)
        return res.get('result')

    # form validation
    popup = ""
    if request.method == 'POST' and form.is_valid():
        smtp_conf = form.save(commit=False)
        system_settings.smtp_settings = smtp_conf
        # We are configuring Node
        if object_id:
            # Node will use Cluster settings
            if smtp_conf.cluster_based_conf:
                node.system_settings.smtp_settings = None
            node.save()
            node_api_res = node.api_request("/api/services/smtp/restart/")
            popup = perform_api_res(node_api_res, node.name)
        else:
            cluster.save()
            cluster_api_res = cluster.api_request("/api/services/smtp/restart/")
            for node in cluster.members:
                popup = perform_api_res(cluster_api_res.get(node.name), node.name)
                if popup[0] == "ERROR":
                    break

    smtp_status = {}
    if object_id:
        node_api_res = node.api_request("/api/services/smtp/status/")
        smtp_status[node.name] = perform_api_res(node_api_res, node.name)
    else:
        cluster.save()
        cluster_api_res = cluster.api_request("/api/services/smtp/status/")
        for node in cluster.members:
            smtp_status[node.name] = perform_api_res(cluster_api_res.get(node.name), node.name)

    return render_to_response('smtp.html',
                              {'form': form, 'cluster': cluster, 'smtp_status': smtp_status,
                               'object_id': object_id, 'popup': popup},
                              context_instance=RequestContext(request))


@group_required('administrator', 'system_manager')
def ipsec_view(request, object_id=None):
    """

    :param request:
    :return:
    """
    # Retrieving cluster configuration
    ipsec_status = {}
    ipsec_sa = {}

    cluster = Cluster.objects.get()

    # Object_id is defined => we are configuring a Node
    if object_id is not None:
        node = Node.objects.with_id(ObjectId(object_id))
        system_settings = node.system_settings
        old_enabled = False if not system_settings.ipsec_settings else system_settings.ipsec_settings.enabled
        # Instantiate form
        form = IPSECSettingsForm(request.POST or None, instance=system_settings.ipsec_settings)
    else:
        form = IPSECSettingsForm(None)

    # form validation
    if request.method == 'POST' and form.is_valid():
        ipsec_conf = form.save(commit=False)
        # We are configuring Node
        if object_id:
            # If the admin wants to start the service
            if not old_enabled and ipsec_conf.enabled:
                action_service = "start"
            # If he wants to stop it
            elif not ipsec_conf.enabled:
                action_service = "stop"
            # Otherwise, restart it
            else:
                action_service = "restart"
            system_settings.ipsec_settings = ipsec_conf
            node.save()

            node.api_request("/api/services/ipsec/{}/".format(action_service))

    # Service status part
    ipsec_sa=""
    if object_id:
        status = node.api_request("/api/services/ipsec/status/")
        logger.info(status)
        if isinstance(status, bool):
            ipsec_status[node.name] = ("ERROR", "Cannot contact node ")
        else:
            ipsec_status[node.name] = status['result'][0]
            ipsec_sa = status['result'][1].replace("\n", "<br>")

    else:
        ipsec_status = cluster.api_request("/api/services/ipsec/status/")
        for node in cluster.members:
            # Keep database data up-to-date
            node_info = ipsec_status.get(node.name)
            if node_info:
                try:
                    node_ipsec_state = node_info['result'][0]
                    node.system_settings.ipsec_settings.enabled = True if node_ipsec_state == 'UP' else False

                    ipsec_status[node.name] = node_ipsec_state

                except AttributeError:
                    pass
            else:
                continue

            node.save(bootstrap=True)

    return render_to_response('ipsec.html',
                              {'form': form, 'ipsec_status': ipsec_status, 'ipsec_sa':ipsec_sa, 'cluster': cluster, 'object_id': object_id},
                              context_instance=RequestContext(request))


@group_required('administrator', 'system_manager')
def restart_ipsec(request, object_id=None):
    """ View dedicated to restart Strongswan service, it sends restart request to
    selected node or to all cluster's node

    :param request: Django request object
    """
    # Object_id is provided, restart IPSec service only on related Node
    if object_id:
        node = Node.objects.with_id(ObjectId(object_id))
        response = node.api_request("/api/services/ipsec/restart/")
    # Restart IPSec service on all nodes
    else:
        cluster = Cluster.objects.get()
        response = cluster.api_request("/api/services/ipsec/restart/")
    return JsonResponse(response)

@group_required('administrator', 'system_manager')
def test_smtp(request):
    """ View dedicated to test SMTP service settings

    : param request: Django request object
    """
    cluster = Cluster.objects.get()
    node    = cluster.get_current_node()

    form_data = {
        'domain_name'       : request.POST['domain_name'],
        'smtp_server'       : request.POST['smtp_server'],
        'cluster_based_conf': request.POST['cluster_based_conf'],
    }
    recipient = request.POST['recipient']
    msg            = MIMEText("Vulture MAIL works !")
    msg['Subject'] = 'Vulture test MAIL'
    msg['From']    = "localhost@{}".format(node.name)
    msg['To']      = recipient

    try:
        s = smtplib.SMTP(form_data['smtp_server'])
        s.sendmail("localhost@{}".format(node.name), [recipient], msg.as_string())
        s.quit()
        return JsonResponse({'status': True})
    except Exception as e:
        return JsonResponse({'status': False, 'error': e.__str__().split(']')[1]})



@group_required('administrator', 'system_manager')
def ssh_view(request, object_id = None):
    """ """
    ssh_status = {}
    node_list = []
    api_url = "/api/services/ssh"
    popup = ""
    # Retrieving cluster configuration
    cluster = Cluster.objects.get()

    # Object_id is defined => we are configuring a Node
    if object_id is not None:
        """ Verify if objectId id valid and exists in DB """
        try:
            node = Node.objects.with_id(ObjectId(object_id))
            if not node:
                raise InvalidId()
        except InvalidId:
            return HttpResponseForbidden('Injection detected')
        system_settings = node.system_settings
        node_or_cluster = node
        node_list.append(node)
    # Cluster configuration
    else:
        system_settings = cluster.system_settings
        node_or_cluster = cluster
        node_list = cluster.members

    # Instantiate form
    form = SSHSettingsForm(request.POST or None,
                           instance=system_settings.ssh_settings)

    # form validation
    if request.method == 'POST' and form.is_valid():
        ssh_conf = form.save(commit=False)
        node_or_cluster.system_settings.ssh_settings = ssh_conf

        old_enabled = False if not system_settings.ssh_settings else system_settings.ssh_settings.enabled

        # Save settings
        node_or_cluster.save()

        # If the admin wants to start the service
        if not old_enabled and ssh_conf.enabled:
            action_service = "start"
        # If he wants to stop it
        elif not ssh_conf.enabled:
            action_service = "stop"
        # Otherwise, restart it
        else:
            action_service = "restart"

        api_result = node_or_cluster.api_request("{}/{}/".format(api_url, action_service))
        if isinstance(node_or_cluster, Cluster):
            for node in node_list:
                node_result = api_result.get(node.name, {})
                if not node_result:
                    popup = ("ERROR", "Error on node {}.".format(node.name))
                else:
                    popup = node_result.get('result')
        else:
            if not api_result:
                popup = ("ERROR", "Error on node {}.".format(node_or_cluster.name))
            else:
                popup = api_result.get('result')
        # Sleep while service is stopping/starting before get its status
        sleep(2)

    # Service status part
    if object_id:
        status = node.api_request("{}/status/".format(api_url))
        ssh_status[node.name] = ('ERROR', "Error on node {}.".format(node.name)) if not status else status.get('result')
        if node.system_settings.ssh_settings and status and status.get('result'):
            node.system_settings.ssh_settings.enabled = True if status.get('result', ['DOWN'])[0] == 'UP' else False
            node.save(bootstrap=True)
    else:
        cluster_res = cluster.api_request("{}/status/".format(api_url))
        for node in cluster.members:
            # Keep database data up-to-date
            node_info = cluster_res.get(node.name)
            if node_info:
                node_ssh_state = node_info.get('result', ['ERROR', "Error on node {}.".format(node.name)])
                try:
                    ssh_status[node.name] = node_ssh_state
                    if node.system_settings.ssh_settings:
                        node.system_settings.ssh_settings.enabled = True if node_ssh_state[0] == 'UP' else False
                        node.save(bootstrap=True)
                except AttributeError as e:
                    logger.error("SSH::view: Error while trying to parse for node {} status : {}".format(node.name, e))
            else:
                ssh_status[node.name] = ('ERROR', "Error on node {}.".format(node.name))

    return render_to_response('ssh.html',
                              {'form': form, 'ssh_status': ssh_status, 'popup': popup,
                               'cluster': cluster, 'object_id': object_id},
                              context_instance=RequestContext(request))


@group_required('administrator', 'system_manager')
def pf_view(request, object_id):
    """ """
    pf_status = {}
    # Retrieving cluster configuration
    cluster = Cluster.objects.get()

    # Object_id is defined => we are configuring a Node
    if object_id is not None:
        node = Node.objects.with_id(ObjectId(object_id))
    else:
        node = cluster.get_current_node()


    system_settings = node.system_settings

    # Instantiate form
    form = PFSettingsForm(request.POST or None,
                           instance=system_settings.pf_settings)

    # form validation
    if request.method == 'POST' and form.is_valid():
        pf_conf = form.save(commit=False)
        data_repository   = form.cleaned_data.get('data_repository')
        syslog_repository = form.cleaned_data.get('syslog_repository')
        repository_type   = form.cleaned_data.get('repository_type')

        pf_conf.data_repository   = data_repository
        pf_conf.syslog_repository = syslog_repository
        pf_conf.repository_type   = repository_type

        rules = json.loads(request.POST['pf_rules'])
        pf_conf.pf_rules = []
        for rule in rules:

            for x in ('source', 'destination', 'port'):
                if ',' in rule[x] and not rule[x].startswith('{') and not rule[x].endswith('}'):
                    rule[x] = "{ "+rule[x]+" }"

            pf_conf.pf_rules.append(PfRules(**rule))

        pf_conf.pf_rules_text = pf_conf.pf_rules_text.replace("\r", "")
        system_settings.pf_settings = pf_conf

        node.save(bootstrap=True)


    status = node.api_request("/api/services/pf/status/")
    cluster.api_request("/api/logs/management/")
    if status:
        pf_status[node.name] = status['result'][0]
        pf_current_blacklist = status['result'][1]['pf_current_blacklist']
        pf_current_whitelist = status['result'][1]['pf_current_whitelist']
    else:
        pf_status[node.name] = "Service error, check logs"
        pf_current_blacklist = "Service error, check logs"
        pf_current_whitelist = "Service error, check logs"

    parameters = {
        'protocol' : json.dumps(PfRules.PROTOCOL),
        'action'   : json.dumps(PfRules.ACTION),
        'direction': json.dumps(PfRules.DIRECTION),
    }

    interfaces = [('any', 'ANY')]
    for intf in Interface.objects.all():
        listeners = []
        for ip in intf.inet_addresses:
            try:
                if ip.is_physical:
                    listeners.append(ip.ip)
            except:
                pass

        interfaces.append((intf.device, '{} - {}'.format(intf.device, ",".join(listeners))))

    try:
        rules = [rule.to_json() for rule in system_settings.pf_settings.pf_rules]
    except:
        rules = []


    return render_to_response('pf.html',
                              {'form': form, 'pf_status': pf_status,
                               'cluster': cluster, 'object_id': node.id,
                               'parameters': parameters, 'rules': json.dumps(rules),
                               'interfaces': json.dumps(interfaces),
                               'pf_current_blacklist': pf_current_blacklist.replace("\n","<br/>"),
                               'pf_current_whitelist': pf_current_whitelist.replace("\n","<br/>")
                               },
                                context_instance=RequestContext(request))

@group_required('administrator', 'system_manager')
def restart_pf(request, object_id=None):
    """ View dedicated to restart PF service, it sends restart request to
    selected node

    :param request: Django request object
    """
    # If Object_id is provided, restart PF service only on related Node
    # Else restart pf on every node
    if object_id:
        node = Node.objects.with_id(ObjectId(object_id))
        response = node.api_request("/api/services/pf/restart/")
    else:
        cluster = Cluster.objects.get()
        response = cluster.api_request("/api/services/pf/restart/")

    return JsonResponse(response)


def is_subnet_of(a, b):
   """
   Returns boolean: is `a` a subnet of `b`?
   """
   a = ipaddress.ip_network(a)
   b = ipaddress.ip_network(b)
   a_len = a.prefixlen
   b_len = b.prefixlen
   return a_len >= b_len and a.supernet(a_len - b_len) == b

@group_required('administrator', 'system_manager')
def loganalyser_view(request, object_id):
    """ """
    # Retrieving cluster configuration
    cluster = Cluster.objects.get()
    system_settings = cluster.system_settings

    # Instantiate form
    form = LogAnalyserSettingsForm(request.POST or None, instance=system_settings.loganalyser_settings)

    # form validation (Live test of an IP address against redis reputation database)
    if (request.method == 'POST' and request.POST.get('test_reputation')):
        ip = request.POST.get('test_reputation')

        try:
            reader = maxminddb.open_database('/var/db/loganalyzer/ip-reputation.mmdb')
            data   = reader.get(ip)['reputation']
            return JsonResponse({'status': data})
        except:
            return JsonResponse({'status': "Good"})

    # form validation (Update of reputation database)
    elif request.method == 'POST' and form.is_valid():
        loganalyser_conf = form.save(commit=False)

        loganalyser_conf.loganalyser_rules = []
        rules = [v for k, v in request.POST.lists() if k.startswith('loganalyser_rules')]

        for rule in rules:
            loganalyser_conf.loganalyser_rules.append(LogAnalyserRules(**{
                'url': rule[0],
                'description': rule[1],
                'tags': rule[2]
            }))

        system_settings.loganalyser_settings = loganalyser_conf.save()

        cluster = Cluster.objects.get()
        system_settings = cluster.system_settings

    try:
        rules = system_settings.loganalyser_settings.loganalyser_rules
    except:
        rules = []

    return render_to_response('loganalyser_settings.html',
                              {'form': form, 'rules': rules},
                              context_instance=RequestContext(request))
