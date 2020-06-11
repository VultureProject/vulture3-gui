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
__doc__ = 'Interface Class: network interface management'

import re
import subprocess
import sys

import ipaddress

from vulture_toolkit.network.inet import Inet
from vulture_toolkit.network.inet6 import Inet6

sys.path.append("/home/vlt-gui/vulture")

import logging
import logging.config
logger = logging.getLogger('local_listeners')


class Interface(object):
    def __init__ (self, device):
        self.device       = device
        self.inet_list = self.get_inet_list('v4') + self.get_inet_list('v6')

    def get_inet_list(self, version):
        """ Get inet list for Interface

        :param version: IPVersion of expected inet (v4 or v6)
        :returns: an list containing inet object
        """
        #Retrieving inet list 
        if version == 'v4':
            reg = re.compile ('inet (?P<ip>[0-9.]+) netmask (?P<prefixlen>0[xX]'
                              '[0-9a-fA-F]+)(?: broadcast (?P<broadcast>[0-9.]+'
                              '))?(?: vhid (?P<carp_vhid>[0-9]+))?', re.M)
        elif version == 'v6':
            reg = re.compile ('inet6 (?P<ip>[a-z0-9:]+)(?:%[a-z0-9]{3,4})? '
                              'prefixlen (?P<prefixlen>[0-9]+)(?: scopeid ([0-9.]+)'
                              ')?(?: vhid (?P<carp_vhid>[0-9]+))?', re.M)

        proc = subprocess.Popen(["/sbin/ifconfig", self.device],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        res = proc.communicate()
        success = res[0].decode('utf8')

        inet_lst = list()
        matched_inets = reg.finditer(success)
        for match in matched_inets:
            inet = match.groupdict()
            inet_obj = self.create_inet_object(inet)
            if inet_obj.ip_address is not None:
                inet_lst.append(inet_obj)
        return inet_lst

    @staticmethod
    def create_inet_object(inet):
        """
        """
        try:
            ip = ipaddress.ip_address(inet.get('ip'))
        except ValueError as e:
            logger.error(e)
            return None
        except Exception as e:
            logger.exception(e)
            return None

        if ip.version == 4:
            return Inet(inet)
        elif ip.version == 6:
            return Inet6(inet)


    def inet_in_device_networks(self, tested_inet):
        """ check if tested_inet is on same networks of the device

        :param tested_inet: inet object to test
        :returns: True if inet is in network, False otherwise
        """
        for inet in self.inet_list:
            intf = ipaddress.ip_interface(inet.cidr)
            if tested_inet.ip_address in intf.network:
                return True

        return False

    def __eq__(self, other):
        """ Comparizon method, this method is used to compare if interface data 
        are equals to interface data in database  
        """
        db_inet_lst = list()
        for inet in other.inet_addresses:
            inet_obj = self.create_inet_object(inet.to_mongo())
            db_inet_lst.append(inet_obj)

        if db_inet_lst == self.inet_list and self.device == other.device:
            return True
        else :
            return False
