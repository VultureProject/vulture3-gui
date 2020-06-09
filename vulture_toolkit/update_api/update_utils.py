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

import binascii
import json
import logging
import os
import re
import subprocess
import tempfile

from requests import Request, Session
from gui.models.system_settings import Cluster


logger = logging.getLogger('cluster')


class UpdateAPIError(Exception):
    pass


class SymmetricDecryptFailure(UpdateAPIError):
    pass


class AsymmetricDecryptFailure(UpdateAPIError):
    pass


class UpdateUtils(object):

    @staticmethod
    def get_api_key():
        """ Return API key.
        API key is in binary format. We need to convert it into string before
        returning it

        :return: String containing API Key, or None in case of error
        """
        try:
            proc = subprocess.Popen(['/usr/local/bin/sudo', '-u', 'vlt-sys',
                                     '/usr/local/bin/sudo', '/home/vlt-sys/scripts/get_content',
                                     'api_key'], stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            res, errors = proc.communicate()
            res = res.decode('utf8')
            errors = errors.decode('utf8')
            if errors:
                raise UpdateAPIError("Unable to retrieve API Key, error: {}".format(errors))
            else:
                content = int(res, 2)
                api_key = binascii.unhexlify('%x' % content)
                return api_key.decode('utf8')
        except Exception as e:
            raise UpdateAPIError("Unable to retrieve API Key, error: {}".format(e))

    @staticmethod
    def get_private_key():
        """ Return Private key.
        API Private key is in binary format. We need to convert it into string before
        returning it

        :return: String containing API Private Key, or None in case of error
        """
        try:
            proc = subprocess.Popen(['/usr/local/bin/sudo', '-u', 'vlt-sys',
                                     '/usr/local/bin/sudo', '/home/vlt-sys/scripts/get_content',
                                     'priv_key'], stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            res, errors = proc.communicate()
            res = res.decode('utf8')
            errors = errors.decode('utf8')
            if errors:
                raise UpdateAPIError("Unable to retrieve private key, error: {}".format(errors))
            else:
                content = int(res, 2)
                priv_key = binascii.unhexlify('%x' % content)
                return priv_key.decode('utf8')
        except Exception as e:
            raise UpdateAPIError("Unable to retrieve private Key, error: {}".format(e))

    @staticmethod
    def get_api_email():
        """ Return API email.
        API email is in binary format. We need to convert it into string before
        returning it

        :return: String containing API Key, or None in case of error
        """
        try:
            proc = subprocess.Popen(['/usr/local/bin/sudo', '-u', 'vlt-sys',
                                     '/usr/local/bin/sudo', '/home/vlt-sys/scripts/get_content',
                                     'api_email'], stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            res, errors = proc.communicate()
            res = res.decode('utf8')
            errors = errors.decode('utf8')
            if errors:
                raise UpdateAPIError("Unable to retrieve API Email, error: {}".format(errors))
            else:
                content = int(res, 2)
                api_email = binascii.unhexlify('%x' % content)
                return api_email.decode('utf8')
        except Exception as e:
            raise UpdateAPIError("Unable to retrieve API Email, error: {}".format(e))

    @staticmethod
    def get_proxy_conf():
        proxy = None
        if os.path.exists("/etc/rc.conf"):
            http_proxy  = None
            https_proxy = None
            ftp_proxy   = None
            try:
                tmp = open("/etc/rc.conf").read()
                lst = re.findall('http_proxy="(.*)"', tmp)
                if len(lst):
                    http_proxy = lst[0]
                    if http_proxy == "":
                        http_proxy = lst[1]

                lst = re.findall('https_proxy="(.*)"', tmp)
                if len(lst):
                    https_proxy = lst[0]
                elif http_proxy:
                    https_proxy = http_proxy
                
                lst = re.findall('ftp_proxy="(.*)"', tmp)
                if len(lst):
                    ftp_proxy = lst[0]
                elif http_proxy:
                    ftp_proxy = http_proxy

                if http_proxy and "://" not in http_proxy:
                    http_proxy = "http://" + http_proxy
                if https_proxy and "://" not in https_proxy:
                    https_proxy = "http://" + https_proxy
                if ftp_proxy and "://" not in ftp_proxy:
                    ftp_proxy = "http://" + ftp_proxy

                proxy = {
                    "http" : http_proxy,
                    "https": https_proxy,
                    "ftp"  : ftp_proxy
                }

            except:
                pass

        return proxy

    @staticmethod
    def api_call(type_of_update):
        """Call to register API, this API is used to register Vulture product
        and to download Vulture's source
        """

        cluster = Cluster.objects.get()
        source_branch = cluster.system_settings.global_settings.source_branch
        if str(source_branch) != "":
            source_branch="/"+str(source_branch)

        proc=subprocess.Popen(['freebsd-version','-k'], stdout=subprocess.PIPE)
        res,error=proc.communicate()
        res = res.decode('utf8')
        os_version=re.sub(r"-.*","",res.rstrip())
        api_url = "https://download.vultureproject.org/v3/{}{}/Vulture-{}.latest".format(os_version,
                                                                                         source_branch,
                                                                                         type_of_update)

        error_msg = "The request to Register API failed, error: {}"
        try:
            session   = Session()
            req       = Request('GET', api_url, headers={'X-Vlt-User': UpdateUtils.get_api_email()}).prepare()
            proxies   = UpdateUtils.get_proxy_conf()
            response  = session.send(req, verify=True, proxies=proxies)
            result = response.text

            if response.status_code == 200:
                return True, result
            else:
                return False, result
        except Exception as e:
            error = error_msg.format(e)
            logger.exception(e)
        return False, error

    @staticmethod
    def symmetric_decrypt(file_path, key):
        """Decrypt file encrypted by a symmetric key using AES256 CBC.

        :param file_path: string with path to encrypted file
        :param key: key used to encrypt file
        :return: NamedTemporaryFile containing decrypted content
        """
        import hashlib

        target_file = tempfile.NamedTemporaryFile()
        # IV creation from key, convert values in hex because openssl require it
        iv_hash = hashlib.sha1(key).hexdigest()
        iv = binascii.hexlify(iv_hash[:16])
        key = binascii.hexlify(key)
        # Decryption process
        proc = subprocess.Popen(
            ['/usr/bin/openssl', 'enc', '-aes-256-cbc', '-d', '-a', '-in',
             file_path, '-out', target_file.name, '-nosalt',
             '-K', key, '-iv', iv], stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        res, error = proc.communicate()
        if not error:
            return target_file
        else:
            raise SymmetricDecryptFailure(error.decode('utf8'))

    @staticmethod
    def asymmetric_decrypt(data, key):
        """Decrypt data encrypted using asymmetric keys

        :param data: data to decrypt
        :param key: string containing private key in PEM format
        :return: True and decrypted data in case of success, False and error_msg
        otherwise
        """
        try:
            from M2Crypto import BIO, RSA

            private_key = BIO.MemoryBuffer(key)
            key = RSA.load_key_bio(private_key)
            decrypted = key.private_decrypt(data, RSA.pkcs1_padding)
            return decrypted
        except Exception as error_msg:
            raise AsymmetricDecryptFailure(error_msg)

    @staticmethod
    def check_updates():
        """ Method used to check update for Vulture components (GUI, Engine,
        libs...)

        :return: A dict with update status
        """
        from vulture_toolkit.update_api.gui_updater import GUIUpdater
        from vulture_toolkit.update_api.engine_updater import EngineUpdater
        results = {}
        update_checks = (
            GUIUpdater(),
            EngineUpdater()
        )
        for check in update_checks:
            results[check.key_name] = check.is_up2date()
        return results

    @staticmethod
    def get_updater(update_type):
        """ Method used as a factory. It returns Updater object in order
        to perform update operation

        :param update_type: Type of searched updater (ex: gui)

        :return: A Updater instance. (ex: GuiUpdater)
        """
        from vulture_toolkit.update_api.gui_updater import GUIUpdater
        from vulture_toolkit.update_api.engine_updater import EngineUpdater

        updaters = {
            'gui': GUIUpdater(),
            'engine': EngineUpdater()
        }
        updater_inst = updaters.get(update_type)
        if not updater_inst:
            raise UpdateAPIError("Unable to find updater")
        else:
            return updater_inst
