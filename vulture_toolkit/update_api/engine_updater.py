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
__doc__ = ''

import os
import re
import shutil
import subprocess

import requests

from gui.models.ssl_certificate import SSLCertificate
from gui.models.system_settings import Cluster
from vulture_toolkit.update_api.update_utils import UpdateUtils, UpdateAPIError
from vulture_toolkit.update_api.updater_base import UpdaterBase


class EngineUpdater(UpdaterBase):

    install_path = '/home/vlt-sys/'
    key_name = 'Engine'

    def is_up2date(self, version=None):
        """ Method used to check if an GUI update is available.
        Download it if available

        :return: UP2DATE if Engine is up to date, version number otherwise
        (ex GUI-0.1)
        """
        status, data = UpdateUtils.api_call("Engine")
        if status:
            new_version = data.strip()
            if self.is_version_greater(new_version):
                filename = "Vulture-{}.tar.gz".format(new_version)
                path = "{}{}".format(self.download_path, filename)
                #enc_key = data.get('key').decode('base64')
                #enc_file = data.get('file')
                # self.logger.info("GUI: Update available, trying to download-it")
                # if self.decrypt(enc_key, enc_file, path):
                #     version = filename.split('Vulture-')[1].split('.tar.gz')[0]
                #     self.logger.info("New GUI version successfully decrypted."
                #                      " version: {}".format(version))
                #     return version
                # else:
                #     self.logger.error("Unable to decrypt {}".format(filename))
                #     raise UpdateAPIError("An error has occurred during decryption"
                #                          " of GUI file. Please refers to logs "
                #                          "for additional informations")
                version = filename.split('Vulture-')[1].split('.tar.gz')[0]
                proc = subprocess.Popen(['freebsd-version', '-k'], stdout=subprocess.PIPE)
                res, error = proc.communicate()
                os_version = re.sub(r"-.*", "", res.decode('utf8').rstrip())

                cluster = Cluster.objects.get()
                source_branch = cluster.system_settings.global_settings.source_branch
                if str(source_branch) != "":
                    source_branch="/"+str(source_branch)

                base_url = "https://download.vultureproject.org/v3/{}{}/".format(os_version, source_branch)

                try:
                    response = requests.get(base_url+filename, stream=True,
                                            proxies=UpdateUtils.get_proxy_conf(),
                                            verify=False)
                except Exception as e:
                    self.logger.exception(e)

                if response.status_code == 200:
                    with open(path, 'wb') as handle:
                        for block in response.iter_content(1024):
                            handle.write(block)
                    self.logger.info("New ENGINE version successfully decrypted."
                                     " version: {}".format(version))
                    return version
                else:
                    self.logger.error("Unable to download file '{}' : HTTP status != 200".format(filename))
            else:
                self.logger.info("ENGINE: No update available")
                return 'UP2DATE'
        else:
            raise UpdateAPIError("Error has occurred during connection to "
                                 "update server, error: {}".format(data))

    @property
    def current_version(self):
        """ Return current version of Vulture Engine package

        :return:
        """
        try:
            f = open("/home/vlt-sys/Engine/version")
            content = f.read()
            if re.match("^Engine-[0-9.-]+$", content):
                return content.strip()
            else:
                return 'N/A'
        except Exception as e:
            self.logger.error("Unable to found Engine version, "
                              "error: {}".format(e))
            self.logger.exception(e)
            return 'N/A'

    def pre_install(self):
        """ Called by updater_base.py within install()
            Stop running listeners
            backup /home/vlt-sys/Engine/ and remove files inside


        :return:
        """
        self.logger.info("Pre-install: Stopping running listeners")
        os.system("/home/vlt-sys/scripts/vulture_apps_starter stop")

        super(EngineUpdater, self).pre_install()
        src_path = '/home/vlt-sys/Engine/'

        self.logger.info("Pre-install: Backup Engine")
        self.backup(src_path)
        try:
            shutil.rmtree(src_path)
        except Exception as e:
            self.logger.error("An error has occurred during current version"
                              " deletion")
            self.logger.exception(e)
        self.logger.debug("End of Pre-install")

    def post_install(self):
        """ Called by updater_base.py within install()
            Backup and restore Apache conf files
            Apply right ownerships and permissions
            Restart services
        """
        self.logger.info("Starting Post-install")
        super(EngineUpdater, self).post_install()
        src_path = '/home/vlt-sys/Engine/'
        conf_path = '{}conf'.format(src_path)
        backup_conf_path = "{}/{}/conf".format(self.backup_path,
                                               self.previous_version)
        self.logger.info("Post-install: Clearing and restoring configuration")
        shutil.rmtree(conf_path)
        shutil.copytree(backup_conf_path, conf_path)

        # Changing owner of conf directory
        self.logger.info("Post-install: Applying ownership and permissions")
        os.system("/usr/sbin/chown -R vlt-sys:vlt-conf {}".format(conf_path))
        os.system("/bin/chmod 644 {}/*".format(conf_path))

        os.system("/usr/sbin/chown -R vlt-gui:daemon {}/haproxy".format(conf_path))
        os.system("/bin/chmod 770 {}/haproxy".format(conf_path))
        os.system("/bin/chmod 640 {}/haproxy/*".format(conf_path))

        os.system("/usr/sbin/chown -R vlt-gui:vlt-conf {}/modsec".format(conf_path))
        os.system("/bin/chmod 775 {}/modsec".format(conf_path))
        os.system("/bin/chmod 644 {}/modsec/*".format(conf_path))

        os.system("/usr/sbin/chown vlt-gui:vlt-conf {}/*.conf*".format(conf_path))
        os.system("/usr/sbin/chown vlt-sys:vlt-conf {}/portal-httpd.conf".format(conf_path))
        os.system("/usr/sbin/chown vlt-sys:vlt-conf {}/gui-httpd.conf".format(conf_path))

        os.system("/usr/sbin/chown vlt-gui:daemon {}/SSL*".format(conf_path))
        os.system("/bin/chmod 640 {}/SSL*".format(conf_path))

        os.system("/usr/sbin/chown -R vlt-gui:vlt-web {}/certs".format(conf_path))
        os.system("/bin/chmod 775 {}/certs".format(conf_path))
        os.system("/bin/chmod 664 {}/certs/*".format(conf_path))

        os.system("/bin/chmod 755 {}/extra".format(conf_path))
        os.system("/bin/chmod 644 {}/extra/*".format(conf_path))

        # We can start listeners
        os.system("/home/vlt-sys/scripts/vulture_apps_starter start")

        self.logger.debug("End of Post-install")

    def is_version_greater(self, new_version):
        """ Method used to check if provided version is greater than current version.

        :param major_version: downloaded version of Vulture Engine
        :return: True if provided version is greater than current, False otherwise
        """
        reg = re.compile("^Engine-2.(?P<major>[0-9\.]+)-(?P<minor>[0-9\.]+)$")
        current_major, current_minor = reg.match(self.current_version).groups()
        new_major, new_minor = reg.match(new_version).groups()
        # comparing version
        if float(new_major) > float(current_major):
            return True
        elif int(new_minor) > int(current_minor):
            return True
        return False
