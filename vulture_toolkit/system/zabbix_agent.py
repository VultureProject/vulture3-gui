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
__author__ = "Kevin Guillemot"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = 'Zabbix-Agent Toolkit'

# Django system imports

# Django project imports
from vulture_toolkit.system.service_base import ServiceBase
from vulture_toolkit.templates import tpl_utils
from gui.models.ssl_certificate import SSLCertificate

# Required exceptions imports
from vulture_toolkit.system.exceptions import ServiceConfigError, ServiceStartError, ServiceStopError

# Extern modules imports
from re import search as re_search
from subprocess import Popen, PIPE
from sys import path as sys_path
sys_path.append("/home/vlt-gui/vulture")

# Logger configuration imports
import logging
logger = logging.getLogger('services_events')


class ZABBIX(ServiceBase):
    """ Class wrapper for Zabbix_agentd service 
    """
    def __init__(self):
        self.service_name = "zabbix_agentd"
        self.config_path = "/usr/local/etc/zabbix4"


    def write_configuration(self, parameters, service_settings=None, text_config=None):
        template, path_template = tpl_utils.get_template(self.service_name)

        if not text_config:
            try:
                parameters = self.write_certificate(parameters)
            except Exception as e:
                logger.error("Failed to write Zabbix certificate files :")
                logger.exception(e)
                raise ServiceConfigError(str(e))

            text_config = template.render({'conf': parameters})

        logger.info("[ZABBIX] Writing configuration file '{}'".format(path_template))
        try:
            # The called function must raise !
            self.write_configuration_file(path_template, text_config)
        except Exception as e:
            logger.error("Failed to write Zabbix configuration file '{}' :".format(path_template))
            logger.exception(e)
            raise ServiceConfigError(str(e))


    def write_certificate(self, zabbix_options):
        def passed(options):
            return options
        option_functions = {
            'cert': self.perform_cert_options,
            'psk': self.perform_psk_options,
        }
        zabbix_options = option_functions.get(zabbix_options['tls_accept'], passed)(zabbix_options)
        return option_functions.get(zabbix_options['tls_connect'], passed)(zabbix_options)


    def perform_cert_options(self, zabbix_options):
        certificate_files = {
            'chain': "{}/pki/ca_cert.crt".format(self.config_path),
            'cert': "{}/pki/cert.crt".format(self.config_path),
            'key': "{}/pki/cert.key".format(self.config_path),
            'crl': "{}/pki/cert.crl".format(self.config_path)
        }
        # Retrieve SSLCertificate object
        ssl_cert = SSLCertificate.objects(id=zabbix_options.get('tls_cert')).only(*certificate_files.keys()).first()
        for attribute_name in certificate_files.keys():
            self.write_configuration_file(certificate_files[attribute_name], getattr(ssl_cert, attribute_name))
        # If CRL is not present, set the crl empty
        if not ssl_cert.crl:
            certificate_files['crl'] = ""
        # Replace SSLCertificate object by dict for template use
        zabbix_options['tls_cert_file'] = certificate_files
        return zabbix_options


    def perform_psk_options(self, zabbix_options):
        psk_key_path = "{}/pki/psk.key".format(self.config_path)
        self.write_configuration_file(psk_key_path, zabbix_options.get('psk_key'))
        zabbix_options['psk_file'] = psk_key_path
        return zabbix_options


    def write_configuration_file(self, filepath, content):
        """Write content into file. Used to create/update configuration files
        !!! Warning, for security purpose filename have to be in allowed files list
         present in write_configuration_file script !!!

        :param filepath: complete path to file (ie: path + filename)
        :param content: a string containing content
        :return:
        """
        proc = Popen(['/usr/local/bin/sudo', '-u', 'vlt-sys', '/usr/local/bin/sudo',
                                 '/home/vlt-sys/scripts/write_configuration_file',
                                 filepath, content], stdout=PIPE, stderr=PIPE)
        res, errors = proc.communicate()

        if not errors:
            logger.info("[ZABBIX] Configuration file {} successfully written.".format(filepath))
            return True
        else:
            raise Exception("Write configuration file {} failed : {}".format(str(filepath), str(errors)))


    def status(self, parameters=None):
        """ Service status

        :returns: status of service (UP, DOWN, ERROR, UNKNOWN, NEED_UPDATE) and return of system command
        """
        if parameters:
            try:
                if self.conf_has_changed(parameters):
                    return "NEED_UPDATE", "Configuration differs on disk"
            except ServiceConfigError as e:
                return "ERROR", "Cannot {}: {}".format(e.trying_to, str(e))

        # Executing service service_name status as vlt-sys user
        proc = Popen(['/usr/local/bin/sudo', '-u', 'vlt-sys', '/usr/local/bin/sudo',
                      'service', self.service_name, 'onestatus'], stdout=PIPE, stderr=PIPE)
        success, error = proc.communicate()
        success = success.decode('utf8')
        if success:
            logger.info("[ZABBIX] Status of service: {}".format(success))
            m = re_search('{} is (not )?running'.format(self.service_name), success)
            if m:
                status = "UP" if not m.group(1) else "DOWN"
                logger.debug("[ZABBIX] Status successfully retrieved : {}".format(status))
            else:
                status = "UNKNOWN"
                logger.error("[ZABBIX] Status unknown, STDOUT='{}', STDERR='{}'".format(success, error))

        elif error:
            """ Something were wrong during service call"""
            status = "ERROR"
            success = "{}".format(str(error))
            logger.error("[ZABBIX] - Error in status ! STDOUT:'{}', STDERR:'{}'".format(str(success), str(error)))

        else:
            """ Service status is unknown"""
            status = "UNKNOWN"
            logger.error("[ZABBIX] Status unknown, STDOUT and STDERR are empty.")

        return status, success


    def conf_has_changed(self, parameters, service_settings=None, conf_django=None):
        """ Test if configuration into system configuration file is same that
        configuration in database (from parameters var)

        :param parameters: A dict containing configuration parameters
        :param service_settings: A dict containing configuration parameters, sent to tempale.render as 'conf_service'
        :param conf_django: A dict containing configuration parameters, sent to template.render as 'conf_django'
        """
        # Modify parameters according to tls/psk options
        if parameters.get('tls_accept') == 'cert' or parameters.get('tls_connect') == 'cert':
            certificate_files = {
                'chain': "{}/pki/ca_cert.crt".format(self.config_path),
                'cert': "{}/pki/cert.crt".format(self.config_path),
                'key': "{}/pki/cert.key".format(self.config_path),
                'crl': "{}/pki/cert.crl".format(self.config_path)
            }
            ssl_cert = SSLCertificate.objects(id=parameters.get('tls_cert')).only(*certificate_files.keys()).first()
            if not ssl_cert.crl:
                certificate_files['crl'] = ""
            parameters['tls_cert_file'] = certificate_files

        if parameters.get('tls_accept') == 'psk' or parameters.get('tls_connect') == 'psk':
            parameters['psk_file'] = "{}/pki/psk.key".format(self.config_path)

        global_conf_has_changed = super(ZABBIX, self).conf_has_changed(parameters, service_settings, conf_django)

        if global_conf_has_changed.startswith("Unable to check if conf has changed"):
            raise ServiceConfigError(global_conf_has_changed)

        # If the configuration file hasn't changed, check if certificate/psk files has changed
        if not global_conf_has_changed:
            if parameters.get('tls_accept') == 'cert' or parameters.get('tls_connect') == 'cert':
                for attribute_name, filename in certificate_files.items():
                    if not filename:
                        continue
                    try:
                        with open(filename, 'r') as fd:
                            orig_conf = fd.read()
                            if orig_conf != getattr(ssl_cert, attribute_name):
                                logger.info("[ZABBIX] Configuration file '{}' differs on disk".format(filename))
                                return True
                    except Exception as e:
                        # FIXME : raise Exception to say the admin "Hey, cannot read conf!" in the GUI ?
                        logger.error("[ZABBIX] Cannot check configuration on '{}' file: ".format(filename))
                        logger.exception(e)
                        # We can't read the file, but it may have been modified
                        return True

            if parameters.get('tls_accept') == 'psk' or parameters.get('tls_connect') == 'psk':
                psk_key_path = "{}/pki/psk.key".format(self.config_path)
                try:
                    with open(psk_key_path, 'r') as fd:
                        orig_conf = fd.read()
                    if orig_conf != parameters.get('psk_key'):
                        logger.info("[ZABBIX] Configuration file '{}' differs on disk".format(psk_key_path))
                        return True
                except Exception as e:
                    logger.error("[ZABBIX] Cannot check configuration on '{}' file: ".format(psk_key_path))
                    logger.exception(e)
                    # We can't read the file, but it may have been modified
                    return True
            # If none of the files has changed: return False
            return False

        # If the configuration file has changed, return True
        logger.info("[ZABBIX] Global configuration file '/usr/local/etc/zabbix4/zabbix_agentd.conf' differs on disk.")
        return True

