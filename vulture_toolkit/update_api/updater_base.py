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
import logging
import os
import shutil
import tarfile
import tempfile

from vulture_toolkit.update_api.update_utils import UpdateUtils, AsymmetricDecryptFailure, SymmetricDecryptFailure

logger = logging.getLogger('cluster')


class UpdaterBase(object):

        download_path = '/var/vdownload/'
        install_path = None
        backup_path = '/var/vdownload/backup/'
        previous_version = None
        logger = logging.getLogger('cluster')

        @staticmethod
        def decrypt(enc_key, enc_file, filename):
            """ Method in charge to decrypt key used to encrypt file then
            decrypt file

            :param enc_key: Encrypted key (used to encrypt file)
            :param enc_file: Encrypted file
            :param filename: filename of encrypted file
            :return: True in case of success, False otherwise
            """

            try:
                # Key decrypting part
                priv_key = UpdateUtils.get_private_key()
                file_key = UpdateUtils.asymmetric_decrypt(enc_key, priv_key)
                # Key is decrypted, we can use it to decrypt archive file
                f_encrypt = tempfile.NamedTemporaryFile()
                f_encrypt.write(enc_file)
                f_encrypt.flush()
                file_data = UpdateUtils.symmetric_decrypt(f_encrypt.name,
                                                          file_key)
                # Archive file is decrypted, we can write it on disk
                f = open(filename, 'wb')
                f.write(file_data.read())
                f.close()
                file_data.close()
                return True
            except AsymmetricDecryptFailure as e:
                error_msg = "An error occurred during file_key decryption, error: " \
                            "{}".format(e)
            except SymmetricDecryptFailure as e:
                error_msg = "An error occurred during file decryption, error: " \
                            "{}".format(e)
            except Exception as e:
                error_msg = "An error occurred during install process, error: " \
                            "{}".format(e)
            logger.error(error_msg)
            return False

        def install(self, version):
            """ Method in charge to install Vulture update
            Call pre_install() in engine_updater.py
            Check extraction of Engine tar
            Call post_install() in engine_updater.py
            """
            try:
                self.previous_version = self.current_version
                self.pre_install()
                path = "{}Vulture-{}.tar.gz".format(self.download_path, version)
                tfile = tarfile.open(path)
                tfile.extractall(self.install_path)
                self.post_install()
                return True
            except tarfile.TarError as e:
                self.logger.error("An error occurred during archive extraction"
                                  ", error: {}".format(e))
            except Exception as e:
                self.logger.error("An error occurred during install process, "
                                  "error: {}".format(e))
                self.logger.exception(e)
            self.restore_previous_version()
            return False

        def pre_install(self):
            """ Overrided in engine_updater.py
            """
            pass

        def post_install(self):
            """ Overrided in engine_updater.py
            """
            pass

        def restore_previous_version(self):
            pass

        def backup(self, src_path):
            """ Method used to backup current version of vulture package.
            Method copy folder contained in src_path to backup path
             attribute. Example for Engine packages (/var/vdownload/backup/Engine-2.4-2)

            :param src_path: path to backup
            """

            backup_path = "{}/{}".format(self.backup_path, self.current_version)
            if os.path.exists(backup_path):
                shutil.rmtree(backup_path)
            try:
                shutil.copytree(src_path, backup_path)
            except (OSError, shutil.Error) as e:
                if e.errno == errno.ENOTDIR:
                    shutil.copy(src_path, backup_path)
                else:
                    self.logger.error("An error occurred during backup of "
                                      "current version")
            except Exception as e:
                self.logger.error("An error occurred during backup of "
                                  "current version")
                self.logger.exception(e)