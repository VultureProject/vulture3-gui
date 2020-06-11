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
__author__ = "Florian Hagniel"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = 'Base class for service object'


# Django system imports
from django.conf                      import settings

# Django project imports
from vulture_toolkit.templates        import tpl_utils
from vulture_toolkit.system.sys_utils import check_service_status, write_in_file

# Required exceptions imports
from vulture_toolkit.system.exceptions import (ServiceConfigError, ServiceStopError, ServiceNoConfigError,
                                               ServiceStartError)

# Extern modules imports
from hashlib                          import sha1
from subprocess                       import Popen, PIPE
from re                               import search as re_search
from os                               import system as os_system

# Logger configuration imports
import logging.config
logger = logging.getLogger('services_events')


class ServiceBase(object):

    def stop_service(self, service_name=None):
        """ Stop Service
        :returns: (True,message) if success, raise Exception otherwise
        """
        service_name2 = service_name or self.service_name
        # Executing service postfix stop as vlt-sys user
        proc = Popen(['/usr/local/bin/sudo', '-u', 'vlt-sys', '/usr/local/bin/sudo',
                      'service', service_name2, 'onestop'], stdout=PIPE, stderr=PIPE)
        success, error = proc.communicate()
        success = success.decode('utf8')
        error = error.decode('utf8')
        if success:
            logger.info("[{}] service stopped".format(service_name2))
            return "DOWN", success
        elif error:
            pattern = '{} not running'.format(service_name2)
            if not re_search(pattern, error):
                logger.error("[{}] Error stopping : {}".format(service_name2, error))
                raise ServiceStopError(str(error))
            return "DOWN", error
        else:
            return_code = proc.returncode
            if return_code == 0:
                logger.info("{} service stopped".format(service_name2))
                return "DOWN", "Service {} stopped".format(service_name2)
            else:
                logger.error("Unable to stop {} service".format(service_name2))
                raise ServiceStopError("No message, return code = {}".format(return_code))

    def start_service(self, service_name=None):
        """ Start Service

        :returns: True if success, False otherwise
        """
        if not service_name:
            service_name = self.service_name
        # Executing service service_name start as vlt-sys user
        proc = Popen(['/usr/local/bin/sudo', '-u', 'vlt-sys', '/usr/local/bin/sudo',
                      'service', service_name, 'onestart'], stdout=PIPE, stderr=PIPE)
        success, error = proc.communicate()

        if success:
            success = success.decode('utf8')
            logger.info("[{}] service started: {}".format(service_name, success))
            return "UP", success
        elif error:
            error = error.decode('utf8')
            pattern = service_name + ' already running'
            if not re_search(pattern, error):
                logger.error("[{}] Error starting : {}".format(service_name, error))
                raise ServiceStartError(str(error))
            return "UP", error
        else:
            return_code = proc.returncode
            if return_code == 0:
                logger.info("{} service started".format(service_name))
                return "UP", "Service {} started".format(service_name)
            else:
                logger.error("Unable to start {} service".format(service_name))
                raise ServiceStartError("No message, return code = {}".format(return_code))

    def restart_service(self, service_name=None):
        """ Restart Service

        :returns: True if success, False otherwise
        """
        if not service_name:
            service_name = self.service_name
        self.stop_service(service_name)
        return self.start_service(service_name)

    def status(self, parameters=None):
        """ Give status of Service

        :returns: True if Service is running, False otherwise
        """

        # Looking if configuration are iso between file and database
        if parameters is not None:
            try:
                need_update = self.conf_has_changed(parameters)
                if need_update:
                    return "NEED_UPDATE", "Configuration is not the same on disk."
            except ServiceConfigError as e:
                return "NEED_UPDATE", str(e)
        status = check_service_status(self.service_name)
        if status:
            return "UP", "Processus {} is running.".format(self.service_name)
        else:
            return "DOWN", "Processus {} is not running.".format(self.service_name)

    def write_configuration(self, parameters, service_settings=None, text_config=None):
        """ Write service configuration into system configuration file.
        Write operation occurs if configuration differs from initial file

        :param parameters: A dict containing configuration parameters
        :param service_settings: service settings used to generate template
        :param text_config: Config to use instead of template
        """
        tpl, path = tpl_utils.get_template(self.service_name)

        if text_config:
            try:
                conf_sha1 = sha1(text_config.encode('utf8')).hexdigest()
            except Exception as e:
                return False
            # Write conf to temporary file
            with open ('/tmp/{}.conf'.format(conf_sha1),'w') as f:
                f.write(text_config)
            # Set owner of that file : root:wheel
            try:
                os_system("/usr/local/bin/sudo -u vlt-sys /usr/local/bin/sudo /usr/local/bin/sudo "
                          "/usr/sbin/chown root:wheel /tmp/{}.conf".format(conf_sha1))
            except Exception as e:
                logger.error("Unable to set owner root:wheel of file '/tmp/{}.conf', error: {}".format(conf_sha1, e))

            # Mv the temporary file to configuration file
            proc=Popen(['/usr/local/bin/sudo', '-u', 'vlt-sys', '/usr/local/bin/sudo', '/usr/local/bin/sudo', '/bin/mv', '/tmp/{}.conf'.format(conf_sha1),  path], stdout=PIPE)
            res, errors = proc.communicate()
            if not errors:
                logger.info("New {} configuration successfully applied".format(self.service_name))
                return True
            else:
                logger.info("Problem during write of {} configuration".format(self.service_name))
                return False

        elif self.conf_has_changed(parameters, service_settings, conf_django=settings):
            conf = tpl.render(conf=parameters, conf_service=service_settings, conf_django=settings)

            if conf:
                logger.info("{} configuration has changed, writing new one".format(self.service_name))

                if write_in_file(path, conf):
                    logger.info("New {} configuration successfully applied".format(self.service_name))
                    return True
                else:
                    return False

    def conf_has_changed(self, parameters, service_settings=None, conf_django=None):
        """ Test if configuration into system configuration file is same that
        configuration in database (from parameters var)

        :param parameters: A dict containing configuration parameters
        :param service_settings: A dict containing configuration parameters, sent to tempale.render as 'conf_service'
        :param conf_django: A dict containing configuration parameters, sent to template.render as 'conf_django'
        """
        tpl, path = tpl_utils.get_template(self.service_name)
        conf = tpl.render(conf=parameters, conf_service=service_settings, conf_django=conf_django)
        try:
            with open(path, 'r') as f:
                orig_conf = f.read()

            if orig_conf != conf:
                return conf
            return ""

        except Exception as e:
            logger.error("Unable to check if conf has changed for {}: ".format (self.service_name, str(e)))
            logger.exception(e)
            return "Unable to check if conf has changed : {}".format(str(e))
