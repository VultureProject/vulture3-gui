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
__doc__ = 'Inet Class: network inet management'

import logging
import socket
import struct

import ipaddress
from iptools.ipv4 import hex2ip, validate_netmask

logger = logging.getLogger('local_listeners')

from vulture_toolkit.network.inet_base import InetBase

class Inet(InetBase):
    """Class used to handle IPv4 inets. This class check the consistency of
     inet (IP and netmask) and can make inet Up or Down.

    """

    def __init__ (self, inet):
        """ Creating the Inet object, during this creation IP and netmask are
        checked, if they are ok we create CIDR representation of inet

        :param inet: Dictionary containing values used to define an IPV4 address
        """
        self.ip_address = self.valid_ip(inet.get('ip'))
        self.netmask = self.valid_netmask(inet.get('prefixlen'))
        self.vhid = inet.get('carp_vhid')
        self.passwd = inet.get('carp_passwd')
        self.advskew = inet.get('carp_priority')

        if self.ip_address and self.netmask:
            self.str_ip_address = str(self.ip_address)
            self.cidr = self.create_cidr_notation()
        else :
            logger.error("Wrong IP or Netmask : {} {}".format(self.ip_address,
                          self.netmask))


    def valid_netmask(self, netmask):
        """ Test the validity of gave netmask, supported netmask
        notation are dotted-quad (x.x.x.x), CIDR (/x) and hex
        encoded netmask

        :param netmask:String containing netmask
        :return:True if netmask is valid, False otherwise
        """
        if not netmask:
            return False
        #Handling netmask with CIDR prefix
        if netmask[:1] == '/':
            try:
                cidr_prefix = int(netmask[1:])
                netmask = self.cidr_prefix2netmask(cidr_prefix)
            except ValueError:
                return False

        #Handling hexadecimal netmask
        if hex2ip(netmask):
            netmask = hex2ip(netmask)

        if validate_netmask(netmask):
            return netmask
        else:
            return False


    def valid_ip(self, ip_address):
        """Check if IP address is a valid IP Address

        :param ip_address: A string containing an IP Address
        :return:IPv4Address Object if IP is valid, False otherwise
        """
        try:
            return ipaddress.ip_address(ip_address)
        except ValueError:
            return False


    def up(self, intf, version=''):
        """Make inet up on related network interface controller

        :param intf: A string containing name of NIC (ex:em0, lo0)
        :param version: Version of IP, still empty in this case
        :return:True if Inet was correctly make UP, False otherwise
        """
        return super(Inet,self).up(intf, version)


    def down(self, intf, version=''):
        """Make inet down on related network interface controller

        :param intf: A string containing name of NIC (ex:em0, lo0)
        :param version: Version of IP, still empty in this case
        :return:True if Inet was correctly make down, False otherwise
        """
        return super(Inet, self).down(intf, version)


    def cidr_prefix2netmask(self, cidr_prefix):
        """ Convert a CIDR prefix to a dotted netmask

        :param cidr_prefix: Int containing CIDR prefix
        :return:A string containing a dotted netmask
        """
        var_struct = struct.pack(">I", (0xffffffff << (32 - cidr_prefix))
                                 & 0xffffffff)
        return socket.inet_ntoa(var_struct)


    def __str__(self):
        return "{} ({})" .format(self.str_ip_address, self.netmask)