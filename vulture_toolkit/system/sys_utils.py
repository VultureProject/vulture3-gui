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
__doc__ = 'System Utils Toolkit'

import logging
import re
import subprocess

logger = logging.getLogger('services_events')

def check_service_status(service_name):
    """ Check system service status

    :param service_name: name of the service
    :returns: True if service is running, False otherwise
    """
    output = subprocess.check_output(['/usr/local/bin/sudo', '-u', 'vlt-sys', '/usr/local/bin/sudo','/usr/local/bin/sudo', '/bin/ps', '-A']).decode('utf8')
    if re.search(service_name, output):
        return True
    return False

def write_in_file(filepath, content):
    """Write content into file. Used to create/update configuration files
    !!! Warning, for security purpose filename have to be in allowed files list
     present in write_configuration_file script !!!

    :param filepath: complete path to file (ie: path + filename)
    :param content: a string containing content
    :return:
    """
    proc = subprocess.Popen(['/usr/local/bin/sudo', '-u', 'vlt-sys', '/usr/local/bin/sudo',
                             '/home/vlt-sys/scripts/write_configuration_file',
                             filepath, content], stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    res, errors = proc.communicate()
    if not errors:
        logger.debug("write_in_file:: Configuration file {} successfully written.")
        return True
    else:
        logger.error("write_in_file:: Write configuration file {} failed : {}".format(str(filepath), str(errors)))
        return False
