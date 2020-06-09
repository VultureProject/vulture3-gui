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
__doc__ = 'Django models dedicated to network settings'

from django.utils.translation import ugettext_lazy as _
from mongoengine import StringField, BooleanField, IntField, ListField, DynamicDocument, ReferenceField, PULL, DictField

from gui.signals.gui_signals import listener_modified
# logger configuration
import logging
logger = logging.getLogger('listeners')

from vulture_toolkit.network.interface import Interface as InterfaceHelper
from gui.models.modssl_settings import ModSSL

BALANCING_CHOICES = (
    ('roundrobin', "RoundRobin"),
    ('leastconn', "Least Conn"),
    ('first', "First server"),
    ('source', "Source IP based"),
    ('uri', "URI based"),
    ('url_param', "URL param based"),
    ('hdr', "Header based"),
    ('rdp-cookie', "RDP-Cookie based"),
)


class LoadbalancerBackend(DynamicDocument):
    host   = StringField()
    ip     = StringField()
    port   = IntField()
    weight = IntField()
    tls    = StringField()
    send_proxy = BooleanField(default=False)


class Loadbalancer(DynamicDocument):

    name              = StringField(help_text=_("Name of loadbalancer"), required=True)
    http_mode         = BooleanField(default=False)
    enable_tls        = BooleanField(default=False)
    ssl_profile       = ReferenceField("ModSSL", reverse_delete_rule=PULL, help_text=_('Select the SSL profile to use for network encryption'))
    incoming_listener = ReferenceField("Listener")
    incoming_port     = IntField(required=True)
    http_keepalive    = BooleanField(default=False)
    http_sticky_session = BooleanField(default=False)
    backends          = ListField(ReferenceField("LoadbalancerBackend"))
    timeout_connect   = IntField(required=True, default=500, help_text=_("Set the maximum inactivity time on the client side"))
    timeout_client    = IntField(required=True, default=5000, help_text=_("Set the maximum time to wait for a connection attempt to a server to succeed"))
    timeout_server    = IntField(required=True, default=2000, help_text=_("Set the maximum inactivity time on the server side"))
    timeout_tunnel    = IntField(required=True, default=600, help_text=_("Set the maximum inactivity time on the client and server side for tunnels (e.g Websockets)"))
    timeout_client_fin= IntField(required=True, default=10, help_text=_("Set the maximum inactivity time on the client and server side for tunnels (e.g Websockets)"))
    maxconn           = IntField(required=True, default=10000, help_text=_("Fix the maximum number of concurrent connections on a frontend"))
    balance           = StringField(required=True, default='roundrobin', choices=BALANCING_CHOICES,
                                    help_text=_("Balancing mode of servers"))
    balancing_param   = StringField(required=False, help_text=_("Option of balancing mode (if needed)"))
    listen_conf       = StringField(help_text=_("Custom listen configuration for Haproxy"))

    @property
    def balancing(self):
        if self.balance == "hdr":
            result = "hdr({})".format(self.balancing_param)
        elif self.balance == "url_param":
            result = "url_param {}".format(self.balancing_param)
        elif self.balance == "rdp-cookie":
            result = "rdp-cookie({})".format(self.balancing_param)
        else:
            result = self.balance
        return result

    def save(self, *args, **kwargs):
        super(Loadbalancer, self).save(*args, **kwargs)
        listener_modified.send(self)

    def delete(self, *args, **kwargs):
        super(Loadbalancer, self).delete(*args, **kwargs)
        listener_modified.send(self)


class Listener(DynamicDocument):
    """
    """
    alias = StringField(default='undefined', help_text=_('Name of listener'))
    ip = StringField(required=True, help_text=_('IP Address of listener'))
    version = StringField()
    prefixlen = StringField(required=True,help_text=_('Netmask of listener: '
                          'accepted syntax are dotted-quad (x.x.x.x) or CIDR '
                            'notation  (/x)'))
    is_carp = BooleanField(default=False)
    is_physical = BooleanField(default=False)
    carp_vhid = IntField(help_text=_('Virtual Host ID'))
    carp_passwd = StringField(required=False)
    carp_priority = IntField(help_text=_('Priority of Listener'), default=1)
    is_gui = BooleanField(default=False)
    related_node = ReferenceField('Node', required=False)
    previous_inet = DictField(default={})

    def is_equals(self, cmp_inet):
        """ Used to compare inet DB objects (Listener) to helpers inets
        objects (Inet or Inet6). Helpers corresponds to running ifconfig
        configuration

        :param cmp_inet: Inet object to compare
        :return: True if cmp_inet is same than Listener object,
        False otherwise
        """
        if self.prefixlen == cmp_inet.netmask and self.ip == cmp_inet.str_ip_address:
            return True
        return False

    def as_inet_helper(self):
        """ Turn Listener Object into Inet helper object

        """
        inet = InterfaceHelper.create_inet_object(self.to_mongo())
        return inet


    def save(self, *args, **kwargs):
        """ Override save method

            if bootstrap is set to True, then don't send the
            node_modified signal. This is to avoid timeout
            at bootstrap time when trying to contact non-existing
            API (Vulture-GUI is not started yet at this time)

            Store previous configuration into previous_inet.
            This is required to shutdown the previous interface configuration via 'ifconfig'
        """
        boot = kwargs.get('bootstrap') or False

        """ Do not send signal during bootstrap process because GUI is not yet started """
        if boot is False:
            logger.info("Listener.save(): Sending node_modified signal")
            listener_modified.send(self)

        super(Listener, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        bootstrap = kwargs.pop('bootstrap', False)
        logger.info("Calling Listener.delete() on {}".format (self))
        super(Listener, self).delete(*args, **kwargs)
        if not bootstrap:
            listener_modified.send(self)

    def __str__(self):
        node = self.get_related_node()

        try:
            return "{} - {}" .format(node.name, self.ip)

        except AttributeError:
            from gui.models.system_settings import Node
            node = Node.objects.with_id(node)
            return "{} - {}" .format(node.name, self.ip)


    def deploy_inet(self):
        """Execute deploy method on listener

        :return:
        """
        return self.deploy(self)


    def deploy_carp(self):
        """Execute deploy method on all related carp listener

        """
        for inet in self.get_related_carp_inets():
            self.deploy(inet)

    def deploy(self, inet):
        """
        Deploy listener configuration saved on database to corresponding node.

        :param inet: Listener Object to deploy
        """


        from gui.models.system_settings import Node
        logger.info(inet)
        intf = Interface.objects.get(inet_addresses__in=[inet])
        node = Node.objects.get(interfaces=intf)

        #First we shut down the listener on the corresponding node if there was an existing configuration
        previous_inet = inet.get_previous_inet()
        if previous_inet:
            logger.debug("inet {} got previous conf".format(str(inet)))
            previous_inet, previous_intf, previous_node = previous_inet
            logger.info("Sending down order to inet : {} ({}) on node {} ({})".format(previous_inet.ip, previous_inet.prefixlen, previous_node.name, previous_intf.device))

            res = node.api_request("/api/network/listener/" + str(inet.id) + "/down/")
            if not res.get('status'):
                logger.error(res)

            inet.delete_previous_inet()


        #Then we update what needs to be updated on the node
        logger.info("Refresh rc_conf on node {}".format(node.name))
        res = node.api_request("/api/cluster/management/conf/")
        if isinstance(res, bool) and not res:
            logger.error("Fail to update rc.conf.local file. Node {} not reachable.".format(node.name))
        elif res.get('changed'):
            logger.info("rc.conf.local updated on {}".format (node.name))


        #At least, we start the interface
        logger.info("Startup device {} on node {}".format(intf.device, node.name))
        res = node.api_request("/api/network/listener/" + str(inet.id) + "/up/")
        if isinstance(res, bool) and not res:
            logger.error("Fail to start device {} on node {}. Node not reachable.".format(intf.device, node.name))
        elif not res.get('status'):
            logger.error(res)
            return False

        return True

    def get_previous_inet(self):
        """ Return previous configuration of inet if defined, this previous
        configuration is usually used to down an existing inet

        :returns: previous Listener object and related Interface and Node objects
        None if previous configuration doesn't exist
        """
        from gui.models.system_settings import Node
        if self.previous_inet:
            inet = Listener(**self.previous_inet)
            intf = Interface.objects.get(inet_addresses__in=[self])
            node = Node.objects.get(interfaces=intf)
            return inet, intf, node
        else:
            return None

    def delete_previous_inet(self):
        """ Delete configuration of previous inet, usually used after inet goes
        down
        """
        self.previous_inet = None
        self.save(bootstrap=True)

    def get_related_carp_inets(self):
        """A list containing all Listener object related of CARP listener

        :return: list of Listener object
        """
        inets = list()
        #logger.info("Looking for inet vhid :" + str(self.carp_vhid))
        if self.carp_vhid is not None:
            inets = Listener.objects(carp_vhid=self.carp_vhid)
        #logger.debug("Related carp listeners are : " + str(inets))
        return inets

    def get_related_carp_intfs(self):
        """A list containing all Interface object related of CARP listener

        :return: list of Interface object
        """
        intf_lst = list()
        for inet in self.get_related_carp_inets():
            #logger.debug("looking for inet " + str(inet))
            intf = Interface.objects.get(inet_addresses__in=[inet])
            intf_lst.append(intf)
        return intf_lst

    def get_related_carp_inets_detailed(self):
        """ A list containing detailed information about carp inets,each element
        of the list is a dict. Dict-key's explanation :
        node : Node object of carp inet
        intf : Interface object of carp inet
        inet : Listener object

        """
        returned_inets = list()
        carp_inets = self.get_related_carp_inets()
        for inet in carp_inets:
            carp_inet = dict()
            intf = Interface.objects.get(inet_addresses__in=[inet])
            node = intf.get_related_node()
            carp_inet['node'] = node
            carp_inet['intf'] = intf
            carp_inet['inet'] = inet
            returned_inets.append(carp_inet)
        return returned_inets

    def get_related_node(self):
        """ Return related Node
        """
        if self.related_node:
            return self.related_node

        intf = self.get_related_interface()
        node = intf.get_related_node()
        self.related_node=node
        self.save(bootstrap=True)
        return node

    def get_related_interface(self):
        """ Return related Interface
        """
        for intf in Interface.objects.all():
            for listener in intf.inet_addresses:
                if listener == self:
                    return intf

    @property
    def ip_cidr(self):
        """ Return IP/CIDR notation of Listener

        :return: String with ip/cidr notation
        """
        from iptools.ipv4 import netmask2prefix
        import ipaddress
        ip = ipaddress.ip_address(self.ip)

        if ip.version == 4:
            prefix = netmask2prefix(self.prefixlen)
            return "{}/{}".format(self.ip, prefix)
        else:
            prefix = self.prefixlen
            return "{} prefixlen {}".format(self.ip, prefix)

    @property
    def rc_conf(self):
        """ Return listener as rc.conf format

        :return: String with listener as rc.conf format
        """

        import ipaddress
        ip = ipaddress.ip_address(self.ip)

        if ip.version == 4:
            family="inet"
        else:
            family="inet6"


        intf = self.get_related_interface()
        if self.is_carp:
            device = "{}_alias".format(intf.device)
            device += '{}'
            inet = "{} {} vhid {} advskew {} pass {}".format(family, self.ip_cidr, self.carp_vhid, self.carp_priority, self.carp_passwd)
        elif not self.is_physical:
            device = "{}_alias".format(intf.device)
            device += '{}'
            inet = "{} {}".format(family, self.ip_cidr)
        else:
            device = intf.device
            inet = "{} {}".format(family, self.ip_cidr)

        if self.version == '6':
            device += "_ipv6"

        return 'ifconfig_{}="{}"'.format(device, inet)


class Interface(DynamicDocument):
    """
    """
    alias = StringField(default='undefined')
    device = StringField()
    inet_addresses = ListField(ReferenceField('Listener', reverse_delete_rule=PULL))


    def __hash__(self):
        return hash(str(self.id))

    def get_inet_by_ip(self, ip):
        """Search Listener object by IP Address

        :param ip: IP Address of the searched inet
        :returns: Inet object or None if not found
        """
        for inet in self.inet_addresses:
            try:
                if inet.ip == ip:
                    return inet
            except:
                return None
        return None

    def find_carp_inet(self, searched_inet):
        """ Search if given CARP inet is present on this interface

        :param searched_inet: Listener object to find
        :return: Inet if exist, None otherwise
        """
        for inet in self.inet_addresses:
            if inet.carp_vhid == searched_inet.carp_vhid:
                return inet
        return None

    def create_listener(self, inet, primary=False):
        """

        :param inet:
        :return:
        """
        obj = Listener()
        obj.ip = inet.str_ip_address
        obj.prefixlen = inet.netmask
        obj.version = str(inet.ip_address.version)
        if inet.vhid is not None:
            obj.is_carp = True
            obj.carp_vhid = int(inet.vhid)
        elif primary:
            obj.is_physical = True
        obj.save()
        self.inet_addresses.append(obj)
        self.save()

    def get_related_node(self):
        """ Return Node object related to this Interface

        :return: Node object
        """
        from gui.models.system_settings import Node
        node = Node.objects.get(interfaces=self)
        return node

    def __str__(self):
        return "{} on node {}" .format(self.alias, self.get_related_node().name)



    def __eq__(self, other):
        """ Override __eq__ method to compare Interface object(DB) to Intf (Helper)
        """
        if other.__module__ == 'vulture_toolkit.network.interface':
            return other.__eq__(self)
        else:
            return super(Interface, self).__eq__(other)
