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
__doc__ = 'InetBase Class: network inet management'

import logging
import subprocess

from iptools.ipv4 import netmask2prefix
#from vulture_toolkit.log import log_utils
logger = logging.getLogger('local_listeners')


class InetBase(object):
    """ 
    
    """
    def create_cidr_notation(self):
        """ Create the CIDR notation of inet device (example :
        IP 192.168.0.1 with 255.255.255.0 netmask will be 192.168.0.1/24

        :returns: string with Inet in CIDR notation 
        """
        str_prefix = str(netmask2prefix(self.netmask))
        return "/".join([self.str_ip_address, str_prefix]) 


    def up(self, intf, version):
        """ Adding the inet into ifconfig entries

        :param intf: the device where IP is attached (ex : em0, lo0..)
        :param version: version of IP, expected empty string for v4 and 6 for v
        :return: True if success, otherwise False and error's detail
        """
        logger.info("Making inet " + self.str_ip_address + " up on " + intf)
        inet_version = 'inet' + version
        """Handling inet which aren't CARP.
        IE, execute "ifconfig intfname inet_version cidr alias" from vlt-sys user
        """
        try:
            if self.vhid is None or self.vhid == 0:
                logger.info("Creating NON-CARP listener")
                logger.info("/usr/local/bin/sudo -u vlt-sys /usr/local/bin/sudo "
                             "/sbin/ifconfig {} {} {} alias"
                             .format(intf, inet_version, self.cidr))
                proc = subprocess.Popen(['/usr/local/bin/sudo','-u','vlt-sys',
                                         '/usr/local/bin/sudo','/sbin/ifconfig',
                                        intf, inet_version, self.cidr, 'alias'],
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                """Handling CARP inet. IE, execute :
                "ifconfig intfname inet_version vhid vhid_value advskew advskew_value
                pass pass_value cidr alias" from vlt-sys user
                """
            else:
                logger.debug("Creating CARP listener")
                proc = subprocess.Popen(['/usr/local/bin/sudo','-u','vlt-sys',
                                         '/usr/local/bin/sudo','/sbin/ifconfig',
                                        intf, inet_version,'vhid', str(self.vhid),
                                        'advskew', str(self.advskew),'pass',
                                        self.passwd, self.cidr, 'alias'],
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            success, error = proc.communicate()
            if error:
                logger.error("Unable to make {} up, reason: {} "
                             "".format(self.str_ip_address, error))
                return False, str(error)
            else:
                logger.info("Inet {} successfully up "
                            "".format(self.str_ip_address))
                return True, None
        except Exception as e:
            logger.exception(e)
            return False, str(e)

    def down(self, intf, version):
        """ Removing the inet from ifconfig entries

        :param intf: the device where IP is attached (ex : em0, lo0..)
        :param version: version of IP, expected empty string for v4 and 6 for v6
        :return: True if success, otherwise False and error's detail
        """
        logger.info("Making inet " + self.str_ip_address + " down on " + intf)
        inet_version = 'inet' + version

        """Handling inet which aren't CARP.
        IE, execute "ifconfig intfname inet_version cidr -alias" from vlt-sys user
        """
        try:
            logger.debug("/usr/local/bin/sudo -u vlt-sys /usr/local/bin/sudo "
                         "/sbin/ifconfig {} {} {} -alias"
                         .format(intf, inet_version, self.str_ip_address))
            proc = subprocess.Popen(['/usr/local/bin/sudo','-u','vlt-sys',
                                     '/usr/local/bin/sudo','/sbin/ifconfig', intf,
                                    inet_version, self.str_ip_address, '-alias'],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
            success, error = proc.communicate()
            if error:
                logger.error("Unable to shut down {}, reason: {} "
                             "".format(self.str_ip_address, error))
                return False, str(error)
            else:
                logger.info("Inet {} successfully shutted down "
                            "".format(self.str_ip_address))
                return True, None
        except Exception as e:
            logger.exception(e)
            return False, str(e)


    def __eq__(self, other):
        """ Comparizon method for inets object,
        Inet object are equals if their dict are equals
        """
        return self.__dict__ == other.__dict__
