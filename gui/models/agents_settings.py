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
__author__ = "Kevin Guillemot"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = 'Django models dedicated to monitoring agents'


# Django system imports
from django.utils.translation import ugettext_lazy as _
from mongoengine              import (BooleanField, DynamicDocument, IntField, ListField, PULL, ReferenceField,
                                      StringField)

# Django project imports
from gui.models.network_settings import Listener # Needed by ReferenceField
from gui.models.ssl_certificate import SSLCertificate # Needed by ReferenceField
from vulture_toolkit.network.net_utils import get_hostname

# Required exceptions imports

# Extern modules imports

# Logger configuration imports
import logging
logger = logging.getLogger('debug')


# Global shared variables
ENCRYPTION_TYPE = (
    ('unencrypted', 'Clear text'),
    ('psk', 'Pre-shared key'),
    ('cert', 'Certificate')
)


class ZabbixAgent(DynamicDocument):
    """ Zabbix Agent model representation
    """

    # Retrieve node hostname to set default value of 'hostname' field
    default_hostname = get_hostname()

    enabled = BooleanField(default=False, verbose_name=_('Enable service'), required=True,
                           help_text=_('Enable agent service'))

    servers = StringField(verbose_name=_('Server(s)'), required=True, default='127.0.0.1,::127.0.0.1,::ffff:127.0.0.1',
                          help_text=_('List of comma delimited IP addresses (or hostnames) of Zabbix servers.'))

    listeners = ListField(ReferenceField('Listener', reverse_delete_rule=PULL), verbose_name=_("Listen address(es)"),
                          required=True, help_text=_('List of IP addresses that the agent should listen on.'))

    port = IntField(default=10050, required=True, min_value=1024, max_value=65535, verbose_name=_("Listen port"),
                    help_text=_('Agent will listen on this port for connections from the server.'))

    active_servers = StringField(verbose_name=_('Active Server(s)'), required=True,
                                 default="127.0.0.1:20051,zabbix.domain,[::1]:30051,::1,[12fc::1]",
                                 help_text=_('List of comma delimited IP:port (or hostname:port) pairs of Zabbix'
                                             ' servers for active checks.'))

    hostname = StringField(verbose_name=_('Hostname'), required=True, default=default_hostname,
                           help_text=_('Required for active checks and must match hostname'
                                       ' as configured on the server.'))

    allow_root = BooleanField(verbose_name=_('Allow root'), required=True, default=False,
                              help_text=_('Allow the agent to run as "root".'))

    tls_accept = StringField(verbose_name=_('TLS Accept'), default='unencrypted', choices=ENCRYPTION_TYPE,
                             required=True, help_text=_('What incoming connections to accept.'))

    tls_connect = StringField(verbose_name=_('TLS Connect'), required=True, default='unencrypted',
                              choices=ENCRYPTION_TYPE,
                              help_text=_('How the agent should connect to server or proxy. Used for active checks.'))

    tls_cert = ReferenceField('SSLCertificate', reverse_delete_rule=PULL, verbose_name=_('Agent certificate'),
                              required=False, help_text=_('Certificate used by "TLS Accept" and/or "TLS Connect"'))

    tls_server_subject = StringField(verbose_name=_('Server certificate subject'), required=False,
                                     help_text=_('Allowed server certificate subject.'))

    tls_server_issuer = StringField(verbose_name=_('Server certificate issuer'), required=False,
                                    help_text=_('Allowed server certificate issuer.'))

    psk_identity = StringField(verbose_name=_('Agent PSK identity '), required=False,
                               help_text=_('Unique, case sensitive string used to identify the pre-shared key.'))

    psk_key = StringField(verbose_name=_('Agent PSK string '), required=False,
                          help_text=_('Pre-shared key used by agent to verify connection.'))

    enable_remote_commands = BooleanField(verbose_name=_('Enable remote commands'), required=True, default=False,
                                          help_text=_('Whether remote commands from Zabbix server are allowed.'))

    log_remote_commands = BooleanField(verbose_name=_('Log remote commands'), required=True, default=False,
                                       help_text=_('Enable logging of executed shell commands as warnings.'))

    start_agents = IntField(default=3, required=True, min_value=0, max_value=100, verbose_name=_("Start Agents"),
                            help_text=_('Number of pre-forked instances of zabbix_agentd that process passive checks.'
                                        'If set to 0, disables passive checks and the agent will not listen on any TCP '
                                        'port.'))

    refresh_active_checks = IntField(default=120, required=True, min_value=60, max_value=3600,
                                     verbose_name=_("Refresh active checks"),
                                     help_text=_('How often list of active checks is refreshed, in seconds.'))

    timeout_process = IntField(default=3, required=True, min_value=1, max_value=30, verbose_name=_("Timeout"),
                               help_text=_('Spend no more than Timeout seconds on processing.'))

    buffer_send = IntField(default=5, required=True, min_value=1, max_value=3600, verbose_name=_("Buffer send"),
                           help_text=_('Do not keep data longer than N seconds in buffer.'))

    buffer_size = IntField(default=100, required=True, min_value=2, max_value=65535, verbose_name=_("Buffer size"),
                           help_text=_('Maximum number of values in a memory buffer. The agent will send all '
                                       'collected data to Zabbix Server/Proxy if the buffer is full.'))

    def to_template(self):
        """ Dictionary used to create configuration file.

        :return: Dictionary of configuration parameters
        """
        # Convert self attributes into dict
        zabbix_settings = self.to_mongo()

        # Convert listeners list into string
        zabbix_settings['listeners'] = ','.join([l.ip for l in self.listeners])
        # Convert Boolean fields into int (0 or 1)
        bool_to_int = {
            True: 1,
            False: 0,
            # 'True': 1,
            # 'False': 0
        }
        attrs_to_convert = {
            'allow_root': self.allow_root,
            'enable_remote_commands': self.enable_remote_commands,
            'log_remote_commands': self.log_remote_commands,
        }
        for attr_name, attr in attrs_to_convert.items():
            zabbix_settings[attr_name] = bool_to_int[attr]
        return zabbix_settings

    def __str__(self):
        return "Zabbix-Agent Settings"
