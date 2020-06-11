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
__doc__ = 'Inet6 Class: network inet management for IPV6'

import logging

import ipaddress

logger = logging.getLogger('local_listeners')
from vulture_toolkit.network.inet_base import InetBase


class Inet6(InetBase):
    """Class used to handle IPv6 inets. This class check the consistency of
     inet6 (IP and netmask) and can make inet Up or Down.

    """

    def __init__(self, inet):
        """ Creating the Inet6 object, during this creation IP and netmask are
        checked, if they are ok we create CIDR representation of inet

        :param inet: Dictionary containing values used to define an IPV6 address
        """
        self.ip_address = self.valid_ip(inet.get('ip'))
        self.netmask = self.valid_netmask(inet.get('prefixlen'))
        self.vhid = inet.get('carp_vhid')
        self.passwd = inet.get('carp_passwd')
        self.advskew = inet.get('carp_priority')

        if self.ip_address and self.netmask:
            self.str_ip_address = str(self.ip_address)
            self.cidr = self.create_cidr_notation()

    def valid_netmask(self, netmask):
        """ Test the validity of gave netmask, supported netmask
        notation are CIDR (/x) and int values. Netmask have to be in 4-128 range

        :param netmask:String containing netmask
        :return:Netmask if netmask is valid, False otherwise
        """

        # Handling netmask with CIDR prefix
        if netmask[:1] == '/':
            netmask = netmask[1:]
        try:
            netmask = int(netmask)
        except ValueError:
            logger.error("Invalid netmask : {}".format(netmask))
            return False

        if netmask in range(3, 129):
            return str(netmask)  # String because netmask is saved in Stringfield
        else:
            logger.error("{} not in supported CIDR IPv6 Prefixes (4-128)"
                         "".format(str(netmask)))
            return False

    def valid_ip(self, ip_address):
        """Check if IP address is a valid IP Address,

        :param ip_address: A string containing an IP Address
        :return:IPv6Address Object if IP is valid, False otherwise
        """
        try:
            ip = ipaddress.ip_address(ip_address)
            # Link local address are valid, but we don't need them.
            if not ip.is_link_local:
                return ip
            else:
                return None
        except ValueError:
            return False

    def up(self, intf, version='6'):
        """Make inet up on related network interface controller

        :param intf: A string containing name of NIC (ex:em0, lo0)
        :param version: Version of IP, still 6 in this case
        :return:True if Inet6 was correctly make UP, False otherwise
        """
        return super(Inet6,self).up(intf,version)

    def down(self, intf, version='6'):
        """Make inet down on related network interface controller

        :param intf: A string containing name of NIC (ex:em0, lo0)
        :param version: Version of IP, still 6 in this case
        :return:True if Inet6 was correctly make down, False otherwise
        """
        return super(Inet6, self).down(intf,version)

    def create_cidr_notation(self):
        """ Create the CIDR notation of inet6 device (example : IP
        fe80::a00:27ff:fe23:40da with 64 prefixlen will be
        fe80::a00:27ff:fe23:40da/64

        :returns: string with Inet in CIDR notation
        """
        return "/".join([self.str_ip_address, self.netmask])

    def __str__(self):
        return "{} ({})" .format(self.str_ip_address, self.netmask)