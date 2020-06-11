#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals


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
__doc__ = 'Django models dedicated to applications'

from django.conf import settings
from django.utils.crypto import get_random_string
from django.utils.translation import ugettext_lazy as _
from mongoengine import StringField, BooleanField, DynamicDocument, ReferenceField, ListField, IntField, PULL
from mongoengine.base.datastructures import BaseList

from gui.models.modaccess_settings import ModAccess
from gui.models.modlog_settings import ModLog
from gui.models.modsec_settings import ModSec, ModSecRules, ModSecSpecificRulesSet, ModSecDOSRules, ModSecRulesSet
from gui.models.modssl_settings import ModSSL
from gui.models.network_settings import Listener
from gui.models.repository_settings import SSOProfile
from gui.models.ssl_certificate import SSLCertificate
from gui.models.system_settings import Cluster
from gui.models.template_settings import portalTemplate
from gui.models.user_document import VultureUser
from gui.models.worker_settings import Worker
from gui.signals.gui_signals import app_modified
from vulture_toolkit.network import net_utils
from vulture_toolkit.system import http_pins as PKP
from vulture_toolkit.system.aes_utils import AESCipher
from vulture_toolkit.system.http_utils import get_uri_fqdn_without_scheme, get_uri_path
from vulture_toolkit.system.replica_set_client import ReplicaSetClient, ReplicaConnectionFailure
from vulture_toolkit.templates import tpl_utils

from bson.objectid import ObjectId
import hashlib
import os
import codecs
import logging
import re
import json
import copy
from secret_key import SECRET_KEY
from ssl import PROTOCOL_SSLv3, PROTOCOL_TLSv1, PROTOCOL_TLSv1_1, PROTOCOL_TLSv1_2
import sys

logger = logging.getLogger('debug')

SSL_PROTOCOLS = (
    (int(PROTOCOL_SSLv3), 'SSLv3'),
    (int(PROTOCOL_TLSv1), 'TLSv1'),
    (int(PROTOCOL_TLSv1_1), 'TLSv1.1'),
    (int(PROTOCOL_TLSv1_2), 'TLSv1.2'),
)

class Filter(DynamicDocument):
    """ Filter for the log window
    name   : the name of the filter
    content: conditions string for query builder
    user   : the owner of the filter
    """

    name = StringField(required=True)
    content = StringField(required=True)
    user = ReferenceField(VultureUser, required=True, reverse_delete_rule=PULL)
    type_logs = StringField(required=True, choices=('security', 'access', 'packet_filter', 'vulture', 'diagnostic'))


class HeaderIn(DynamicDocument):
    """ Rules on incoming HTTP headers
    action: The action to be done on the incoming header
    name: HTTP Header name
    value: Pattern on the header value
    replacement: Pattern for replacement
    condition: The condition for the rule to be triggered
    condition_v: The condition expression or environment variable
    """

    ACTION_LIST = (
        ('set'),
        ('setifempty'),
        ('add'),
        ('append'),
        ('merge'),
        ('edit'),
        ('edit*'),
        ('unset')
    )

    CONDITION_LIST = (
        ('always'),
        ('satisfy'),
        ('env_exists'),
        ('env_not_exists')
    )

    enable = BooleanField(required=True, default=True)
    action = StringField(required=True, choices=ACTION_LIST)
    name = StringField(required=True)
    value = StringField(required=False)
    replacement = StringField(required=False)
    condition = StringField(required=True, choices=CONDITION_LIST)
    condition_v = StringField(required=False)


class HeaderOut(DynamicDocument):
    """ Rules on outgoing HTTP headers
    action: The action to be done on the response header
    name: HTTP Header name
    value: Pattern on the header value
    replacement: Pattern for replacement
    condition: The condition for the rule to be triggered
    condition_v: The condition expression or environment variable
    """

    ACTION_LIST = (
        ('set'),
        ('setifempty'),
        ('add'),
        ('append'),
        ('merge'),
        ('edit'),
        ('edit*'),
        ('unset'),
        ('copy'),
        ('store')
    )

    CONDITION_LIST = (
        ('always'),
        ('satisfy'),
        ('env_exists'),
        ('env_not_exists')
    )

    enable = BooleanField(required=True, default=True)
    action = StringField(required=True, choices=ACTION_LIST)
    name = StringField(required=True)
    value = StringField(required=False)
    replacement = StringField(required=False)
    condition = StringField(required=True, choices=CONDITION_LIST)
    condition_v = StringField(required=False)


class ContentRule(DynamicDocument):
    """ mod_substitute and mod_deflate Management
    types: The Content-Types affected by the rule
    deflate: Do we have to deflate before rewriting ?
    inflate: Do we have to inflate after rewriting ?
    pattern: The pattern to replace
    replacement: The replacement
    replacement_flags: The mod_substitute flags
    """

    enable = BooleanField(required=True, default=True)
    types = StringField(required=False)
    condition = StringField(required=False)
    deflate = BooleanField(required=False, default=False)
    inflate = BooleanField(required=False, default=False)
    pattern = StringField(required=False)
    replacement = StringField(required=False)
    flags = StringField(required=False)


class ProxyBalancerMember(DynamicDocument):
    """ Configuration of proxy balancer members
    uri_type: Type of backend
    uri: URI of backend
    disablereuse: Immediately close connection to backend after use. Defaults is 'Off'. Set this to On if there is a firewall between us and backend and if this firewall drops packets
    keepalive: Default to 'Off'. Set this to On if there is a firewall between us and backend and if this firewall drops packets
    lbset: Load-Balancing group ID
    retry: Delay, in second, between attempts when the backend server is down
    route: Route ID of the backend
    timeout: Defaults to ProxyTimeout
    ttl: Delay in second after which a connection will not be reused
    config: Expert mode - balancer member configuration
    """

    APP_TYPE = (
        ('http', 'Web Application'),
        ('https', 'SSL/TLS Web Application'),
        ('ftp', 'FTP Application'),
        ('fcgi', 'FCGI Application'),
        ('scgi', 'SCGI Application'),
        ('wstunnel', 'Websocket Tunnel'),
        ('ajp', 'AJP Proxy')
    )

    uri_type = StringField(required=True, choices=APP_TYPE, default='http', help_text=_('Backend type'))
    uri = StringField(required=True, help_text=_('Backend IP Address'))
    disablereuse = BooleanField(default=False,
                                help_text=_('If set to "On", immediately close connection to backend after use'))
    keepalive = BooleanField(default=False, help_text=_('If set to "On", proxy will send KeepAlive to backend server'))
    lbset = StringField(required=False, default=0, help_text=_('Load-balancer group ID'))
    retry = StringField(required=False, default=60,
                        help_text=_('Delay, in second, between attempts when the backend server is down'))
    route = StringField(required=False, help_text=_('Route ID of the backend'))
    timeout = StringField(required=True, default='%ProxyTimeout%',
                          help_text=_('Time to wait, in second, for backend answer'))
    ttl = StringField(required=False, help_text=_('Delay in second after which a connection will not be reused'))
    config = StringField(required=False,
                         help_text=_('Expert mode. See http://httpd.apache.org/docs/current/mod/mod_proxy.html'))

    def __str__(self):
        return "{}".format(self.uri_type + '://' + self.uri)


class ProxyBalancer(DynamicDocument):
    """ Configuration of mod_proxy_balancer settings
    name: A friendly name for the balancer
    lbmethod: LB algorithm (Apache defaults to 'byrequests')
    maxattempts: Max attempts before failure (Apache defaults to 'nb_worker - 1')
    nofailover: If set to On, the session will stop if the targeted host is down (Apache defaults to 'Off')
                Set this to On if backends do not support session replication
    stickysession: Name of the persistent SESSION COOKIE
    stickysessionsep: Separator character in the session cookie (Apache defaults to '.')
    scolonpathdelim: If set to 'On', the character ';' will be used as a path separator in the stickysession (Apache defaults to 'Off')
    timeout: Load-balancer timeout in second (Apache defaults to 0)
    failontimeout: If set to 'On', the process will fail if a timeout occurs with backend (Apache defaults to 'Off')
    failonstatus: List of comma-separated backend HTTP status code on which the worker will fail
    forerecovery: If set to 'On', all members will be queried again if they are all in error mode. (Apache defaults to 'On')
    """

    LB_METHODS = (
        ('bybusyness', 'By backend busyness'),
        ('heartbeat', 'By heartbeat'),
        ('byrequests', 'By backend requests'),
        ('bytraffic', 'By Traffic')
    )

    

    name = StringField(required=True, help_text=_('Friendly name to reference the application'))
    lbmethod = StringField(required=True, choices=LB_METHODS, help_text=_('Load-Balancing algorithm'))
    stickysession = StringField(required=False, help_text=_('The name of the persistent session Cookie'))
    stickysessionsep = StringField(required=True, default='.', help_text=_(
        'Separator character in the session cookie. Set to "Off" for no separator'))
    config = StringField(required=False,
                         help_text=_('Expert mode. See http://httpd.apache.org/docs/current/mod/mod_proxy.html'))
    members = ListField(ReferenceField('ProxyBalancerMember', reverse_delete_rule=PULL))
    hcmethod = StringField (required=False, default='None',help_text=_('How to check that backends are available'))
    hcpasses = StringField (required=False, default=1, help_text=_('Number of successful health check tests before worker is re-enabled'))
    hcfails = StringField (required=False, default=1, help_text=_('Number of failed health check tests before worker is disabled'))
    hcinterval = StringField (required=False, default=30, help_text=_('Period of health checks in seconds (e.g. performed every 30 seconds)'))
    hcuri = StringField (required=False, help_text=_('Additional URI to be appended to the worker URL for the health check'))
    hcexpr = StringField (required=False, help_text=_('Expression used to check response headers for health'))
    hcexpr_data = StringField (required=False)

    def __str__(self):
        if self.is_ssl():
            return "{}".format(self.name + ' [ Method = ' + self.lbmethod + ', TLS ]')
        else:
            return "{}".format(self.name + ' [ Method = ' + self.lbmethod + ' ]')

    def is_ssl(self):
        for member in self.members:
            if member.uri_type == "https":
                return True
        return False

    def memberList(self):
        if not self.members:
            return '<Please add members>'
        str = ''
        for member in self.members:
            str += "{}".format(member.uri_type + '://' + member.uri + '<br>')
        return str


class ListenAddress(DynamicDocument):
    """ Addresses on which the application will be accessible
    listener: A reference to a listener
    port: The port number to listen on
    ssl_profile: The SSL profile to use
    is_up2date: Internal flag to speed up GUI: If False, then config should be restarted
    """
    address = ReferenceField('Listener', reverse_delete_rule=PULL, required=True,
                             help_text=_('Select the listener'))
    port = StringField(required=True, help_text=_('Select the TCP port to listen on'))
    redirect_port = StringField(required=False,
                                help_text=_('Select the Translated public TCP port to use in redirection'))
    ssl_profile = ReferenceField('ModSSL', reverse_delete_rule=PULL,
                                 help_text=_('Select the SSL profile to use for network encryption'))

    is_up2date = BooleanField(default=False)
    related_node = ReferenceField('Node', required=False)

    def __init__(self, *args, **kwargs):
        self.internal_error = dict()
        super(ListenAddress, self).__init__(*args, **kwargs)

    def isRunning(self):
        node = self.get_related_node()
        status = node.api_request("/api/network/listener/running/%s/%s" % (str(self.address.id), self.port))
        if status and status.get('status'):
            return True
        return False

    def get_related_node(self, nosave=None):
        """ To avoid breaking things after GUI-0.5 migration """
        if self.related_node:
            return self.related_node

        self.related_node = self.address.get_related_node()
        if not nosave:
            self.save()
        return self.related_node

    def buildConf(self, config):
        """ Write the given config on disk on appropriate nodes
        :return: True or False
        """

        # Write Certificate Files, if needed
        if self.ssl_profile:
            self.ssl_profile.writeConf()

        # Write ModSecurity Rules, if needed
        # Find all applications that share the same address / port
        apps = self.get_apps()

        templates, rules, tmp_rules, svms, certs_id = [], [], [], [], []
        for app in apps:
            # Creating list of templates to write on disk
            if app.template.id not in templates:
                templates.append(app.template.id)

            # Creating list of rules to write on disk
            for rule in app.rules_set:
                if rule.id not in tmp_rules:
                    rules.append(rule)
                    tmp_rules.append(rule.id)

            # Creating list of rules to write on disk
            for rule in app.specific_rules_set:
                if rule.id not in tmp_rules:
                    rule.rs.conf = rule.rs.get_conf()
                    rules.append(rule.rs)
                    tmp_rules.append(rule.rs.id)

            app.wl_bl_rules.write_conf()

            # Creating list of SSL Client certificate to write on disk
            if app.ssl_client_certificate:
                path_split = app.ssl_client_certificate.split("SSLProxyCertificateFile-")
                cert_id = path_split[1][:-4]

                if cert_id not in certs_id:
                    certs_id.append(cert_id)

            for svm_id in app.activated_svms:
                if svm_id not in svms:
                    svms.append(svm_id)

            if app.activated_svms:
                from gui.models.dataset_settings import SVM
                for svm_id in app.activated_svms:
                    svm = SVM.objects.no_dereference().with_id(ObjectId(svm_id))
                    logger.info("Building configuration of SVM with id '{}'".format(svm_id))
                    svm_config = svm.getConf()
                    if svm_config['error']:
                        logger.error(
                            "Cannot build configuration of SVM with id {} : {}".format(svm_id, svm_config['error']))
                    else:
                        if svm.write_conf(svm_config['config']):
                            logger.info("SVM(id:{}) configuration writed successfully".format(svm_id))
                        else:
                            logger.error("Unable to write configuration of SVM(id:{})".format(svm_id))

        # Write Apache configuration
        try:
            with codecs.open(self.configuration_path, 'w', encoding='utf8') as f:
                f.write(config)
        except Exception as e:
            logger.error("Unable to build configuration. Reason is: " + str(e))
            logger.exception(e)
            return False

        ## Writing templates on disk
        for t in templates:
            portalTemplate.objects.with_id(t).write_on_disk()

        ## Writing rules
        for r in rules:
            r.write_conf()

        ## Writing SSL Client certificate
        for cert_id in certs_id:
            cert = SSLCertificate.objects.with_id(ObjectId(cert_id))
            cert.write_certificate()

        ## Writing SVM
        if svms:
            from gui.models.dataset_settings import SVM

        for svm_id in svms:
            svm = SVM.objects.no_dereference().with_id(ObjectId(svm_id))
            logger.info("Building configuration of SVM with id '{}'".format(svm_id))
            svm_config = svm.getConf()
            if svm_config['error']:
                logger.error("Cannot build configuration of SVM with id {} : {}".format(svm_id, svm_config['error']))
            else:
                if svm.write_conf(svm_config['config']):
                    logger.info("SVM(id:{}) configuration writed successfully".format(svm_id))
                else:
                    logger.error("Unable to write configuration of SVM(id:{})".format(svm_id))

        """ Update all listener that shares the same IP:port """
        listenaddress_all = ListenAddress.objects.filter(address=self.address, port=self.port)
        for l in listenaddress_all:
            l.is_up2date = True
            l.save()

        return True

    def get_apps(self):
        """returns a list with all applications that share the same address / port
            This is sorted by reverse_public dir, as we need this order in apache configuration file
        :return: A list of Applications
        """
        listenaddress_all = ListenAddress.objects.filter(address=self.address, port=self.port)
        return Application.objects.filter(listeners__in=listenaddress_all, enabled=True).order_by('-public_dir')

    def getConf(self, rewrite_rules):
        """return the "in-database" configuration for this listener
         A configuration is the whole configuration file for a given listener address and port
         Reminder: There is One configuration file per listener on each node
         :return: A dict containing the whole Apache configuration
         """
        from gui.models.dataset_settings import SVM
        parameters = dict()
        rewriting = dict()

        # Variables for server context
        parameters['server_address'] = self.address.ip
        parameters['server_port'] = self.port

        try:
            parameters['server_main_address'] = self.address.get_related_node().get_management_listener()
        except Exception as e:
            parameters['server_main_address'] = "127.0.0.1"
            logger.exception(e)

        unique_id = hashlib.md5()
        unique_id.update(str(self.address.ip + self.port).encode('utf8', 'ignore'))
        parameters['pid_file'] = "/home/vlt-sys/run/{}.pid".format(unique_id.hexdigest())
        parameters['scoreboard_file'] = "/home/vlt-sys/run/{}.runtime_status".format(unique_id.hexdigest())
        parameters['sslsessioncache_file'] = "shmcb:/home/vlt-sys/run/{}.ssl_gcache_data(512000)".format(
            unique_id.hexdigest())
        parameters['sslstaplingcache_file'] = "shmcb:/home/vlt-sys/run/{}.ssl_stapling_data(128000)".format(
            unique_id.hexdigest())

        parameters['server_ssl_profile'] = self.ssl_profile
        parameters['server_worker'] = None
        parameters['server_log_buffered'] = list()
        parameters['server_global_rewriting'] = list()
        parameters['server_log_format'] = list()
        parameters['server_module_svm2'] = False
        parameters['server_module_svm3'] = False
        parameters['server_module_svm4'] = False
        parameters['server_module_svm5'] = False

        # Variables for application context
        parameters['apps'] = list()
        parameters['local_ips'] = list()

        # Dictionary used to detect conflict in the configuration
        # This can happens when, for example, 2 applications sharing same IP/port use different SSL Profiles
        conf_error = list()

        # Load cluster global configuration
        cluster = Cluster.objects.get()
        system_settings = cluster.system_settings
        global_conf = system_settings.global_settings

        parameters['server_portal_cookie'] = global_conf.portal_cookie
        parameters['server_app_cookie'] = global_conf.app_cookie
        parameters['server_portal_cookie'] = global_conf.portal_cookie
        parameters['server_public_token'] = global_conf.public_token
        parameters['server_oauth2_token'] = global_conf.x_vlt_token
        parameters['vulture_status_ip_allowed'] = global_conf.vulture_status_ip_allowed

        try:
            parameters['remote_ip_internal_proxy'] = [ip for ip in global_conf.remote_ip_internal_proxy if ip != ""]
        except:
            parameters['remote_ip_internal_proxy'] = []

        for listener in Listener.objects.all():
            parameters['remote_ip_internal_proxy'].append(listener.ip)

        parameters['remote_ip_internal_proxy'] = set(parameters['remote_ip_internal_proxy'])

        parameters['server_ssl_proxyengine'] = 'Off'
        parameters['server_ssl_proxy_protocol'] = ""
        parameters['server_ssl_proxyciphersuite'] = ""
        parameters['server_ssl_proxyverify'] = False
        parameters['server_ssl_proxycacertificatepath'] = "/home/vlt-sys/Engine/conf/certs/"
        parameters['server_ssl_proxycheck_peer_name'] = False
        parameters['server_ssl_proxycheck_peer_expire'] = False
        parameters['server_ssl_proxymachine_certificate_file'] = ""
        parameters['server_module_geoip'] = False
        parameters['server_module_geoip_city'] = False
        parameters['server_module_reputation'] = False

        parameters['modsec_policy'] = ModSec.objects()
        parameters['rules_set'] = list()
        parameters['ssl_profile'] = ModSSL.objects()

        # Prepare rewriting rules
        for rewrite in rewrite_rules:
            # Global rewriting rules
            global_rules = rewrite.buildRules()
            if not rewrite.application and global_rules not in parameters['server_global_rewriting']:
                parameters['server_global_rewriting'].append(global_rules)
            # Application specific rewriting rules
            else:
                for rewrite_appli in rewrite.application:
                    try:
                        if global_rules not in rewriting[rewrite_appli.id]:
                            rewriting[rewrite_appli.id].append(global_rules)
                    except:
                        rewriting[rewrite_appli.id] = list()
                        rewriting[rewrite_appli.id].append(global_rules)

        # Find all applications that share the same address / port
        apps = self.get_apps()
        subapps = dict()

        # Create a dict to have applications associated to a private URI
        # This will be used to create one <proxy> section for each private_uri
        private_uris = dict()

        activated_svms = {}
        for app in apps:
            app.name = str(app.name).replace(' ', '_')
            if app.type == "balanced":
                app_k = "balancer://{}".format(app.id)
            else:
                app_k = "{}".format(app.private_uri)

            try:
                private_uris[app.public_name][app_k].append(app)
            except:
                try:
                    private_uris[app.public_name][app_k] = list()
                    private_uris[app.public_name][app_k].append(app)
                except:
                    private_uris[app.public_name] = dict()
                    private_uris[app.public_name][app_k] = list()
                    private_uris[app.public_name][app_k].append(app)

            try:
                app.rewriting = rewriting[app.id]
            except:
                pass

            # Add rules set used by the app
            for ruleset in app.rules_set:
                if ruleset.type_rule in ['crs', 'vulture', 'trustwave', 'custom']:
                    if ruleset not in parameters['rules_set']:
                        parameters['rules_set'].append(ruleset)

            for ruleset in app.specific_rules_set:
                if ruleset.rs.type_rule in ['crs', 'vulture', 'trustwave', 'custom']:
                    if ruleset.rs not in parameters['rules_set']:
                        parameters['rules_set'].append(ruleset.rs)

            # Detect conflicts in SSL configuration
            first = 1

            certificate_pinning_sha256=list()
            for listener in app.listeners:
                if listener.address.ip not in parameters['local_ips']:
                    parameters['local_ips'].append(listener.address.ip)

                if listener.ssl_profile is None:
                    continue

                if listener.address.ip == self.address.ip and listener.port == self.port:

                    # This is saved for SSL server config: we take the first returned listener
                    if first == 1:
                        first = 0
                        parameters['server_ssl_profile'] = listener.ssl_profile

                    # This is saved for SSL application config
                    app.ssl_profile = listener.ssl_profile

                    # SSL Certificate MD5 compute
                    if listener.ssl_profile:
                        hash = hashlib.md5()
                        if listener.ssl_profile.accepted_ca:
                            hash.update(listener.ssl_profile.accepted_ca.encode('utf8', 'ignore'))
                            app.ssl_profile.SHA256sum_accepted_ca = hash.hexdigest()

                        if listener.ssl_profile.certificate.chain:
                            hash.update(listener.ssl_profile.certificate.cert.encode('utf8',
                                                                                         'ignore') + self.ssl_profile.certificate.chain.encode(
                                'utf8', 'ignore'))
                            app.ssl_profile.SHA256sum_cert = hash.hexdigest()
                        else:
                            hash.update(listener.ssl_profile.certificate.cert.encode('utf8', 'ignore'))
                            app.ssl_profile.SHA256sum_cert = hash.hexdigest()

                        hash.update(listener.ssl_profile.certificate.key.encode('utf8', 'ignore'))
                        app.ssl_profile.SHA256sum_key = hash.hexdigest()

                        crl = listener.ssl_profile.certificate.getCRL()
                        if crl:
                            hash.update(crl.encode('utf8', 'ignore'))
                            app.ssl_profile.SHA256sum_crl = hash.hexdigest()

                            #Compute HTTP Public Key Pinning Extensions, if needed
                            if app.ssl_profile.hpkp_enable:
                                app.ssl_profile.pkp=PKP.getSPKIFingerpring(app.ssl_profile.certificate.cert)

                    if str(parameters['server_ssl_profile'].engine) != str(app.ssl_profile.engine):
                        conf_error.append('[TLS] - CryptoDevice for application ' + str(app.name) + ' is ' + str(
                            app.ssl_profile.engine) + '. Expected: ' + str(parameters['server_ssl_profile'].engine))



            """ SERVER CONFIGURATION """
            """ We do that to speed up template generation """
            app.balancer_config = app.get_proxy_balancer()
            if app.type == 'balanced' and app.balancer_config:
                parameters['server_module_proxybalancer'] = True
                parameters['server_module_lbmethod_' + str(app.proxy_balancer.lbmethod)] = True
                for member in app.proxy_balancer.members:
                    if member.uri_type in ('http', 'https'):
                        parameters['server_module_proxy_http'] = True
                    else:
                        parameters['server_module_proxy_' + str(member.uri_type)] = True
            else:
                if app.type in ("https", 'http'):
                    parameters['server_module_proxy_http'] = True
                else:
                    parameters['server_module_proxy_' + str(app.type)] = True

            if app.geoip is True:
                parameters['server_module_geoip'] = True

            if app.geoip_city is True:
                parameters['server_module_geoip_city'] = True

            if app.reputation is True:
                parameters['server_module_reputation'] = True

            if app.get_headers("in") or app.get_headers("out"):
                parameters['server_module_headers'] = True

            if parameters['server_log_buffered'] and str(parameters['server_log_buffered']) != str(
                    app.log_custom.buffered):
                conf_error.append('[ModLog] - BufferedLogs for application ' + str(app.name) + ' is ' + str(
                    app.log_custom.buffered) + '. Application ' + str(
                    parameters['server_log_buffered_app_ref']) + ' has previously defined this setting to ' + str(
                    parameters['server_log_buffered']))
            else:
                parameters['server_log_buffered'] = app.log_custom.buffered
                parameters['server_log_buffered_app_ref'] = app.name

            if parameters['server_worker']:
                wk = parameters['server_worker']
                if str(wk.id) != str(app.worker.id):
                    conf_error.append('[Worker] -  Worker is ' + str(app.worker.name) + 'for application ' + str(
                        app.name) + '. Application: ' + str(
                        parameters['server_worker_app_ref']) + ' has previously defined this setting to ' + str(
                        wk.name))
            else:

                """ These methods are time consuming, call them here once, not in template """
                app.worker.h2_config = app.worker.get_h2_config()
                app.worker.req_timeout = app.worker.get_req_timeout()
                app.worker.req_limit = app.worker.get_rate_limit()
                app.worker.maxrequestworkers = app.worker.getMaxRequestWorkers()

                parameters['server_worker'] = app.worker
                parameters['server_worker_app_ref'] = app.name

                if app.worker.rate_limit:
                    parameters['server_module_ratelimit'] = True
                if app.worker.req_timeout:
                    parameters['server_module_reqtimeout'] = True
                if app.worker.h2_config and app.enable_h2:
                    parameters['server_module_h2'] = True

            if app.enable_rpc:
                parameters['server_module_rpc'] = True

            if app.modsec_policy or app.learning:
                parameters['server_module_security'] = True
                parameters['server_module_defender'] = True

            """ APPLICATIONS' CONFIGURATION """

            """ We do that to speed up template generation """
            app.proxy_balancer_hcexpr = app.get_proxy_balancer_hcexpr()
            app.public_dir_clean = app.public_dir.replace('/', '')
            app.redirect_uri = app.get_redirect_uri()
            app.private_uri_is_ssl = app.private_uri_is_ssl()
            app.private_uri_fqdn = app.private_uri_fqdn()
            app.private_uri_path = app.private_uri_path()

            app.headers_tpl_in = app.get_headers('in')
            # We need to force ProxyPreserveHost to 'On' if the user wants to add or Rewrite a 'Host' header
            if 'Host' in app.headers_tpl_in:
                app.preserve_host = True

            app.headers_tpl_out = app.get_headers('out')
            app.dos_rules = app.get_modsec_dos_rules()
            app.rules = app.get_rules()

            app.reputation_tags = ",".join(app.block_reputation)
            app.reputation_tags_pipe = "|".join(app.block_reputation)
            app.allow_geoip = "|".join(app.allow_geoip)
            app.block_geoip = "|".join(app.block_geoip)

            # SVMs part
            # The 'activated_svms' attribute of app contains the ids of the svm to activate for that app
            for svm_id in app.activated_svms:
                svm = SVM.objects(id=ObjectId(svm_id)).no_dereference().only('built', 'algo_used',
                                                                             'dataset_used').first()
                # If the svm is built
                if svm.built:
                    # Add it to the dict
                    try:
                        svm_conf_file = svm.get_config_file()
                        if not svm_conf_file:
                            logger.error(
                                "getConf::Can't get config_filename of svm '{}' for app '{}'".format(svm_id, app.name))
                            continue
                        else:
                            activated_svms[str(app.id)].append(svm.get_config_file())
                    except:
                        activated_svms[str(app.id)] = list()
                        svm_conf_file = svm.get_config_file()
                        if not svm_conf_file:
                            logger.error(
                                "getConf::Can't get config_filename of svm '{}' for app '{}'".format(svm_id, app.name))
                            continue
                        else:
                            activated_svms[str(app.id)].append(svm.get_config_file())
                    # Add the necessary attribute to the conf, to LoadModule
                    if svm.algo_used == "Levenstein":
                        parameters['server_module_svm2'] = True
                    elif svm.algo_used == "Levenstein2":
                        parameters['server_module_svm3'] = True
                    elif svm.algo_used == "HTTPcode_bytes_received":
                        parameters['server_module_svm4'] = True
                    elif svm.algo_used == "Ratio":
                        parameters['server_module_svm5'] = True
                # If the svm is not built
                else:
                    logger.error(
                        "getConf::SVM with id '{}' is not built - can't activate it for app '{}'".format(svm_id,
                                                                                                         app.name))

            """ Group applications by public_name """
            try:
                subapps[app.public_name].append(app)
            except:
                subapps[app.public_name] = list()
                """ Add vulture-status and vulture-balancer-status as App, to create Location """
                subapps[app.public_name].append(Application(name="vulture-status", type="http", public_dir="vulture-status"))
                subapps[app.public_name].append(Application(name="vulture-balancer-status", type="http", public_dir="vulture-balancer-status"))
                subapps[app.public_name].append(app)

            if app.log_custom not in parameters['server_log_format']:
                parameters['server_log_format'].append(app.log_custom)

            # ModSecurity part
            if len(app.rules_set):
                parameters['server_module_security'] = True

        """ Order apps by length of public dir """
        for public_name, apps in subapps.items():
            subapps[public_name] = sorted(subapps[public_name], key=lambda app: len(app.public_dir), reverse=True)

        first_app = None
        backend_conns = {}
        for public_name, apps in subapps.items():

            for app in apps:
                if first_app is None and app.name not in ("vulture-status", "vulture-balancer-status"):
                    first_app = app

                if first_app is not None and app.enable_proxy_protocol != first_app.enable_proxy_protocol:
                    conf_error.append("[PROXY] PROXY protocol must have the same values for all applications "
                                      "that share the same FQDN : "
                                      "Parameter differs between '{}' and '{}'".format(app.name, first_app.name))

                if app.private_uri_is_ssl:
                    parameters['server_ssl_proxyengine'] = 'On'
                    for proto in SSL_PROTOCOLS:
                        if str(app.ssl_protocol) == str(proto[0]):
                            app.ssl_protocol = proto[1]
                    if backend_conns.get(app.private_uri) and len(backend_conns.get(app.private_uri)) > 0:
                        for old_app in backend_conns.get(app.private_uri):
                            if old_app.ssl_protocol != app.ssl_protocol:
                                conf_error.append('[TLS] - SSLProxyProtocol for application ' + str(
                                    app.name) + ' differs with application ' + old_app.name)

                            if old_app.ssl_verify_certificate != app.ssl_verify_certificate:
                                conf_error.append('[TLS] - SSLProxyVerify for application ' + str(
                                    app.name) + ' differs with application ' + old_app.name)

                            if old_app.ssl_verify_certificate_name != app.ssl_verify_certificate_name:
                                conf_error.append('[TLS] - SSLProxyCheckPeerName for application ' + str(
                                    app.name) + ' differs with application ' + old_app.name)

                            if old_app.ssl_verify_certificate_expired != app.ssl_verify_certificate_expired:
                                conf_error.append('[TLS] - SSLProxyCheckPeerExpire for application ' + str(
                                    app.name) + ' differs with  application ' + old_app.name)

                            if old_app.ssl_client_certificate != app.ssl_client_certificate:
                                conf_error.append('[TLS] - SSLProxyMachineCertificateFile for application ' + str(
                                    app.name) + ' differs with application ' + old_app.name)

                            if old_app.ssl_cipher != app.ssl_cipher:
                                conf_error.append('[TLS] - SSLProxyCipherSuite for application ' + str(
                                    app.name) + ' differs with application ' + old_app.name)
                        backend_conns[app.private_uri].append(app)
                    else:
                        backend_conns[app.private_uri] = [app]

        ret = dict()
        try:
            t = tpl_utils.get_template("vulture_httpd")[0]
            ret['config'] = t.render(conf=parameters, apps=subapps, private_uris=private_uris, svms=activated_svms)
            ret['error'] = "</br>".join(list(set(conf_error)))
        except Exception as e:
            logger.exception(e)
            ret['error'] = str(e)
        return ret

    def saveConf(self):
        """Backup an existing configuration
        """
        if os.path.isfile(self.configuration_path):
            try:
                with codecs.open(self.configuration_path, 'r', encoding='utf8') as fs:
                    content = fs.read()
                with codecs.open(self.backup_configuration_path, 'w', encoding='utf8') as fd:
                    fd.write(content)
            except Exception as e:
                logger.info("Unable to backup configuration. Reason is: " + str(e))
                logger.exception(e)
                return False
        return True

    def restoreConf(self):
        """Restore a backuped configuration, and destroy backup
        """
        if os.path.isfile(self.backup_configuration_path):
            try:
                with codecs.open(self.backup_configuration_path, 'r', encoding='utf8') as fs:
                    content = fs.read()
                with codecs.open(self.configuration_path, 'w', encoding='utf8') as fd:
                    fd.write(content)
                os.remove(self.backup_configuration_path)
            except Exception as e:
                logger.info("Unable to restore configuration. Reason is: " + str(e))
                logger.exception(e)
                return False

        return True

    @property
    def configuration_path(self):
        """ Complete path to ListenAdress configuration file

        :return: String with path
        """
        return "%s%s-%s.conf" % (settings.CONF_DIR, self.address.ip, self.port)

    @property
    def backup_configuration_path(self):
        """ Complete path to ListenAdress backup configuration file

        :return: String with path
        """
        return "%s%s-%s.conf.bak" % (settings.CONF_DIR, self.address.ip, self.port)

    def need_restart(self):
        """Compare the "on-disk" configuration with the "in-database" configuration
        :return: True or False
        """

        """ No need to do anything if is_up2date is False """
        if self.is_up2date is False:
            return True

        """ We start to check if Apache configuration file are identical """
        from gui.models.rewrite_settings import Rewrite
        rewrite_rules = Rewrite.objects()
        try:
            with codecs.open(self.configuration_path, 'r', encoding='utf8') as f:
                disk_conf = f.read()
            db_conf = self.getConf(rewrite_rules)
        except Exception as e:
            """ Update all listener that shares the same IP:port """
            listenaddress_all = ListenAddress.objects.filter(address=self.address, port=self.port)
            for l in listenaddress_all:
                l.is_up2date = False
                l.save()
            return True

        db_config = db_conf['config']
        error = db_conf['error']

        """ Configurations differs, we need to restart ListenAddress """
        if error or disk_conf != db_config:
            """ Update all listener that shares the same IP:port """
            listenaddress_all = ListenAddress.objects.filter(address=self.address, port=self.port)
            for l in listenaddress_all:
                l.is_up2date = False
                l.save()
            return True

        """ Now we check if ModSecurity policy is identical """
        apps = self.get_apps()
        for app in apps:
            for rule in app.rules_set:
                if rule.need_restart():
                    """ Update all listener that shares the same IP:port """
                    listenaddress_all = ListenAddress.objects.filter(address=self.address, port=self.port)
                    for l in listenaddress_all:
                        l.is_up2date = False
                        l.save()
                    return True

        """ Update all listener that shares the same IP:port """
        listenaddress_all = ListenAddress.objects.filter(address=self.address, port=self.port)
        for l in listenaddress_all:
            l.is_up2date = True
            l.save()

        return False

    def start(self, passphrases={}):
        """ Locally start ListenAddress on Node. Method need to be
        call after an API call

        :return: True if ListenAddress successfully started, a
        string with errors otherwise
        """
        status = net_utils.start(self.address.ip, self.port, passphrases)
        return status

    def stop(self):
        """ Locally stop ListenAddress on Node. Method need to be
        call after an API call

        :return: True if ListenAddress successfully stopped, a
        string with errors otherwise
        """
        status = net_utils.stop(self.address.ip, self.port)
        return status

    def graceful(self):
        status, error = net_utils.graceful(self.address.ip, self.port)

        return {
            'status': status,
            'error': error
        }


class Application(DynamicDocument):
    """ Vulture application model representation
    name: A friendly name for the application
    tags: Optional application's tags to filter in GUI
    type: Application type (HTTP, WS, ...)
    public_name: Internet name for the application (Apache ServerName)
    public_alias: Internet alias (Apache ServerAlias)
    public_dir: Virtual directory under which the application will be published ("/" by default)
    private_uri: The internal URI of the published application (ex: http://192.168.1.1 if type is HTTP)
    log_custom: The LogFormat for access logs
    log_level: The LogLevel for both access and error logs
    learning: The learning mode, active POST data in log
    access_mode: Whitelist or blacklist approach, based on mod_authz profile
    headers_in: Reference to incoming header rules (Request)
    headers_out: Reference to outgoing header rules (Response)
    listeners: Reference to ListenAddress under which the application will be published
    worker: Reference to a worker profile
    methods: Comma-separated list of valid HTTP Method
    enable_h2: Enable the mod_h2 support
    enable_rpc: Enable RPC over HTTP
    need_auth: The application needs authentication
    enable_oauth2: If enable, it is possible to login on the application with an OAuth2 X-Vlt-Token HTTP header
    enable_ws: If enable, let Web-Socket connexion Upgrade pass through Vulture
    tracking: If set to False, mod_vulture won't be called for this app
    template: reference to a Portal template
    self_template: reference to a Self-Service template
    enabled: If set to false, the application will not be started
    learning_template: reference to a Portal template
    auth_backend: Primary Authentication backend
    auth_backend_fallbacks: Secondary Authentication backend
    sso_capture_content: REGEX to capture content in SSO Forward Response
    sso_replace_content: REGEX to replace content in SSO Forward Response
    sso_after_post_request: URI to make a GET Request after SSO Forward
    sso_after_post_replace_content: REGEX to replace content in the GET response
    """

    APP_TYPE = (
        ('http', 'Plain Text Web Application'),
        ('https', 'TLS Web Application'),
        ('balanced', 'Balanced Application'),
        ('ftp', 'FTP Application'),
        ('fcgi', 'FCGI Application'),
        ('scgi', 'SCGI Application'),
        ('wstunnel', 'Websocket Tunnel'),
        ('ajp', 'AJP Proxy')
    )

    LOG_LEVEL = (
        ('error', 'Error'),
        ('warn', 'Warning'),
        ('notice', 'Notice'),
        ('info', 'Info'),
        ('debug', 'Debug')
    )

    AUTH_TYPE = (
        ('basic', 'Basic Authentication'),
        ('form', 'HTML Form'),
        ('kerberos', 'Kerberos Authentication')
    )

    SSO_TYPE = (
        ('basic', 'Basic Authentication'),
        ('form', 'HTML Form'),
        ('kerberos', 'Kerberos Authentication')
    )

    BASIC_MODE = (
        ('autologon', 'using AutoLogon'),
        ('learning', 'using SSO Learning'),
    )

    BASIC_METHOD = (
        ('GET', 'GET'),
        ('POST', 'POST'),
    )

    SSO_CONTENT_TYPE = (
        ('default', 'application/x-www-form-urlencoded'),
        ('multipart', 'multipart/form-data'),
        ('json', 'application/json')
    )

    _REFERENCE_FIELDS = [
        "proxy_balancer",
        "access_mode",
        "modsec_policy",
        "rules_set",
        "specific_rules_set",
        "wl_bl_rules",
        "log_custom",
        "headers_in",
        "headers_out",
        "content_rules",
        "listeners",
        "worker",
        "template",
        "otp_repository"
    ]

    name = StringField(required=True, unique=True, help_text=_('Friendly name to reference the application'))
    tags = StringField(required=False, help_text=_('Optional tags to reference the application'))
    type = StringField(required=True, choices=APP_TYPE, help_text=_('The type of the application'))
    public_name = StringField(required=True, help_text=_(
        'Public Fully Qualified Distinguisehd Name of the application (ex: \'www.example.com\')'))
    public_alias = StringField(required=False, help_text=_(
        'Public FQDN aliases of the application (ex: \'www.ex.fr, www.ex2.fr, www.example.fr\')'))
    public_dir = StringField(required=True,
                             help_text=_('Name of the virtual directory to publish the application (ex: \'/public/\')'))

    private_uri = StringField(required=True,
                              help_text=_('URI of the internal application (ex: \'https://192.168.36.1/owa/\')'))
    proxy_balancer = ReferenceField('ProxyBalancer', reverse_delete_rule=PULL,
                                    help_text=_('You can define balanced application via "Proxy Balancer" menu'))
    proxy_add_header = BooleanField(default=False, help_text=_(
        'Send the following headers to backend: X-Forwarded-For, X-Forwarded-Host and X-Forwarded-Server'))

    access_mode = ListField(ReferenceField('ModAccess', reverse_delete_rule=PULL),
                            help_text=_('Choose the appropriate network access control for your application'))

    modsec_policy = ReferenceField('ModSec', reverse_delete_rule=PULL,
                                   help_text=_('Select the WAF profile to use for protection'))

    rules_set = ListField(ReferenceField('ModSecRulesSet', reverse_delete_rule=PULL),
                          help_text=_('Rules Set for the application'))
    specific_rules_set = ListField(ReferenceField('ModSecSpecificRulesSet', reverse_delete_rule=PULL),
                                   help_text=_('Rules Set for the application, specific for an url'))

    whitelist_ips = StringField(required=False, help_text=_("Whitelist IPs"))

    wl_bl_rules = ReferenceField('ModSecRulesSet', reverse_delete_rule=PULL,
                                 help_text=_('Whitelist/Blacklist for the app'))
    block_reputation = ListField(StringField(help_text=_('Block known IP by reputation')))

    log_custom = ReferenceField('ModLog', reverse_delete_rule=PULL, required=True,
                                help_text=_('Select the format of logfiles'))
    log_level = StringField(required=True, choices=LOG_LEVEL, help_text=_(
        'LogFormat verbosity (It is recommanded to choose \'error\' in production mode)'))
    learning = BooleanField(default=False, help_text=_('Enable learning mode for Apache'))
    learning_block = BooleanField(default=False, help_text=_('Block requests in learning mode'))

    headers_in = ListField(ReferenceField('HeaderIn', reverse_delete_rule=PULL),
                           help_text=_('Add rules on incoming request headers'))
    headers_out = ListField(ReferenceField('HeaderOut', reverse_delete_rule=PULL),
                            help_text=_('Add rules on outgoing response headers'))

    content_rules = ListField(ReferenceField('ContentRule', reverse_delete_rule=PULL),
                              help_text=_('Add rules for content management'))

    listeners = ListField(ReferenceField('ListenAddress', required=True, reverse_delete_rule=PULL),
                          help_text=_('Application will be available through these listeners'))
    force_tls = BooleanField(default=False, help_text=_(
        'Automagically redirect http:// request to https:// if there is a TLS listener available'))

    enabled = BooleanField(default=True, help_text=_("Enable the application"))
    is_model = BooleanField(default=False, required=True, help_text=_("Template"))

    worker = ReferenceField('Worker', required=True, reverse_delete_rule=PULL,
                            help_text=_('Workers in charge of this application'))

    methods = StringField(required=True, default='HEAD,GET,POST', help_text=_('List of accepted HTTP methods'))
    redirect_uri = StringField(required=False, help_text=_('After successful authentication, redirect to this URI'))

    enable_h2 = BooleanField(default=False, help_text=_('Enable support of HTTP/2 protocol'))
    enable_rpc = BooleanField(default=False, help_text=_('Enable support of Microsoft RPC-Over-HTTP protocol'))

    need_auth = BooleanField(default=False, help_text=_('Check if authentication is needed to access the application'))

    enable_registration = BooleanField(default=False, help_text=_('Enable users registration'))
    group_registration = StringField(help_text=_('Group of ldap registered users'))
    update_group_registration = BooleanField(default=False, help_text=_('Update group members'))

    enable_oauth2 = BooleanField(default=False, help_text=_('If checked, Vulture Oauth2 authentication is allowed'))
    enable_stateless_oauth2 = BooleanField(default=False,
                                           help_text=_('If checked, Vulture accepts OAuth2 HTTP header as a login'))

    pw_min_len = StringField (required=False, default="6", help_text=_('Password minimal length'))
    pw_min_upper = StringField (required=False, default="1", help_text=_('Password minimal length'))
    pw_min_lower = StringField (required=False, default="1", help_text=_('Password minimal length'))
    pw_min_number = StringField (required=False, default="1", help_text=_('Password minimal length'))
    pw_min_symbol = StringField (required=False, default="1", help_text=_('Password minimal length'))

    enable_ws = BooleanField(default=False, help_text=_('If checked, Vulture accepts Web-Socket connexion upgrade'))

    tracking = BooleanField(default=True, help_text=_('If disable, Vulture won\'t give a cookie to anonymous users'))
    auth_type = StringField(required=False, choices=AUTH_TYPE, default="form",
                            help_text=_('Select the method to authenticate user'))

    template = ReferenceField('portalTemplate', required=True, reverse_delete_rule=PULL,
                              help_text=_('Select the template to use for user authentication portal'))

    override_error = BooleanField(default=False, help_text=_('Override error with template theme'))
    rewrite_cookie_path = BooleanField(default=True, help_text=_('Rewrite cookie path to application public directory'))

    auth_portal = StringField(required=False, help_text=_('URI of the authentication portal'))
    auth_backend = StringField(required=False)
    auth_backend_fallbacks = ListField(StringField(required=False))
    auth_timeout = StringField(required=False, default="900")
    auth_timeout_restart = BooleanField(default=True)
    auth_captcha = BooleanField(default=False, help_text=_('Check if human'))
    otp_repository = ReferenceField('OTPRepository', required=False, reverse_delete_rule=PULL,
                                    help_text=_('Select the OTP Repository to handle two steps authentication'))
    otp_max_retry = IntField(default=3, required=False, min_value=1, max_value=999, verbose_name=_("Retries number"),
                             help_text=_('Maximum number of OTP retries until deauthentication'))

    sso_enabled = BooleanField(default=False, help_text=_('Check if you want SSO Forward on this application'))
    sso_forward = StringField(required=False, choices=SSO_TYPE, default="form",
                              help_text=_('Select the method to propagate authentication'))
    sso_forward_basic_mode = StringField(required=False, choices=BASIC_MODE, default="autologon",
                                         help_text=_('Select the SSO Forward way to propagate credentials'))
    sso_forward_only_login = BooleanField(default=False,
                                          help_text=_('Send Basic Authorization only once, to the login URL'))
    sso_forward_basic_url = StringField(required=False, default='http://your_internal_app/action.do?what=login',
                                        help_text=_('URL of the login form'))

    sso_direct_post = BooleanField(required=False, default=False, help_text=_('Enable direct POST'))
    sso_forward_get_method = BooleanField(required=False, default=False, help_text=_('Make a GET instead of a POST'))

    app_krb_service = StringField(required=False, default='myapp.domain.com', help_text=_(
        'Kerberos service used by the app to verify token, (ex: \'HTTP@webapp.testing.tr\')'))
    app_disconnect_url = StringField(required=False, default='/disconnect', help_text=_(
        'Regex for the application disconnection page, (ex: \'/logout\?sessid=.*\')'))
    app_display_logout_message = BooleanField(default=False, help_text=_(
        'Display the "You have been successfuly disconnected" message'))
    app_disconnect_portal = BooleanField(default=False, help_text=_('Also disconnect the user from the portal'))

    sso_forward_follow_redirect_before = BooleanField(default=False, help_text=_(
        'Before posting the login form, follow the 30X redirection'))
    sso_forward_follow_redirect = BooleanField(default=False,
                                               help_text=_('After posting the login form, follow the 30X redirection'))

    sso_forward_return_post = BooleanField(default=False, help_text=_(
        'Return the application\'s response immediately after the SSO Forward Request'))
    sso_forward_content_type = StringField(required=False, choices=SSO_CONTENT_TYPE, default='default',
                                           help_text=_('Content-Type of the SSO Forward request'))
    sso_url = StringField(required=False, default='http://your_internal_app/action.do?what=login',
                          help_text=_('URL of the login form'))
    sso_vulture_agent = BooleanField(default=False,
                                     help_text=_('Override \'User-Agent\' header with Vulture User-Agent'))
    sso_profile = StringField(required=False)

    sso_capture_content_enabled = BooleanField(default=False)
    sso_capture_content = StringField(required=False, default="^REGEX to capture (content.*) in SSO Forward Response$")

    sso_replace_content_enabled = BooleanField(default=False)
    sso_replace_pattern = StringField(required=False, default="^To Be Replaced$")
    sso_replace_content = StringField(required=False, default="By previously captured '$1'/")

    sso_after_post_request_enabled = BooleanField(default=False)
    sso_after_post_request = StringField(required=False, default="http://My_Responsive_App.com/Default.aspx")

    ssl_protocol = StringField(required=False, help_text=_('The SSL protocol to use'))
    ssl_verify_certificate = BooleanField(required=False, help_text=_('Verify the remote certificate'))
    ssl_verify_certificate_name = BooleanField(required=False,
                                               help_text=_('Verify the remote certificate\'s Name and CN'))
    ssl_verify_certificate_expired = BooleanField(required=False,
                                                  help_text=_('Verify if the remote certificate expired'))
    ssl_client_certificate = StringField(required=False, help_text=_('The client side certificate'))
    ssl_cipher = StringField(required=False, default="HIGH:!MEDIUM:!LOW:!aNULL:!eNULL:!EXP:SHA1:!MD5:SSLv3:!SSLv2",
                             help_text=_('The SSL cipher suite to use'))

    timeout = StringField(required=True, default='60', help_text=_('Time to wait, in second, for backend answer'))
    disablereuse = BooleanField(default=False,
                                help_text=_('If set to "On", immediately close connection to backend after use'))
    keepalive = BooleanField(default=True, help_text=_('If set to "On", proxy will send KeepAlive to backend server'))
    ttl = StringField(required=False, default='30',
                      help_text=_('Delay in second after which an inactive connection will not be reused'))
    preserve_host = BooleanField(default=False, help_text=_('Use incoming Host header instead of backend\'s FQDN'))

    activated_svms = ListField(StringField(required=False))
    reputation = BooleanField(default=False,
                              help_text=_('If set to "On", Vulture will analyze the reputation of source IP Address'))
    geoip = BooleanField(default=False, help_text=_('If set to "On", Vulture will geo-localize source IP Address'))
    geoip_city = BooleanField(default=False, help_text=_(
        'If set to "On", Vulture will geo-localize source IP Address at the city level'))
    block_geoip = ListField(StringField(help_text=_('Block these country')))
    allow_geoip = ListField(StringField(help_text=_('Only allow these country')))

    custom_vhost = StringField(required=False, default='#Place your custom <Virtualhost> specific directives here')
    custom_location = StringField(required=False, default='#Place your custom <Location> specific directives here')
    custom_proxy = StringField(required=False, default='#Place your custom <Proxy> specific directives here')

    cookie_encryption = BooleanField(default=False,
                                     help_text=_('If set to "On", Vulture will encrypt the given backend cookies'))
    cookie_cipher = StringField(default='rc4',
                                help_text=_('The cipher Vulture will use to encrypt the backend cookies'))
    cookie_cipher_key = StringField(required=False,
                                    help_text=_('The key the Vulture cookie encryption will use'))
    cookie_cipher_iv = StringField(required=False,
                                   help_text=_('The iv the Vulture cookie encryption will use'))
    forward_x509_fields = BooleanField(default=False,
                                       help_text=_('If set to "On", Vulture will forward X509 certificate attributes as headers for the backend'))
    enable_proxy_protocol = BooleanField(default=False,
                                         help_text=_('Enables or disables the reading and handling of the PROXY protocol connection header.'))

    def full_dump(self):
        """ perform a full (with all fields) dump of an application (faster than dump(self) for that case) """
        try:
            json_object = self.to_json()
            to_return = json.loads(json_object)

            try:
                to_return["_id"] = to_return["_id"]["$oid"]
            except:
                to_return["_id"] = None

            to_return["log_custom"] = str(self.log_custom)
            to_return["template"] = str(self.template)
            to_return["modsec_policy"] = str(self.modsec_policy)
            to_return["worker"] = str(self.worker)
            to_return["wl_bl_rules"] = str(self.wl_bl_rules)
            to_return["headers_in"] = self.get_headers("in")
            to_return["headers_out"] = self.get_headers("out")
            to_return["auth_backend"] = str(self.getAuthBackend())

            rule_set_list = []

            for rule_set in self.rules_set:
                rule_set = str(rule_set)
                rule_set_list.append(rule_set)

            to_return["rules_set"] = rule_set_list

            listener_list = []

            for listener in self.listeners:
                address_list = str(listener.address).split(" - ")

                listener_list.append({
                    "host": address_list[0],
                    "address": address_list[1],
                    "port": listener.port,
                    "redirect_port": listener.redirect_port,
                    "ssl_profile": listener.ssl_profile,
                    "is_up2date": listener.is_up2date,
                    "_id": str(listener.id)
                })

            to_return["listeners"] = listener_list

            return to_return

        except Exception as error:
            logger.exception(error)

            raise error

    @staticmethod
    def generate(descr, is_reload):
        """ generate an application with the description given """
        try:
            if descr['is_model'] and descr['enabled']:
                raise Exception("An application cannot be a model and enabled at the same time")
        except KeyError:
            pass

        try:
            try:
                model_name = descr["model"]
            except KeyError as error:  # we cannot generate an application without a model... yet
                logger.exception(error)

                raise Exception("A model has to be provided")

            del descr['model']  # remove "model" key to prevent it from being copied

            try:
                model = Application.objects.get(name=model_name)
            except:
                raise Exception("Unknown model")

            if not model.is_model:
                raise Exception("Application given is not a model")

            # we clone the new app as a model (preventing it from being saved, each field not being checked yet)
            # if a name is not given (None), a default one will be generated in the clone function
            new_app = model.clone(is_model=True, cloned_name=descr.get("name", None))

            # by default, an app copied from a model is not a model itself. It's up to the user to ask it so
            new_app.is_model = False

            # will set each field accordingly, depending if it is a list or not
            new_app._set_fields(descr)

            new_app.save()

            if is_reload:
                from api.views.network import reloadListener  # to fix: import is here because of circular dependencies

                for listener in new_app.listeners:
                    reloadListener(None, listener.id)

            return
        except Exception as error:
            logger.exception(error)

            raise error

    @staticmethod
    def get_app_by_name(app_name):
        """ return an application with a name given """
        try:
            return Application.objects.get(name=app_name)
        except Exception as error:
            logger.exception(error)

            raise error

    @staticmethod
    def get_apps_by_regex(regex):
        """ return one or several application(s) with a regex given """
        try:
            regex = re.compile(regex)

            return Application.objects(__raw__={
                'name': {
                    '$regex': regex.pattern
                }
            })
        except Exception as error:
            logger.exception(error)

            raise error

    def dump(self, fields=None):
        """ return a dump of the application properly formatted """
        try:
            if fields is None:  # by default, if no fields are returned, all attributes are displayed
                # it could be done better... self.to_json() is used here to get all attributes to dump. Maybe there is
                # a better way to do it?
                # fields = json.loads(self.to_json()).keys()
                return self.full_dump()

            to_return = {}

            for field in fields:
                to_return[field] = self._get_field(field)

            return to_return

        except Exception as error:
            logger.exception(error)

            raise error

    def _get_field(self, field):
        """ return a given field properly formatted """
        field = str(field)

        if field == "rules_set":
            rule_set_list = []

            for rule_set in self.rules_set:
                rule_set_list.append({
                    "_id": str(rule_set.id),
                    "rule_set": str(rule_set)}
                )

            return rule_set_list
        elif field == "listeners":
            listener_list = []

            for listener in self.listeners:
                address_list = str(listener.address).split(" - ")

                listener_list.append({
                    "host": address_list[0],
                    "address": address_list[1],
                    "port": listener.port,
                    "redirect_port": listener.redirect_port,
                    "ssl_profile": listener.ssl_profile,
                    "is_up2date": listener.is_up2date,
                    "_id": str(listener.id)
                })

            return listener_list
        elif field == "_id":
            return str(self.id)
        elif field == "headers_out":
            return self.get_headers("out")
        elif field == "headers_in":
            return self.get_headers("in")
        else:
            try:
                attr = getattr(self, field)

                if isinstance(attr, BaseList):
                    to_return = []

                    for item in getattr(self, field):
                        try:  # adding an _id attribute for reference fields
                            to_return.append({
                                "_id": str(item.id),
                                field: str(item)
                            })
                        except:
                            to_return.append(item)

                    return to_return

                try:  # adding an _id attribute for reference fields
                    attr = {
                        "_id": str(attr.id),
                        field: str(attr)
                    }
                except:  # not a reference field
                    pass
            except Exception as error:
                attr = {
                    field: str(error)
                }

            return attr

    def delete_listeners(self):
        """ delete all listeners of the application. Stop them if there are no longer needed """
        for listener in self.listeners:
            listener.delete()

            # if the listener is no longer needed, we stop it
            if not len(listener.get_apps()):
                listener.stop()

    def clone(self, is_model=False, cloned_name=None):
        """ clone the application """
        new_app_headers_in = list()
        headers_in = self.headers_in

        for header_in in headers_in:
            header_in.pk = None
            header_in.save()
            new_app_headers_in.append(header_in)

        new_app_headers_out = list()
        headers_out = self.headers_out

        for headers_out in headers_out:
            headers_out.pk = None
            headers_out.save()
            new_app_headers_out.append(headers_out)

        new_app_content_rules = list()
        content_rules = self.content_rules

        for content_rule in content_rules:
            content_rule.pk = None
            content_rule.save()
            new_app_content_rules.append(content_rule)

        new_app_listeners = list()
        listeners = self.listeners

        for listener in listeners:
            listener.pk = None
            listener.is_up2date = False
            listener.save()
            new_app_listeners.append(listener)

        new_app = copy.deepcopy(self)

        new_app.pk = None

        if cloned_name is None:  # default name generated
            new_app.name = str(self.name) + '_copy_' + get_random_string(4)
        else:
            new_app.name = cloned_name

        new_app.headers_in = new_app_headers_in
        new_app.headers_out = new_app_headers_out
        new_app.content_rules = new_app_content_rules
        new_app.listeners = new_app_listeners

        modsec_wl_bl = ModSecRulesSet(name="{} whitelist/blacklist".format(new_app.name), type_rule="wlbl")
        modsec_wl_bl.save()
        modsec_wl_bl.conf = modsec_wl_bl.get_conf()
        modsec_wl_bl.save()

        new_app.wl_bl_rules = modsec_wl_bl

        if not is_model:
            new_app.save()

        return new_app

    def update(self, descr):
        """ update the application """
        descr["is_model"] = descr.get("is_model", self.is_model)
        descr["enabled"] = descr.get("enabled", self.enabled)

        # check the values of is_model and enabled when the app will be created
        # both cannot be set to True at the same time, which would mean an app can be both a model and a regular app
        if descr["is_model"] and descr["enabled"]:
            raise Exception("An application cannot be a model and enabled at the same time")

        try:
            self._set_fields(descr)
            self.save()
        except Exception as error:
            logger.exception(error)

            raise error

    def _set_fields(self, descr):
        """ set all fields (name, public_dir, etc.) for an application given a description """
        for field in descr:
            value = getattr(self, field)

            if field == "name":
                descr[field] = descr[field].strip()
                match = re.search(r"^[\w #]+$", descr[field])

                if not match:
                    raise Exception("Please provide a valid name")

                # updating the WL/BL rules name as well
                self.wl_bl_rules.name = "{} whitelist/blacklist".format(descr[field])
                self.wl_bl_rules.save()

            if field in Application._REFERENCE_FIELDS:  # ReferenceFields are not yet supported
                raise Exception("Reference fields modifiers are not implemented yet")

            if isinstance(value, BaseList):  # each item in the list will be updated
                new_list = [item for item in descr[field]]
                setattr(self, field, new_list)
            else:
                setattr(self, field, descr[field])

    def destroy(self):
        """ destroy the application """
        for header_in in self.headers_in:
            header_in.delete()

        for header_out in self.headers_out:
            header_out.delete()

        self.delete_listeners()

        for content_rule in self.content_rules:
            content_rule.delete()

        if self.wl_bl_rules:
            wl_bl_rules = self.wl_bl_rules
        else:
            wl_bl_rules = None

        done = list()

        for listener in self.listeners:
            key = listener.address.ip + ':' + str(listener.port)
            if key not in done:
                listener.need_restart()
                done.append(key)

        self.delete()

        if wl_bl_rules:
            for rule in ModSecRules.objects.filter(rs=wl_bl_rules):
                rule.delete()
            wl_bl_rules.delete()

        try:
            client = ReplicaSetClient()

        except ReplicaConnectionFailure as e:
            logger.error("Failed to connect to ReplicaSet while trying to "
                         "create 'learning_{}' collection".format(str(self.id)))
            logger.exception(e)
            return

        result, error = client.execute_command("printjson(db.learning_{}.drop())".format(str(self.id)), database="logs")

        if error:
            logger.error("Error while trying to drop collection 'learning_{}' : {}".format(str(self.id), error))
        # drop() returns true ou false
        elif not result:
            logger.error("Error while trying to drop collection 'learning_{}', maybe it does not exists".format(str(self.id)))
        else:
            logger.info("Learning collection 'learning_{}' successfully dropped".format(str(self.id)))


    def get_rules(self):
        """ return the apache configuration for content management """
        buffer = ""
        tab = "\t"
        outputfilters = list()
        first_output_filter = True
        for rule in self.content_rules:
            if not rule.enable:
                continue

            """ useless rule """
            if not rule.pattern and not rule.inflate and not rule.deflate:
                continue

            flt = list()
            if rule.inflate:
                flt.append("INFLATE")
                if "INFLATE" not in outputfilters:
                    outputfilters.append("INFLATE")
            if rule.pattern:
                flt.append("SUBSTITUTE")
                if "SUBSTITUTE" not in outputfilters:
                    outputfilters.append("SUBSTITUTE")
            if rule.deflate:
                flt.append("DEFLATE")
                if "DEFLATE" not in outputfilters:
                    outputfilters.append("DEFLATE")
            flt = ";".join(flt)

            if rule.condition:
                buffer += "<If \"{}\"> \n".format(rule.condition)
                tab = "\t\t"

            if not rule.types:
                if first_output_filter:
                    first_output_filter = False
                    buffer = buffer + tab + 'SetOutputFilter %%flt%% \n'

                if rule.pattern:
                    rule_regex = tab + 'Substitute "s|'
                    # Escaping search pattern quotes and pipes
                    rule_regex += rule.pattern.replace('"', '\\"').replace('|', '\|')
                    rule_regex += '|'
                    # Escaping replacement quotes and pipes
                    rule_regex += rule.replacement.replace('"', '\\"').replace('|', '\|')
                    rule_regex += '|'
                    # Adding substitute flags
                    rule_regex += rule.flags.replace(',', '') + '"'
                    buffer = buffer + rule_regex + "\n"
            else:
                buffer = buffer + tab + 'AddOutputFilterByType {} {}'.format(flt, rule.types.replace(",", " ")) + "\n"
                if rule.pattern:
                    rule_regex = tab + 'Substitute "s|'
                    # Escaping search pattern quotes and pipes
                    rule_regex += rule.pattern.replace('"', '\\"').replace('|', '\|')
                    rule_regex += '|'
                    # Escaping replacement quotes and pipes
                    rule_regex += rule.replacement.replace('"', '\\"').replace('|', '\|')
                    rule_regex += '|'
                    # Adding substitute flags
                    rule_regex += rule.flags.replace(',', '') + '"'
                    buffer = buffer + rule_regex + "\n"
            tab = "\t"

            if rule.condition:
                buffer = buffer + tab + "</If>\n"

        outputfilters_sorted = list()
        if "INFLATE" in outputfilters:
            outputfilters_sorted.append("INFLATE")
        if "SUBSTITUTE" in outputfilters:
            outputfilters_sorted.append("SUBSTITUTE")
        if "DEFLATE" in outputfilters:
            outputfilters_sorted.append("DEFLATE")

        return buffer.replace("%%flt%%", ';'.join(outputfilters_sorted))

    def getAuthBackend(self):
        """Return the main Authentication backend"""
        from gui.models import repository_settings
        return repository_settings.BaseAbstractRepository.search_repository(ObjectId(self.auth_backend))

    def getAuthBackendFallback(self):
        """Return the fallback Authentication backend"""
        from gui.models import repository_settings
        return [repository_settings.BaseAbstractRepository.search_repository(ObjectId(object_id)) for object_id in
                self.auth_backend_fallbacks]

    def private_uri_is_ssl(self):
        """Return True if private_uri is SSL or False otherwise"""
        if str(self.private_uri)[:6] == "https:":
            return True

        """ Before returning False, check if there is an HTTPS balanced member """
        if self.proxy_balancer:
            for member in self.proxy_balancer.members:
                if member.uri_type == "https":
                    return True
        return False

    def private_uri_fqdn(self):
        """Return the private application name"""
        return get_uri_fqdn_without_scheme(self.private_uri)

    def private_uri_path(self):
        """Return the path of the private uri"""
        path = get_uri_path(self.private_uri)
        if path == self.private_uri:
            return '/'
        return path

    def need_passphrase(self):
        """ Return True if the application as a TLS listener that require a
        passphrase for private Key

        :return:
        """
        if len(self.get_ssl_profiles(True)) > 0:
            return True
        return False

    def get_ssl_profiles(self, only_with_passphrase=True):
        """ Return list of ModSSL object used by this application

        :param only_with_passphrase: Boolean used to retrieve only SSL
        Profile with passphrase
        :return: A list of ModSSL object
        """
        ssl_profiles = []
        for l in self.listeners:
            if l.ssl_profile:
                if not only_with_passphrase:
                    ssl_profiles.append(l.ssl_profile)
                else:
                    m = re.search('ENCRYPTED', l.ssl_profile.certificate.key)
                    if m is not None:
                        ssl_profiles.append(l.ssl_profile)
        return ssl_profiles

    def get_protected_ssl_profiles(self):
        """ Wrapper of get_ssl_profiles(True), needed because we can't call
        get_ssl_profiles with arguments into Django Template

        :return: List of ModSSL object with a passphrase
        """
        return self.get_ssl_profiles(True)

    """ Return True if the application as, at least, one TLS listener """

    def has_tls(self):
        for l in self.listeners:
            if l.ssl_profile:
                return True
        return False

    """ Return the prefered URL for redirection to this app """

    def get_redirect_uri(self):

        """ Take the first listener in list """
        listener = None
        for l in self.listeners:
            """ TLS priority """
            if l.ssl_profile:
                listener = l

        if not listener:
            listener = self.listeners[0]

        redirect_port = listener.redirect_port
        if redirect_port:
            port = redirect_port
        else:
            port = listener.port

        if listener.ssl_profile:
            if port == "443":
                url = "https://" + str(self.public_name) + str(self.public_dir)
            else:
                url = "https://" + str(self.public_name) + ":" + str(port) + str(self.public_dir)
        else:
            if port == "80":
                url = "http://" + str(self.public_name) + str(self.public_dir)
            else:
                url = "http://" + str(self.public_name) + ":" + str(port) + str(self.public_dir)
        return url

    def get_app_disconnect_url(self):
        return self.app_disconnect_url

    def get_methods(self, config=None):
        """ Returns accepted HTTP VERBS
        :param: if config is True, format the output for vulture_httpd.conf
        """
        ret = ""

        if config:
            return "|".join(self.methods.split(','))

        for s in self.methods.split(','):
            ret = ret + '"' + s + '",'

        return ret[:-1]

    def get_headers(self, direction):
        """ Returns incoming / outgoing headers policy

        :param direction: in or out
        :return:
        """
        if direction is None:
            return None
        if str(direction) == "out":
            headers = self.headers_out
            directive = "Header"
        else:
            headers = self.headers_in
            directive = "RequestHeader"

        if headers is None:
            return None

        ret = ""
        first = True
        for header in headers:
            if not header.enable:
                continue

            if not first:
                ret = ret + '    ' + directive + " " + str(header.action) + " " + str(header.name)
            else:
                ret = ret + directive + " " + str(header.action) + " " + str(header.name)
            if header.value:
                ret = ret + " \"" + header.value + "\""
            if header.replacement or header.action in ('edit', 'edit*'):
                ret = ret + " \"" + header.replacement + "\""
            if header.condition and str(header.condition) == "satisfy" and header.condition_v:
                ret = ret + " " + "\"expr=" + str(header.condition_v) + "\""
            elif header.condition and str(header.condition) == "env_exists" and header.condition_v:
                ret = ret + " " + "env=\"" + str(header.condition_v) + "\""
            elif header.condition and str(header.condition) == "env_not_exists" and header.condition_v:
                ret = ret + " " + "env=\"!" + str(header.condition_v) + "\""

            ret += "\n\t"
            first = None

        return ret


    """Returns proxy_balancer Expression to check backend's availability """
    def get_proxy_balancer_hcexpr(self):

        if self.proxy_balancer:
            balancer = self.proxy_balancer

            if balancer.hcexpr == "hc(\'body\') !~" or balancer.hcexpr == "hc(\'body\') =~":
                return "ProxyHCExpr " + str(balancer.id)[-15:] + " {" + balancer.hcexpr + "/" + balancer.hcexpr_data + "/" + "} \n"
            else:
                return "ProxyHCExpr " + str(balancer.id)[-15:] + " " + balancer.hcexpr + "\n"

    """Returns proxy_balancer configuration or None, if there is a valid proxy_balancer configuration """
    def get_proxy_balancer(self):
        if self.proxy_balancer:
            balancer = self.proxy_balancer
            ret = "    ##### ProxyBalancer Definition - \"" + str(balancer.name) + "\" #####\n"
            proxyset = "\t" + "ProxySet lbmethod=" + str(balancer.lbmethod)
            if balancer.stickysession:
                proxyset = proxyset + " stickysession=" + str(balancer.stickysession)
            if balancer.stickysessionsep:
                proxyset = proxyset + " stickysessionsep=" + str(balancer.stickysessionsep)
            if balancer.config:
                proxyset = proxyset + " " + str(balancer.config).replace(',', ' ')

            ret = ret + proxyset + "\n"

            healthcheck=""
            try:
                if balancer.hcmethod and balancer.hcmethod != "None":
                    healthcheck="hcmethod="+balancer.hcmethod

                if balancer.hcmethod in ["OPTIONS","HEAD","GET"] and balancer.hcuri:
                    healthcheck = healthcheck + " " + "hcuri=" + str(balancer.hcuri)

                if balancer.hcmethod and balancer.hcmethod != "None" and balancer.hcpasses:
                    healthcheck = healthcheck + " " + "hcpasses=" + str(balancer.hcpasses)

                if balancer.hcmethod and balancer.hcmethod != "None" and balancer.hcfails:
                    healthcheck = healthcheck + " " + "hcfails=" + str(balancer.hcfails)

                if balancer.hcmethod and balancer.hcmethod != "None" and balancer.hcinterval:
                    healthcheck = healthcheck + " " + "hcinterval=" + str(balancer.hcinterval)

                if balancer.hcmethod in ["OPTIONS","HEAD","GET"] and balancer.hcexpr:
                    healthcheck = healthcheck + " " + "hcexpr=" + str(balancer.id)[-15:]

            except:
                pass

            balancer_members = ""
            if balancer.members:
                for member in balancer.members:
                    balancer_members += "\tBalancerMember "
                    balancer_members += str(member.uri_type)
                    balancer_members += "://" + str(member.uri)
                    if member.disablereuse:
                        balancer_members += " disablereuse=On"
                    else:
                        balancer_members += " disablereuse=Off"
                    if member.keepalive:
                        balancer_members += " keepalive=On"
                    else:
                        balancer_members += " keepalive=Off"
                    if member.lbset and member.lbset != "none":
                        balancer_members += " lbset=" + str(member.lbset)
                    if member.retry and member.retry != "none":
                        balancer_members += " retry=" + str(member.retry)
                    if member.route and member.route != "none":
                        balancer_members += " route=" + str(member.route)
                    if member.timeout and member.timeout != "none":
                        balancer_members += " timeout=" + str(member.timeout)
                    if member.ttl and member.ttl != "none":
                        balancer_members += " ttl=" + str(member.ttl)
                    if member.config:
                        balancer_members += " " + str(member.config).replace(",", " ")

                    balancer_members += " " + healthcheck + " " + "\n"

            ret += balancer_members
            return ret + "        ##### End of ProxyBalancer Definition #####"

        return None

    def get_modsec_dos_rules(self):
        res = []
        try:
            for dos_rule in self.modsec_policy.dos_rules:
                if dos_rule.enable:
                    res.append(dos_rule)
        except:
            pass
        return res

    @property
    def access_logpath(self):
        """ Return Application access log path

        :return: String with complete path to Application's access logs
        """
        return "/var/log/Vulture/worker/vulture-{}-{}-access.log".format(self.public_name,
                                                                         self.public_dir.replace('/', ''))

    @property
    def security_logpath(self):
        """ Return Application security log path

        :return: String with complete path to Application's access logs
        """
        return "/var/log/Vulture/worker/vulture-{}-{}-security.log".format(self.public_name,
                                                                           self.public_dir.replace('/', ''))

    @property
    def security_debug_logpath(self):
        """ Return Application security log path

        :return: String with complete path to Application's access logs
        """
        return "/var/log/Vulture/worker/vulture-{}-{}-security-debug.log".format(self.public_name,
                                                                                 self.public_dir.replace('/', ''))

    def prepare_learning_collection(self):
        try:
            client  = ReplicaSetClient()

        except ReplicaConnectionFailure as e:
            logger.error("Failed to connect to ReplicaSet while trying to "
                         "create 'learning_{}' collection".format(str(self.id)))
            logger.exception(e)
            return

        result, error = client.execute_command("printjson(db.learning_{}."
                                               "createIndex({{context_id : 1}}, unique=true))"
                                               .format(str(self.id)), database="logs")
        if error:
            logger.error("Error while creating index named 'learning_{}' : {}".format(self.id, error))
        elif result.get('errmsg'):
            logger.error("Error while creating index named 'learning_{}' : {}".format(self.id, result))
        else:
            logger.info("Collection/Index successfully created : 'learning_{}'".format(str(self.id)))

    def get_sso_urls(self):
        """ Return a list of urls, according to backend and SSO url """
        result = []
        """ If SSO Forward disabled """
        if not self.sso_enabled:
            logger.error("SSO Forward is not enabled !")
            return result
        base_url = ""
        """ If send authorization header only to the login page """
        if self.sso_forward in ["basic", "kerberos"] and self.sso_forward_only_login:
            base_url = self.sso_forward_basic_url
        elif self.sso_forward == "form":
            base_url = self.sso_url
        """ If not sso url was specified, use backend url(s) """
        """ If sso url was specified but no "[]" in it, use sso_url """
        """ If sso url was specified and "[]" in it, replace [] by backend(s) uri """
        if not base_url:
            if self.type == "balanced":
                for member in self.proxy_balancer.members:
                    result.append("{}://{}".format(member.uri_type, member.uri))
            else:
                result.append(self.private_uri)
        elif "[]" not in base_url:
            result.append(base_url.replace("\[", '[').replace("\]", ']'))
        else:
            def build_url(backend_url):
                return base_url.replace("[]", backend_url).replace("\[", '[').replace("\]", ']')
            if self.type == "balanced":
                for member in self.proxy_balancer.members:
                    result.append(build_url("{}://{}".format(member.uri_type, member.uri.split('/')[0])))
            else:
                result.append(build_url(self.private_uri))
        return result

    def get_sso_profile(self, login, field_name):
        """ Return value of sso_profile, associated to the principal repository, to a login and a field """
        auth_backend = self.getAuthBackend()
        for sso in SSOProfile.objects.filter(app_id=str(self.id),
                                             repo_id=str(auth_backend.id),
                                             login=login):
            decrypted_value = sso.get_data(sso.encrypted_value, str(self.id),
                                           str(auth_backend.id), str(login),
                                           str(field_name))
            if decrypted_value is not None:
                return decrypted_value
        return None

    def get_sso_profiles(self, login, insecure=False):
        """ Return all sso_profiles associated to the principal repository and to the provided login 
        :return a dict 
        """
        result = {}
        # Retrieve to wizard to get all fields associated to those SSOProfiles
        if self.sso_forward == "basic":
            sso_profiles_app = [{'type': "learn", 'name': "basic_username;vlt;", 'asked_name': "username"},
                                {'type': "learn_secret", 'name': "basic_password;vlt;", 'asked_name': "password"}]
        elif self.sso_forward == "kerberos":
            sso_profiles_app = [{'type': "learn", 'name': "kerberos_username;vlt;", 'asked_name': "username"},
                                {'type': "learn_secret", 'name': "kerberos_password;vlt;", 'asked_name': "password"}]
        else:
            sso_profiles_app = json.loads(self.sso_profile)
        for sso_profile_app in sso_profiles_app:
            if sso_profile_app['type'] in ("learn", "learn_secret"):
                field_name = sso_profile_app['name'].split(';vlt;')[0]
                logger.info(field_name)
                field_value = self.get_sso_profile(login, field_name)
                if field_value is None:
                    continue
                if sso_profile_app.get('asked_name'):
                    field_name = sso_profile_app.get('asked_name')
                # If secret (password), replace chars by *
                if sso_profile_app['type'] == "learn_secret" and not insecure:
                    result[field_name] = "*" * len(field_value)
                else:
                    result[field_name] = field_value
        return result

    def get_all_sso_profiles(self, insecure=False):
        """ Return all sso_profiles associated to the principal repository
        :return a list [{'login': xxx, 'sso_profile': {xxx}}, xxx] """
        result = []
        # Retrieve all logins
        logins = SSOProfile.objects.filter(app_id=str(self.id), repo_id=str(self.getAuthBackend().id)).distinct('login')
        for login in logins:
            try:
                result.append({'login': login, 'sso_profiles': self.get_sso_profiles(login, insecure=insecure)})
            except:
                continue
        return result

    def set_sso_profile(self, login, field_name, field_value):
        """ Create or update a new SSOProfile object """
        auth_backend = self.getAuthBackend()
        sso_profile = False
        for sso in SSOProfile.objects.filter(app_id=str(self.id), repo_id=str(auth_backend.id), login=login):
            if sso.get_data(sso.encrypted_value, str(self.id), str(auth_backend.id), str(login),
                            field_name):
                sso_profile = sso
                break
        if not sso_profile:
            sso_profile = SSOProfile()
        sso_profile.set_data(str(self.id), self.name, str(auth_backend.id), str(auth_backend.repo_name),
                             str(login), field_name, field_value)
        sso_profile.store()

    def set_sso_profiles(self, login, new_sso_profiles):
        """ Create or update all sso_profiles associated to a login and to the principal repository
        :return
        :Raise an error if any failure
        """
        # Update/create asked SSOProfiles
        for field_name, field_value in new_sso_profiles.items():
            self.set_sso_profile(login, field_name, field_value)

    def delete_sso_profile(self, login):
        """ Delete SSOProfiles associated to a login and to the principal repository 
        Can raise an exception if failure
        """
        sso_profiles_app = json.loads(self.sso_profile)
        auth_backend = self.getAuthBackend()
        for sso_profile_app in sso_profiles_app:
            if sso_profile_app['type'] in ("learn", "learn_secret"):
                field_name = sso_profile_app['name'].split(';vlt;')[0]
                for sso_profile in SSOProfile.objects.filter(app_id=str(self.id),
                                                             repo_id=str(auth_backend.id),
                                                             login=login):
                    sso_profile.delete()

    def save(self, *args, **kwargs):
        super(Application, self).save(*args, **kwargs)

        # Checking if learning is active
        # If active, creating learning collection
        if self.learning:
            try:
                self.prepare_learning_collection()
            except Exception as error:
                logger.exception(error)

        no_api = kwargs.get('no_apicall') or False
        if not no_api:
            app_modified.send(sender=self.__class__)

    def __str__(self):
        return "{}".format(self.name + ' [ Type = ' + self.type + ' ]')


class UpdateException(Exception):
    def __init__(self):
        pass
