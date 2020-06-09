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

import errno
import os
import re
import shutil
import subprocess

import requests

from gui.models.system_settings import Cluster
from vulture_toolkit.update_api.update_utils import UpdateUtils, UpdateAPIError
from vulture_toolkit.update_api.updater_base import UpdaterBase


class GUIUpdater(UpdaterBase):

    install_path = '/home/vlt-gui/'
    key_name = 'GUI'

    def is_up2date(self, version=None):
        """ Method used to check if an GUI update is available.
        Download it if available

        :return: UP2DATE if GUI is up to date, version number otherwise
        (ex GUI-0.1)
        """
        status, data = UpdateUtils.api_call("GUI")
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

                base_url = "https://download.vultureproject.org/v3/{}{}/".format(os_version,source_branch)
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
                    self.logger.info("New GUI version successfully decrypted."
                                     " version: {}".format(version))
                    return version
                else:
                    self.logger.error("Unable to download file '{}' : HTTP status != 200".format(filename))
            else:
                self.logger.info("GUI: No update available")
                return 'UP2DATE'
        else:
            raise UpdateAPIError("Error has occurred during connection to "
                                 "update server, error: {}".format(data))

    @property
    def current_version(self):
        """ Return current version of Vulture GUI package

        :return:
        """
        try:
            f = open("/home/vlt-gui/vulture/vulture/version")
            content = f.read()
            if re.match("^GUI-[0-9.]+$", content):
                return content.strip()
            else:
                return 'N/A'
        except Exception as e:
            self.logger.error("Unable to found GUI version, "
                              "error: {}".format(e))
            self.logger.exception(e)
            return 'N/A'

    def pre_install(self):
        """ Pre-install part. During this part, all files
        of '/home/vlt-gui/vulture' are copied to
        /var/vdownload/backup/{{version_name}} then '/home/vlt-gui/vulture'
        is deleted

        :return:
        """
        self.logger.info("Starting Pre-install")
        super(GUIUpdater, self).pre_install()
        src_path = '/home/vlt-gui/vulture/'
        self.backup(src_path)
        try:
            shutil.rmtree(src_path)
        except Exception as e:
            self.logger.error("An error has occurred during current version"
                              "deletion")
            self.logger.exception(e)
        self.logger.info("End of Pre-install")

    def post_install(self):
        """ Post-install part. During this part we copy some Vulture GUI
        files from previous version to new installed version

        :return:
        """
        self.logger.info("Starting Post-install")
        super(GUIUpdater, self).post_install()
        src_path = '/home/vlt-gui/vulture/vulture/'
        backup_path = "{}/{}/vulture/".format(self.backup_path, self.previous_version)
        # Restoring configuration files from backup of previous version
        files = [
            'secret_key.py',
            'mongodb.conf',
            'mongodb.conf.dead'
        ]
        for filename in files:
            path = "{}/{}".format(backup_path, filename)
            try:
                shutil.copy2(path, src_path)
            except IOError as e:
                if filename == 'mongodb.conf.dead':  # file is not mandatory
                    pass
                else:
                    raise

        # Restoring portal templates
        tpl_path = '/home/vlt-gui/vulture/portal/templates/'
        tpl_backup_path = "{}/{}/portal/templates/".format(self.backup_path, self.previous_version)
        shutil.rmtree(tpl_path)
        shutil.copytree(tpl_backup_path, tpl_path)

        # Applying rights to GUI folder
        os.system("chown -R vlt-gui:vlt-gui /home/vlt-gui/vulture/")
        # Executing some migration scripts
        self.execute_migration_scripts()
        os.system("chown -R root:wheel /home/vlt-gui/vulture/vulture_toolkit/update_api/update_scripts/")
        # Restarting GUI and Portal processes

        self.logger.info("Restarting Vulture GUI")
        os.system("service vulture restart")
        self.logger.info("Restarting Vulture Engine")
        os.system("/home/vlt-sys/Engine/bin/httpd -f /home/vlt-sys/Engine/conf/portal-httpd.conf -k restart")
        self.logger.info("End of Post-install")

    def execute_migration_scripts(self):
        """ Method used to execute migration scripts. This method browse update_scripts
         folders and execute appropriate scripts. Scripts are from last deployed
         version

        """
        scripts_path = '/home/vlt-gui/vulture/vulture_toolkit/update_api/update_scripts/'
        directory_list = os.listdir(scripts_path)
        for directory in sorted(directory_list):
            path = "{}{}".format(scripts_path, directory)
            if os.path.isdir(path):
                reg = re.compile("^GUI-(?P<major>[0-9]+)\.(?P<minor>[0-9]+)$")
                test_major, test_minor = reg.match(directory).groups()
                # We execute only scripts with appropriate version.
                # IE: if migrate from GUI-0.2 to GUI-0.4, we will execute
                # only GUI-0.3 and GUI-0.4 scripts
                if self.is_between_version(test_major, test_minor):
                    # Retrieve source branch to send-it in parameter for update scripts
                    # Used by maj_vulture-LIBS.sh
                    cluster = Cluster.objects.get()
                    source_branch = cluster.system_settings.global_settings.source_branch
                    if str(source_branch) != "" and str(source_branch)[0] != '/':
                        source_branch = "/" + str(source_branch)

                    self.logger.info("{} directory in update scripts".format(directory))
                    scripts_list = os.listdir(path)
                    for f in sorted(scripts_list):
                        absolute_path = "{}/{}".format(path, f)
                        self.logger.info("Executing: {} ...".format(absolute_path))
                        os.system("{} {}".format(absolute_path, source_branch))
                else:
                    self.logger.info("{} directory not in update scripts".format(directory))
            else:
                self.logger.warning("{} isn't a directory".format(directory))
        self.logger.info("Migration scripts execution ended.")

    def restore_previous_version(self):
        dst_path = '/home/vlt-gui/vulture/'
        try:
            shutil.rmtree(dst_path)
        except Exception as e:
            self.logger.error("An error has occurred during restore process."
                              "Unable to delete some files")
            self.logger.exception(e)

        backup_path = "{}/{}/vulture/".format(self.backup_path, self.previous_version)
        try:
            shutil.copytree(backup_path, dst_path)
        except (OSError, shutil.Error) as e:
            if e.errno == errno.ENOTDIR:
                shutil.copy(backup_path, dst_path)
            else:
                self.logger.error("An error occurred during restore of "
                                  "previous version")
                self.logger.exception(e)
        except Exception as e:
            self.logger.error("An error occurred during restore of "
                              "previous version")
            self.logger.exception(e)

    def is_between_version(self, tested_major, tested_minor):
        """ Method used to check if provided version is between previous and
        current version.

        :param tested_major: major version of Vulture GUI
        :param tested_minor: minor version of Vulture GUI
        :return: True if provided version is in interval, False otherwise
        """
        reg = re.compile("^GUI-(?P<major>[0-9]+)\.(?P<minor>[0-9]+)$")
        initial_major, initial_minor = reg.match(self.previous_version).groups()
        last_major, last_minor = reg.match(self.current_version).groups()
        # converting to int
        initial_major = int(initial_major)
        initial_minor = float("0.{}".format(initial_minor))
        last_major = int(last_major)
        last_minor = float("0.{}".format(last_minor))
        tested_major = int(tested_major)
        tested_minor = float("0.{}".format(tested_minor))
        # comparing version
        if initial_major > tested_major:
            return False
        elif initial_major == tested_major == last_major:
            return initial_minor < tested_minor <= last_minor
        elif initial_major <= tested_major <= last_major:
            pass  # FIXME NOT IMPLEMENTED

    def is_version_greater(self, new_version):
        """ Method used to check if provided version is greater than current version.

        :param major_version: downloaded version of Vulture Engine
        :return: True if provided version is greater than current, False otherwise
        """
        reg = re.compile("^GUI-(?P<major>[0-9]+)\.(?P<minor>[0-9]+)$")
        current_major, current_minor = reg.match(self.current_version).groups()
        new_major, new_minor = reg.match(new_version).groups()
        # comparing version
        if int(new_major) > int(current_major):
            return True
        if float("0.{}".format(new_minor)) > float("0.{}".format(current_minor)):
            return True
        return False
