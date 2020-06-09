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
__author__ = "Florian Hagniel, Kevin Guillemot"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = 'NTP Toolkit'


# Django project imports
from vulture_toolkit.system.service_base import ServiceBase

# Required exceptions imports
from vulture_toolkit.system.exceptions import ServiceConfigError

# Extern modules imports
import ntplib
from re import search as re_search
from subprocess import Popen, PIPE
from sys import path as sys_path
sys_path.append("/home/vlt-gui/vulture")

# Logger configuration imports
import logging
logger = logging.getLogger('services_events')


class NTP(ServiceBase):

    def __init__(self):
        self.service_name = 'ntpd'
        self.template_name = 'ntp.conf'

    @staticmethod
    def ntp_servers_are_up(ntp_server_list):
        """ Testing NTP Servers connectivity

        :param ntp_server_list: list of ntp server to test
        :returns: True if all servers respond, False otherwise
        """
        for srv in ntp_server_list:
            if not NTP.ntp_server_is_up(srv):
                return False
        return True

    @staticmethod
    def ntp_server_is_up(ntp_server):
        """ Testing NTP Server connectivity

        :param ntp_server: ntp server address
        :returns: True if server respond, False otherwise
        """
        c = ntplib.NTPClient()
        try:
            c.request(ntp_server)
        except ntplib.NTPException:
            return False
        return True

    # NTP is a service, available in /usr/local/etc/rc.d, so override status method
    #  by "service {} status"
    def status(self, parameters=None):
        """ Service status

        :returns: status of service (UP, DOWN, ERROR, UNKNOWN, NEED_UPDATE) and return of system command
        """
        if parameters:
            try:
                if self.conf_has_changed(parameters):
                    return "NEED_UPDATE", "Configuration differs on disk."
            except ServiceConfigError as e:
                return "ERROR", "Cannot {}: {}".format(e.trying_to, str(e))

        # Executing service service_name status as vlt-sys user
        proc = Popen(['/usr/local/bin/sudo', '-u', 'vlt-sys', '/usr/local/bin/sudo',
                      'service', self.service_name, 'onestatus'], stdout=PIPE, stderr=PIPE)
        success, error = proc.communicate()
        success = success.decode('utf8')
        error = error.decode('utf8')
        if success:
            logger.info("[{}] Status of service: {}".format(self.service_name.upper(), success))
            m = re_search('{} is (not )?running'.format(self.service_name), success)
            if m:
                status = "UP" if not m.group(1) else "DOWN"
                logger.debug("[{}] Status successfully retrieved : {}".format(self.service_name.upper(), status))
            else:
                status = "UNKNOWN"
                logger.error("[{}] Status unknown, STDOUT='{}', STDERR='{}'".format(self.service_name.upper(), success,
                                                                                    error))
        elif error:
            """ Something were wrong during service call"""
            status = "ERROR"
            success = "{}".format(str(error))
            logger.error("[{}] - Error in status ! STDOUT:'{}', STDERR:'{}'".format(self.service_name.upper(),
                                                                                    str(success), str(error)))
        else:
            """ Service status is unknown"""
            status = "UNKNOWN"
            logger.error("[{}] Status unknown, STDOUT and STDERR are empty.".format(self.service_name.upper(), ))

        return status, success
