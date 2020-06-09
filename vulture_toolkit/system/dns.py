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
__doc__ = 'DNS Toolkit'

import sys

sys.path.append("/home/vlt-gui/vulture")

import logging
import logging.config
#from vulture_toolkit.log.settings import LOG_SETTINGS

from vulture_toolkit.system.service_base import ServiceBase

#logging.config.dictConfig(LOG_SETTINGS)
logger = logging.getLogger('services_events')


class DNS(ServiceBase):

    def __init__ (self):
        self.service_name = 'dns'
        self.template_name = 'dns.conf'
        self.configuration_path = '/etc/resolv.conf'

    def start_service(self):
        return 'UP', "Configuration applied"

    def stop_service(self):
        return 'UP', "Configuration applied"

    def restart_service(self):
        return 'UP', "Configuration applied"

