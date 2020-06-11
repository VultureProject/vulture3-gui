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
__author__ = "Jérémie Jourdin"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = 'IPSEC Toolkit'

import sys

sys.path.append("/home/vlt-gui/vulture")

import logging
import logging.config
logger = logging.getLogger('services_events')

from vulture_toolkit.system.service_base import ServiceBase
from vulture_toolkit.templates import tpl_utils
from vulture_toolkit.system.sys_utils import write_in_file
import subprocess
import re


class IPSEC(ServiceBase):

    def __init__(self):
        self.service_name = 'strongswan'

    def write_configuration(self, parameters, service_settings=None):

        for file in ["strongswan", "ipsec", "ipsec-secrets"]:
            tpl, path = tpl_utils.get_template(file)
            conf = tpl.render({'conf': parameters})
            logger.info("[IPSEC] - Writing configuration file {}".format(file))
            write_in_file(path, conf)

    def status(self, parameters=None):
        """ Service status

        :returns: True if strongswan is running, False otherwise
        """
        # Executing service service_name status as vlt-sys user
        proc = subprocess.Popen(['/usr/local/bin/sudo', '-u', 'vlt-sys', '/usr/local/bin/sudo',
                                 'service', 'strongswan', 'onestatus'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        success, error = proc.communicate()
        success = success.decode('utf8')
        error = error.decode('utf8')
        if success:
            pattern = re.compile('.*Security Associations.*', re.DOTALL)
            m = re.match(pattern, success)
            if m is not None:
                status = "WARNING"

                if "(0 up" not in success:
                    status = "UP"
            else:
                status = "DOWN"
        elif error:
            """ Something were wrong during service call
                This can happen if strongswan_enable is not set to "YES" in /etc/rc.conf
            """
            status = "ERROR"
            logger.error("[IPSEC] - Error in status ! STDOUT:{}, STDERR:{}".format(str(success), str(error)))
        else:
            """ Service is not up
            """
            status = "DOWN"

        """ Retrieve Security Associations """
        ipsec_sa = success
        return (status, ipsec_sa)
