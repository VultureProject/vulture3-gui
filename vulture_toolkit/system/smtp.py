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
__doc__ = 'SMTP Toolkit'

import sys

sys.path.append("/home/vlt-gui/vulture")

import logging
logger = logging.getLogger('services_events')

from vulture_toolkit.system.service_base import ServiceBase
from vulture_toolkit.templates import tpl_utils
from vulture_toolkit.system.sys_utils import write_in_file
from vulture_toolkit.system.exceptions import ServiceConfigError, ServiceNoConfigError


class SMTP(ServiceBase):
    def __init__ (self):
        self.service_name       = 'smtp'
        self.service_mail_name  = 'mail'
        self.template_name      = 'ssmtp.conf'
        self.template_mail_name = 'mailer.conf'

    def write_configuration(self, parameters, service_settings=None, text_config=None):
        # ### Write the second template (mailer.conf)
        tpl, path = tpl_utils.get_template(self.service_mail_name)
        conf = tpl.render()
        logger.info("{} configuration has changed, writing new "
                    "one".format(self.service_mail_name))
        write_in_file(path, conf)
        logger.info("New {} configuration successfully applied"
                    "".format(self.service_mail_name))

        # ### Write the first template (ssmtp.conf)
        tpl, path = tpl_utils.get_template(self.service_name)
        conf = tpl.render(conf=parameters, conf_service=service_settings)
        logger.info("{} configuration has changed, writing new one".format(self.service_name))
        write_in_file(path, conf)
        logger.info("New {} configuration successfully applied".format(self.service_name))

    def conf_has_changed(self, parameters, service_settings=None, conf_django=None):
        tpl, path = tpl_utils.get_template(self.service_mail_name)
        conf = tpl.render()
        try:
            with open(path, 'r') as f:
                orig_conf = f.read()
            if orig_conf != conf:
                return conf
        except Exception as e:
            logger.error("Unable to check if conf has changed for {}: ".format(self.service_mail_name, str(e)))
            logger.exception(e)
            if "No such file" in str(e):
                raise ServiceNoConfigError(str(e))
            raise ServiceConfigError("Cannot open '{}' for service '{}' : {}".format(path, self.service_mail_name,
                                                                                     str(e)))
        main_changed = super(SMTP, self).conf_has_changed(parameters, service_settings, conf_django)
        if "No such file" in main_changed:
            raise ServiceNoConfigError(main_changed)
        elif "Unable to check if conf has changed" in main_changed:
            raise ServiceConfigError(main_changed)

    def restart_service(self, service_name=None):
        """ There is not service smtp """
        return "UP", "Configuration applied."

    def status(self, parameters=None):
        """ Give status of service
        :param parameters: 
        :return: 
        """
        # Looking if configuration are iso between file and database
        if parameters is not None:
            try:
                need_update = self.conf_has_changed(parameters)
                if need_update:
                    return "NEED_UPDATE", "Configuration is not the same on disk."
            except ServiceNoConfigError as e:
                return "NOT_CONFIGURED", "Please SAVE to configure."
            except ServiceConfigError as e:
                return "NEED_UPDATE", str(e)
        return "UP", "Configuration applied."

    def stop_service(self, service_name=None):
        """ """
        return "DOWN", "Service stopped."

    def start_service(self, service_name=None):
        """ """
        return "UP", "Service started."
