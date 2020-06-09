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
__doc__ = 'Django models dedicated to cluster and system settings'

import collections
import json
import logging
import requests

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

api_logger = logging.getLogger('api')

from mongoengine import ObjectIdField, FloatField, StringField, BooleanField, IntField, ListField, EmbeddedDocument, EmbeddedDocumentField, DynamicDocument, DynamicEmbeddedDocument, ReferenceField, PULL
from gui.signals.gui_signals import node_modified, cluster_modified
from gui.models.network_settings import Interface, Listener
from gui.models.ssl_certificate import SSLCertificate
from gui.models.repository_settings import BaseAbstractRepository
from vulture_toolkit.system import ssl_utils
from vulture_toolkit.network import net_utils
from vulture_toolkit.system.replica_set_client import ReplicaSetClient
from gui.models.agents_settings import ZabbixAgent

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager
from requests import Session, Request
import ssl
import subprocess


class SSLAdapter(HTTPAdapter):
    """ "Transport adapter" that allows us to use TLSv1 """
    def __init__(self, ssl_version=None, **kwargs):
        self.ssl_version = ssl_version
        super(SSLAdapter, self).__init__(**kwargs)

    def init_poolmanager(self, connections, maxsize, block=False):
         self.poolmanager = PoolManager(num_pools=connections, maxsize=maxsize, block=block, ssl_version=self.ssl_version)


class NTPSettings(DynamicEmbeddedDocument):
    server_address_1 = StringField(default='0.freebsd.pool.ntp.org',
                                   help_text=_("NTP Server must be DNS "
                                               "resolvable by node"))
    server_address_2 = StringField(default='1.freebsd.pool.ntp.org',
                                   help_text=_("NTP Server must be DNS "
                                               "resolvable by node"))
    server_address_3 = StringField(default='2.freebsd.pool.ntp.org',
                                   help_text=_("NTP Server must be DNS "
                                               "resolvable by node"))
    server_address_4 = StringField(default='3.freebsd.pool.ntp.org',
                                   help_text=_("NTP Server must be DNS "
                                               "resolvable by node"))
    cluster_based_conf = BooleanField(default=True)

    def to_template(self):
        """Dictionary used to create configuration file. Key 'srv_list' contains
        list of NTP servers

        :return: Dictionary of configuration parameters
        """
        srv_lst = list()
        srv_lst.append(self.server_address_1)
        srv_lst.append(self.server_address_2)
        srv_lst.append(self.server_address_3)
        srv_lst.append(self.server_address_4)
        srv_lst = list(filter(None, srv_lst))
        ntp_settings = {'srv_list': srv_lst}
        return ntp_settings


class DNSSettings(DynamicEmbeddedDocument):
    dns_domain = StringField(help_text=_("Search list for hostname lookup"))
    server_address_1 = StringField(help_text=_("IP address of DNS server #1"))
    server_address_2 = StringField(help_text=_("IP address of DNS server #2"))
    server_address_3 = StringField(help_text=_("IP address of DNS server #3"))
    cluster_based_conf = BooleanField(default=True)

    def to_template(self):
        """ Return the list of DNS server after filtering None values

        :returns: Python list of DNS servers
        """
        srv_lst = list()
        srv_lst.append(self.server_address_1)
        srv_lst.append(self.server_address_2)
        srv_lst.append(self.server_address_3)
        srv_lst = list(filter(None, srv_lst))
        dns_settings = self.to_mongo()
        dns_settings['srv_list'] = srv_lst
        return dns_settings


class SMTPSettings(DynamicEmbeddedDocument):
    domain_name = StringField(help_text=_("The internet domain name of your mail"
                                          " system  (ex: example.org)."))
    """
    origin_name = StringField(help_text=_("The domain name that locally-posted "
                                          "mail appears to come from, and that "
                                          "locally posted mail is delivered to."))
    relay_host = StringField(help_text=_("The next-hop destination of non-local"
                                         " mail."))
    """
    smtp_server = StringField(verbose_name=_("Server"),
                              help_text=_("Name of SMTP Server where Vulture "
                                          "will transmit mails"))
    cluster_based_conf = BooleanField(default=True)

    def to_template(self):
        """ Dictionary used to create configuration file.

        :return: Dictionary of configuration parameters
        """
        smtp_settings = self.to_mongo()
        smtp_settings['hostname'] = net_utils.get_hostname()
        return smtp_settings

class IPSECSettings(DynamicEmbeddedDocument):

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


    enabled             = BooleanField(default=False)
    ipsec_type          = StringField(default="tunnel")
    ipsec_keyexchange   = StringField(choices=KEYEXCHANGE,default="ikev2")
    ipsec_authby        = StringField(choices=AUTHBY, default="secret")
    ipsec_psk           = StringField(default="V3ryStr0ngP@ssphr@se")
    ipsec_fragmentation = BooleanField(default=True)
    ipsec_forceencaps   = BooleanField(default=False)
    ipsec_ike           = StringField(default="aes256-sha512-modp8192")
    ipsec_esp           = StringField(default="aes256-sha512-modp8192")
    ipsec_dpdaction     = StringField(choices=DPD, default="restart")
    ipsec_dpddelay      = StringField(default="35s")
    ipsec_rekey         = BooleanField(default=True)
    ipsec_ikelifetime   = StringField(default="3h")
    ipsec_keylife       = StringField(default="1h")
    ipsec_right         = StringField(default="")
    ipsec_leftsubnet    = StringField(default="")
    ipsec_leftid        = StringField(default="")
    ipsec_rightsubnet   = StringField(default="")


    def to_template(self):
        """ Dictionary used to create configuration file.

        :return: Dictionary of configuration parameters
        """
        ipsec_settings = self.to_mongo()
        ipsec_settings['hostname'] = net_utils.get_hostname()
        return ipsec_settings

class GLOBALSettings(DynamicEmbeddedDocument):
    LOGROTATE_LIST = (
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly')
    )

    owasp_crs_url = StringField(default="https://github.com/SpiderLabs/owasp-modsecurity-crs/archive/v3.0/master.zip",
                                help_text=_("URL to download OWASP CRS for ModSecurity"))
    trustwave_url = StringField(
        default="https://www.modsecurity.org/autoupdate/repository/modsecurity-slr/slr_vuln_latest/slr_vuln_latest_1.0.0.zip",
        help_text=_("URL to download Trustwave rules for ModSecurity"))
    trustwave_user = StringField(default="", help_text=_("Trustwave Authentication Header"))
    source_branch = StringField(help_text=_("Name of the Vulture source code branch. Leave it empty for community edition"), default="")
    portal_cookie = StringField(help_text=_("Name of Vulture's Portal Cookie"))
    app_cookie = StringField(help_text=_("Name of Vulture's Application Cookie"))
    public_token = StringField(help_text=_("Name of Vulture's Public Token used in redirection URL"))
    redis_pwd = StringField()
    logs_repository = ObjectIdField()
    log_rotate = IntField(default=0, help_text=_('Lifetime of logs inside the internal MongoDB Repository'))
    file_logrotate = StringField(choices=LOGROTATE_LIST, required=True, default=30, help_text=_("Rotate frequency for logs file"))
    keep_logs = IntField(required=True, help_text=_("Count time before delete logs files. Ex: logrotate: daily, keep logs: 30 (Logs files will be saved for 30 days)"))
    city_name = StringField()
    latitude = FloatField()
    longitude = FloatField()
    gui_timeout = IntField(required=False, default=5, help_text=_("Disconnect GUI users after X minutes"))
    x_vlt_token = StringField (default='X-Vlt-Token', help_text=_("Name of the HTTP header used to get the user's OAuth2 token"))
    remote_ip_internal_proxy = ListField(required=False, default=[], help_text=_("Trusted IP for which X-Forwarded-For is acceptable"))
    vulture_status_ip_allowed = ListField(StringField(), required=False, default=[], help_text=_("Trusted IP for which Vulture will grant access to Apache Status"))

    def to_template(self):
        """Dictionary used to create configuration file.

        :return: Dictionary of configuration parameters
        """
        global_settings = self.to_mongo()
        return global_settings

    @property
    def repository(self):
        """ Property used to map repository field to Repository Object

        :return:
        """
        return BaseAbstractRepository.search_repository(self.logs_repository)


class SSHSettings(DynamicEmbeddedDocument):
    enabled = BooleanField(default=True)

    def to_template(self):
        ssh_settings = dict()
        return ssh_settings


class PfRules(EmbeddedDocument):
    """ Rules for pf
    """
    PROTOCOL = (
        ('any', 'ANY'),
        ('carp', 'CARP'),
        ('icmp', 'ICMP'),
        ('icmp6', 'ICMP6'),
        ('tcp', 'TCP'),
        ('udp', 'UDP'),
    )

    ACTION = (
        ('block', 'BLOCK'),
        ('pass', 'PASS'),
    )

    INET = (
        ('inet', 'IPv4'),
        ('inet6', 'IPv6'),
    )

    DIRECTION = (
        ('', 'Both'),
        ('in', 'Inbound'),
        ('out', 'Outbound'),
    )

    source              = StringField(required=False, default="")
    destination         = StringField(required=False, default="")
    port                = StringField(required=False, default="")
    interface           = StringField(required=False, default="")
    inet                = StringField(choices=INET, required=False)
    protocol            = StringField(choices=PROTOCOL, required=True)
    action              = StringField(choices=ACTION, required=True)
    direction           = StringField(choices=DIRECTION, required=False)
    log                 = BooleanField(default=False, required=True)
    flags               = StringField(required=False, default="")
    comment             = StringField(required=False, default="")
    rate                = StringField(required=False, default="")
    blacklist           = BooleanField(default=False, required=False)
    max_src_conn        = StringField(required=False, default="")
    max_src_conn_rate   = StringField(required=False, default="")
    overload            = StringField(required=False, default="")


class PFSettings(DynamicEmbeddedDocument):
    TYPE_REPO = (
        ('file', 'File'),
        ('data', 'Data repository'),
    )

    repository_type   = StringField(choices=TYPE_REPO, default='file', required=True, help_text=_("Type of repository where Vulture will store PF logs"))
    data_repository   = ObjectIdField()
    syslog_repository = ObjectIdField()
    pf_rules          = ListField(EmbeddedDocumentField(PfRules))
    pf_limit_states   = IntField(required=True, default=100000, help_text=_('Maximum number of entries in the memory '
                                                                            'pool used for state table entries (keep '
                                                                            'state).'))
    pf_limit_frags    = IntField(required=True, default=25000, help_text=_('Maximum number of entries in the memory '
                                                                           'pool used for packet reassembly (scrub '
                                                                           'rules).'))
    pf_limit_src      = IntField(required=True, default=50000, help_text=_('Maximum number of entries in the memory '
                                                                           'pool used for tracking source IP addresses'))

    pf_blacklist      = StringField(required=False, default="")
    pf_whitelist      = StringField(required=False, default="")
    pf_rules_text     = StringField(required=False, default="""

#Never remove this line
{{rule}}

""")

    def to_template(self):
        return self.to_mongo()

    @property
    def repository(self):
        """ Property used to map repository field to Repository Object

        :return:
        """
        if self.repository_type == 'data':
            return BaseAbstractRepository.search_repository(self.data_repository)
        return self.repository_type


class LogAnalyserRules(EmbeddedDocument):
    """ Rules for loganalyser
    """

    url = StringField(required=True)
    description = StringField(required=True)
    tags = StringField(required=True)


class LogAnalyserSettings(DynamicEmbeddedDocument):

    loganalyser_rules = ListField(EmbeddedDocumentField(LogAnalyserRules))

    @property
    def repository(self):
        """ Property used to map repository field to Repository Object

        :return:
        """
        if self.repository_type == 'data':
            return BaseAbstractRepository.search_repository(self.data_repository)
        return self.repository_type



class Version(DynamicEmbeddedDocument):
    gui_version = StringField()
    gui_last_version = StringField()
    engine_version = StringField()
    engine_last_version = StringField()
    lib_version = StringField()  # FIXME ???
    lib_last_version = StringField()  # FIXME ???

    def is_gui_up2date(self):
        if self.gui_version == self.gui_last_version:
            return True
        else:
            return False

    def is_engine_up2date(self):

        if self.engine_version == self.engine_last_version:
            return True
        else:
            return False

    @property
    def need_update(self):
        if not self.is_gui_up2date() or not self.is_engine_up2date():
            return True
        else:
            return False


class Vulnerabilities(DynamicEmbeddedDocument):
    need_update = BooleanField(required=True, default=False)
    global_vulns = StringField()
    distrib_vulns = StringField()
    kernel_vulns = StringField()
    global_vulns_verbose = StringField()
    distrib_vulns_verbose = StringField()
    kernel_vulns_verbose = StringField()

    def get_global_vulns(self, verbose=False):
        try:
            proc = subprocess.Popen(['/usr/local/bin/sudo', '-u', 'vlt-sys',
                                     '/usr/local/bin/sudo', '/home/vlt-sys/scripts/get_vulns',
                                     'global', str(verbose)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            res, errors = proc.communicate()

            if errors:
                api_logger.error("Unable to retrieve global vulnerabilities : {}".format(str(errors)))

            if res:
                return res.decode('utf8')
            else:
                return None
        except Exception as e:
            api_logger.exception(e)
            return None


    def get_distrib_vulns(self, verbose=False):
        try:
            proc = subprocess.Popen(['/usr/local/bin/sudo', '-u', 'vlt-sys',
                                    '/usr/local/bin/sudo', '/home/vlt-sys/scripts/get_vulns',
                                    'distrib', str(verbose)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            res, errors = proc.communicate()

            if errors:
                api_logger.error("Unable to retrieve distrib vulnerabilities : {}".format(str(errors)))

            if res:
                return res.decode('utf8')
            else:
                return None
        except Exception as e:
            api_logger.exception(e)
            return None


    def get_kernel_vulns(self, verbose=False):
        try:
            proc = subprocess.Popen(['/usr/local/bin/sudo', '-u', 'vlt-sys',
                                    '/usr/local/bin/sudo', '/home/vlt-sys/scripts/get_vulns',
                                    'kernel', str(verbose)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            res, errors = proc.communicate()

            if errors:
                api_logger.error("Unable to retrieve kernel vulnerabilities : {}".format(str(errors)))

            if res:
                return res.decode('utf8')
            else:
                return None
        except Exception as e:
            api_logger.exception(e)
            return None


class GUISettings(DynamicEmbeddedDocument):  # FIXME A SUPPRIMER
    auth_backends = ListField(ObjectIdField())


class SystemSettings(DynamicEmbeddedDocument):
    ntp_settings = EmbeddedDocumentField(NTPSettings)
    dns_settings = EmbeddedDocumentField(DNSSettings)
    smtp_settings = EmbeddedDocumentField(SMTPSettings)
    ssh_settings = EmbeddedDocumentField(SSHSettings)
    ipsec_settings = EmbeddedDocumentField(IPSECSettings)
    zabbix_settings = ReferenceField('ZabbixAgent')
    pf_settings = EmbeddedDocumentField(PFSettings)
    loganalyser_settings = EmbeddedDocumentField(LogAnalyserSettings)
    global_settings = EmbeddedDocumentField(GLOBALSettings)


class Node(DynamicDocument):
    """ Node model representation

        name : name gave to the node
        default_gw : Node's Vulture gateway
        interfaces : list of node's interfaces
        system_settings : Reference to system configuration of the node
        certificate : Node's certificate
        temporary_key: random key needed to join cluster
        version: GUI / Engine version
        is_dead : Boolean that indicates if a Node is dead or Alive.
                  It is used for performance reason.
                  As soon as an API request raises an Exception, the node becames Dead.
                  The host will become Alive by the crontab script dead_node.minute
        """
    name = StringField(max_length=64, required=True, unique=True,
                       help_text=_("Name of Node"))
    default_ipv4_gw = StringField(required=False, help_text=_('IPV4 Address of Default Gateway'))
    default_ipv6_gw = StringField(required=False, help_text=_('IPV6 Address of Default Gateway'))
    static_route = StringField(required=False, help_text=_('Static routes'), default="""#Routes statiques pour joindre les differents VLANS
#static_routes="vlan1 vlan2"
#route_vlan1="-net -inet6 fd00:1::/64 fd00:3::ffff"
#route_vlan2="-net -inet6 fd00:2::/64 fd00:3::ffff" """)
    interfaces = ListField(ReferenceField('Interface', reverse_delete_rule=PULL))
    system_settings = EmbeddedDocumentField(SystemSettings)
    certificate = ReferenceField('SSLCertificate', reverse_delete_rule=PULL)
    temporary_key = StringField(max_length=8, required=True)
    version = EmbeddedDocumentField(Version)
    vulns = EmbeddedDocumentField(Vulnerabilities)
    is_dead = BooleanField(required=True, default=False)
    diagnostic = StringField(required=True, default="")

    def create_certificate(self):
        """ Create Node certificate from Cluster CA authority

        """
        if self.certificate is None:
            # Get PKI next serial number
            cluster = Cluster.objects.get()
            serial = cluster.ca_serial
            serial += 1

            crt, key = ssl_utils.mk_signed_cert(ssl_utils.get_ca_cert_path(),
                                                ssl_utils.get_ca_key_path(),
                                                self.name,
                                                'FR', '', '', '', '', serial)

            # TODO: Error handling
            # Save serial number
            cluster.ca_serial = serial
            cluster.save()

            # Store the certificate
            certificate = SSLCertificate()
            certificate.name = str(crt.get_subject())
            certificate.cn = str(self.name)
            certificate.o = 'FR'
            certificate.cert = crt.as_pem().decode('utf8')
            certificate.key = key.as_pem(cipher=None).decode('utf8')
            certificate.status = 'V'
            certificate.issuer = str(crt.get_issuer())
            certificate.validfrom = str(crt.get_not_before().get_datetime())
            certificate.validtill = str(crt.get_not_after().get_datetime())
            certificate.serial = str(serial)
            certificate.is_ca = False

            internal = cluster.ca_certificate
            certificate.chain = str(internal.cert)

            certificate.save()
            self.certificate = certificate
            self.save()

    def save(self, *args, **kwargs):
        """ Override save method to create SystemSettings and
            certificate objects at node creation

            if bootstrap is set to True, then don't send the
            node_modified signal. This is to avoid timeout
            at bootstrap time when trying to contact non-existing
            API (Vulture-GUI is not started yet at this time)
        """
        boot = kwargs.get('bootstrap') or False

        if not self.system_settings:
            self.system_settings = SystemSettings()

        """ Do not send signal during bootstrap process because GUI is not yet started """
        super(Node, self).save(*args, **kwargs)
        if boot is False:
            api_logger.debug("Node.save(): Sending node_modified signal")
            node_modified.send(self)



    def delete(self, *args, **kwargs):
        """ Override delete method to delete all inet related to this Node
        """

        for intf in self.interfaces:
            try:
                for inet in intf.inet_addresses:
                    inet.delete()
                intf.delete()
            # Object doesn't exist
            except AttributeError:
                pass
        super(Node, self).delete(**kwargs)
        node_modified.send(self)

    # TODO OVERRIDE DELETE TO ALSO DELETE CERTIFICATE ??

    def get_interfaces(self):
        """ Return interface list for current node, make an API query, to
        ensure Database data are up-to-date
        """

        self.api_request("/api/network/update_intf_list/")
        return self.interfaces

    def get_interface_by_device_name(self, device_name):
        """Search Interface object by device_name, if not found create a new one

        :param device_name: name of the searched interface
        :returns: Interface object
        """
        # looking for interface
        for intf in self.interfaces:
            if intf.device == device_name:
                return intf


        # No interface found ==> create new one
        intf = Interface(device=device_name, alias='if_' + device_name)
        intf.save()
        self.interfaces.append(intf)
        self.save()

        return intf

    def api_request(self, uri, params=None, timeout=None):
        """ Send a GET request to the API located on the node

        :param uri: URI corresponding to the requested action
        :param params: Valid JSON chain
        :param timeout: Used to override default timeout for some specific long requests
        :returns: The API response or False if the node is dead or if request fails
        """

        """ Immediately return False if the host is dead,
             except for the 'is_up()' request
        """
        if uri != '/api/cluster/node/status/' and self.is_dead is True:
            api_logger.info("Node API Request: Node {} is dead, ignoring {}".format(self.name, uri))
            return False

        req = '{}'
        port = settings.API_PORT
        proto = settings.API_PROTO
        headers = {}
        # Parameters are provided
        if params is not None:
            # Parameters validation
            headers = {'Content-Type': 'application/json','Referer': 'vulture-internal'}
            try:
                params = json.dumps(params)
            except Exception as e:
                api_logger.exception(e)
        else:
            headers={'Referer': 'vulture-internal'}


        if not net_utils.is_resolvable_hostname(self.name):
            api_logger.info("{} not resolvable, adding it".format(self.name))
            ip = False
            for intf in self.interfaces:
                for listener in intf.inet_addresses:
                    if listener.is_gui and listener.is_physical:
                        ip = listener.ip
                        break
                if ip:
                    break

            if ip:
                net_utils.make_hostname_resolvable(self.name, ip)

        request_uri = "{}://{}:{}{}".format(proto, self.name, port, uri)
        session = Session()
        kwargs = {}
        if proto == "https":
            session.mount("https", SSLAdapter(ssl.PROTOCOL_TLSv1_2))
            kwargs = {'cert': "/var/db/mongodb/mongod.pem",
                      'verify': "/var/db/mongodb/ca.pem"}

        request = requests.Request("get", request_uri, params, headers).prepare()

        try:
            if timeout:
                t=timeout
            else:
                t=10

            f = session.send(request, **kwargs, timeout=t)
        except requests.RequestException as e:
            api_logger.error("Node API Error for request {}  reason: {}".format(request_uri, str(e)))
            return False

        js = f.content
        return json.loads(js, object_pairs_hook=collections.OrderedDict)


    def is_up(self):
        """ Method used to determine if Node is UP
        It is use in crontab script to check if the node is dead or alive

        :return: True if Node is up, False otherwise
        """
        try:
            status = self.api_request('/api/cluster/node/status/')
            return status.get('status')
        except Exception as e:
            return False

    def get_management_listener(self):
        for intf in self.interfaces:
            for listener in intf.inet_addresses:
                if listener.is_gui:
                    return listener
        # TODO HANDLE THIS CASE
        return None

    def get_applications(self, is_running=False, both=False):
        """ Return list of Applications which are running on current Node

        :param is_running: Boolean used to get only running application
               both: Boolean used to return all apps + running apps as a tuple
        :return: List of Application objects
        """

        app_list_running = list()
        l_list=list()
        l_list_running=list()
        app_full=list()

        from gui.models.application_settings import ListenAddress

        done=dict()
        done_l=dict()
        for listen_address in ListenAddress.objects.filter(related_node=self):

            key="%s/%s"% (str(listen_address.address.ip), listen_address.port)

            """ Get all the apps that share ip/port """
            try:
                app_list = done_l[key]
                continue
            except KeyError as e:
                done_l[key] = listen_address.get_apps()
                app_list=done_l[key]
                pass

            if is_running or both:
                try:
                    status=done[key]
                except KeyError as e:
                    status = net_utils.is_running(listen_address.address.ip, listen_address.port)
                    if status:
                        status=True
                    else:
                        status=False

                    done[key]=status
                    l_list.append(listen_address)
                    if status is True:
                        l_list_running.append(listen_address)

                    for app in app_list:
                        if status is True and app not in app_list_running:
                            app_list_running.append(app)
                        if app not in app_full:
                            app_full.append(app)
                    pass
            else:
                for app in app_list:
                    if app not in app_full:
                        app_full.append(app)

        if not is_running and not both:
            return app_full


        if both:
            return app_full, app_list_running, l_list, l_list_running
        else:
           return app_list_running, l_list_running

    def get_listeners(self):
        """ Return list of Listeners on current Node

        :return: List of Listener objects
        """
        listeners = list()
        """ interfaces is a list of (device, inet_addresses:list(Listeners)) """
        for intf in self.interfaces:
            for listener in intf.inet_addresses:

                """ Handle the case where listener is DEREFERENCED in mongoDB """
                if isinstance (listener, Listener):
                    listeners.append(listener)


        return listeners

    def get_listen_addresses(self):
        """ Return list of Listen address on current Node

        :return: List of ListenAddress objects
        """
        listen_address_list = list()
        from gui.models.application_settings import ListenAddress

        for listen_address in ListenAddress.objects.all():
            if listen_address.address.get_related_node() == self:
                listen_address_list.append(listen_address)
        return listen_address_list

    def is_mongodb_primary(self):
        replica_set = ReplicaSetClient()
        status = replica_set.get_replica_status(self.name + ':9091')

        if status:
            return status == "PRIMARY"
        return False


class Cluster(DynamicDocument):
    """ Cluster model representation

        name : name gave to the cluster
        members : list of node, members of cluster
        system_settings : system settings (ntp/dns/smtp...) of cluster
        ca_certificate : Certification authority certificate of cluster
        ca_serial : Serial Number of last issued certificate
    """
    name = StringField(max_length=64, required=True, unique=True,
                       help_text=_("Name of your cluster"))
    members = ListField(ReferenceField('Node', reverse_delete_rule=PULL))
    system_settings = EmbeddedDocumentField(SystemSettings)
    ca_certificate = ReferenceField('SSLCertificate', reverse_delete_rule=PULL)
    ca_serial = IntField(required=True, default=1)
    ca_crl = StringField(required=False)
    gui_settings = EmbeddedDocumentField(GUISettings)  # FIXME A SUPPRIMER

    def getTokenName(self):
        return self.system_settings.global_settings.public_token

    def getRedisPwd(self):
        return self.system_settings.global_settings.redis_pwd

    def getPortalCookie(self):
        return self.system_settings.global_settings.portal_cookie

    def getAppCookie(self):
        return self.system_settings.global_settings.app_cookie

    def api_request(self, uri, params=None, timeout=None, exclude=None):
        """ Function used to make API request to all cluster's Node

        :param uri: API URI used to send order
        :param timeout: Override default timeout in API calls
        :param exclude: A list of node that we don't want to call
        :returns: list of order result by member
        """
        response = dict()  # TODO Check impact list to dict
        for node in self.members:
            if node.is_dead or node.temporary_key:
                response[node.name] = False
                continue

            if exclude and node.name == exclude:
                response[node.name] = False
                continue

            try:
                """ This URI is very time consuming """
                if uri == '/api/supervision/process/':
                    timeout=20
                api_answer = node.api_request(uri, params, timeout)
                response[node.name] = api_answer
            except Exception as e:
                response[node.name] = False
                api_logger.error("API Request failed for '{}' on node '{}': {}".format(uri,node.name,e))

        return response

    def get_current_node(self):
        """ Return Node object for current node

        :returns: Node object if Node founded, None otherwise
        """
        for node in self.members:
            if node.name == net_utils.get_hostname():
                return node
            else:
                # TODO Exception
                pass

    def get_authentication_repositories(self):
        """ Method used to retrieve list of GUI authentication repositories

        :return: List of Repository Object
        """
        repositories = list()
        from gui.models import repository_settings

        for backend in self.gui_settings.auth_backends:
            for obj in repository_settings.BaseAbstractRepository.__subclasses__():
                try:
                    repo = obj.objects.get(id=backend)
                    repositories.append(repo)
                except obj.DoesNotExist as e:
                    pass
        return repositories

    def get_interface_choices(self):
        """ Return interface list for all nodes as a tuple, ex: ('em0',
        'if_em0')

        :returns: a tuple of interface
        """
        nodes_intfs = list()
        for node in self.members:
            intf_lst = list()
            intf_infos = list()
            intf_lst.append('Node: ' + node.name)
            for intf in node.interfaces:
                intf_info = list()
                intf_info.append(intf.id)
                intf_info.append(intf.alias + ' (on node: ' + node.name + ')')
                intf_infos.append(tuple(intf_info))
            intf_lst.append(tuple(intf_infos))
            nodes_intfs.append(tuple(intf_lst))
        return tuple(nodes_intfs)

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        """ Send bootstrap=True to prevent sending of signal """
        boot = kwargs.get('bootstrap', False)
        x = super(Cluster, self).save()
        if not boot:
            cluster_modified.send(self)
