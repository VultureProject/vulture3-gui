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
__author__ = "Jérémie Jourdin, Kevin Guillemot"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = 'KERBEROS authentication wrapper'


# Django system imports

# Django project imports
from .base_auth  import BaseAuth

# Required exceptions imports
from .exceptions import AuthenticationError, ChangePasswordError, UserNotFound

# Extern modules imports
from base64      import b64decode
from subprocess  import Popen, PIPE
from os          import system, remove
from kerberos    import authGSSServerInit, authGSSServerStep, authGSSServerUserName, authGSSServerResponse, authGSSServerClean, changePassword
from hashlib     import sha1
from json        import dumps

# Logger configuration imports
import logging
logger = logging.getLogger('portal_authentication')


class KerberosClient(BaseAuth):
    def __init__(self, settings, **kwargs):
        """ Instantiation method

        :param settings:
        :return:
        """
        if len(kwargs) != 0 :
            super(KerberosClient, self).__init__(**kwargs)

        self.realm = settings.realm
        self.krb5_service = settings.krb5_service


    def authenticate(self, username, password, **kwargs):
        """ Authentication method for Kerberos backend

        :param username: String with username
        :param password: String with password
        :return:True if authentication succeed, None otherwise
        """
        backend_id = kwargs['backend_id']
        # Hash "backend_id"+"username" to get the filename of tgt
        ccname = "/tmp/krb5cc_"+sha1("{}{}".format(backend_id, username).encode('utf8')).hexdigest()
        logger.debug("Trying to authenticate username {}".format(username))

        tgt = self.create_tgt_from_creds(username, password, ccname)

        if tgt is None:
            logger.error("KerberosClient::authenticate: Kerberos authentication for {} failed".format(username))
            raise AuthenticationError("Credentials not valid or invalid configuration")
        else:
            logger.debug("KerberosClient::authenticate: TGT successfully retrieven/created with credentials")
            logger.info("KerberosClient::authenticate: Successfull authentication for username {}".format(username))
            return {
                'dn' : username,
                'user_phone' : 'N/A',
                'user_email' : username+'@'+self.realm,
                'password_expired' : False,
                'account_locked' : False
            }


    def test_user_connection(self, username, password):
        """ Method used to check user's password against Kerberos
        :param username: String with username
        :param password: String with password
        """
        response = {
            'status': None,
            'reason': None,
        }

        try:
            response['status'] = True
            response['data']   = dumps(self.authenticate(username, password, backend_id="test"), indent=2)
        except AuthenticationError as e:
            response['status'] = False
            response['reason'] = str(e)
        except Exception as e:
            response['status'] = False
            response['reason'] = str(e)

        return response


    def verify_token(self, logger, token):
        """ Method used to verify token against KDC
        :param token: Base64 encoded token (don't decoded it)
        :return If authentication succeed, dict with {'token_resp':the base64 encoded reponse from KDC, 'user':username of client}
        """
        # Initialize context with service
        res = dict()
        username = ""

        try:
            result, context = authGSSServerInit("HTTP@"+self.krb5_service)
            if result != 1:
                logger.error("KerberosClient::verify_token: authGSSServerInit(HTTP@{}) failed with status code : {}".format(str(self.krb5_service), str(result)))
                return res

            result = authGSSServerStep(context, token)
            if result != 1:
                logger.error("KerberosClient::verify_token: authGSSServerStep(token) failed with status code : {}".format(str(result)))
                return res
            # Retrieve username of authenticated user
            username = authGSSServerUserName(context)
            # Retrieve KDC response
            kdc_response = authGSSServerResponse(context)
            # Clean kerberos context
            authGSSServerClean(context)

        except Exception as e:
            logger.error("KerberosClient::verify_token: Verify token against KDC failed : {}".format(str(e)))
            return res

        logger.info("KerberosClient::verify_token: Successfull authentication for username {}".format(username))
        return {
                'dn'              : username,
                'user_phone'      : 'N/A',
                'user_email'      : username if '@' in username else username+'@'+self.realm,
                'password_expired': False,
                'account_locked'  : False,
                'token_resp'      :kdc_response
            }


    def create_tgt_from_creds(self, username, password, ccname, app_service=None):
        """ Method used to create tgt with given credentials if necessary
            And retrieve the base64-encoded tgt from cache to send-it over HTTP header.
        :param username: Username
        :param password: Password
        :return tgt: The retrieved tgt, or None"""

        #"""If the user is already authenticated, there is a tgt in cache for this user : so retrieve-it !"""
        #tgt = self.retrieve_tgt_from_cache(ccname, service)
        service = app_service or self.krb5_service

        """Create the tgt with kinit"""
        proc = Popen(['/bin/echo "' + password + '" | /usr/bin/kinit -S '+"HTTP/{}".format(service)+
                                 ' -c '+ccname+' --password-file=STDIN ' + username],
                                stdout=PIPE, stderr=PIPE, shell=True)
        success, error = proc.communicate()

        if not error:
            tgt = self.retrieve_tgt_from_cache(ccname, service)
            logger.debug("KerberosClient::create_tgt_from_creds: TGT successfully retrieven in cache for service '{}'".format(service))
            try:
                system("/usr/bin/chgrp daemon " + ccname)
                system("/bin/chmod 640 " + ccname)
            except Exception as e:
                logger.error("KerberosClient::create_tgt_from_creds: Unable to set permissions on {} file : {}".format(ccname, str(e)))
        else:
            logger.error("KerberosClient::create_tgt_from_creds: Kinit error for user {} : {}".format(username, error.decode('utf8')))
            return None

        return tgt


    def retrieve_tgt_from_cache(self, cachefile, app_service):
        """ Method used to retrieve tgt from cache for given user
        param: Username
        return: Retrieved tgt, or None"""
        tgt = None
        proc = Popen(['/usr/local/bin/sudo', '-u', 'vlt-sys', '/usr/local/bin/sudo',
                                 '/home/vlt-sys/scripts/get_tgt', cachefile, "HTTP@"+app_service],
                                stdout=PIPE,
                                stderr=PIPE)
        res, errors = proc.communicate()
        res = res.decode('utf8')
        if not errors:
            tgt = res.replace("TGT=", "").rstrip()
        else:
            logger.error("KerberosClient::retrieve_tgt_from_cache: Error while retrieving tiquet for service {} : {}".format(app_service,str(errors)))

        return tgt


    def change_password(self, username, old_password, new_password, ccname, app_service):
        if not changePassword(username+"@"+self.realm, old_password, new_password):
            raise ChangePasswordError("Password cannot be changed")

        try:
            system("/bin/rm "+ccname)
        except:
            pass

        # Replace the tgt in cache with the new password
        self.create_tgt_from_creds(username, new_password, ccname, "HTTP/"+str(app_service))

        return True


    def search_user_by_email(self, email):
        tmp = email.split('@')
        username = tmp[0]
        domain   = tmp[1]

        if domain.lower() == self.realm.lower():
            return username

        raise UserNotFound("Bad domain for email '{}'".format(email))


def test_keytab(keytab):
    """ Method used to check keytab content
    :param keytab: String base64 encoded keytab
    """
    response = {
        'status': None,
        'reason': None,
    }
    if keytab is None:
        response['status'] = False
        response['reason'] = "Keytab file is empty"
        return response
    try:
        with open('/tmp/tmp_keytab', 'wb') as f:
            f.write(b64decode(keytab))

        proc = Popen(['/usr/sbin/ktutil', '-k', '/tmp/tmp_keytab',
                                 'list'], stdout=PIPE,
                                stderr=PIPE)
        res, errors = proc.communicate()
        if not errors:
            res = res.decode('utf8')
            if len(res.split('\n')) > 2 :
                res = '\n'.join(res.split('\n')[2:])
            response['status'] = True
            response['reason'] = res
        else:
            response['status'] = False
            response['reason'] = errors.decode('utf8')
    except Exception as e:
        logger.exception(e)
        response['status'] = False
        response['reason'] = str(e)
    finally:
        try:
            remove('/tmp/tmp_keytab')
        except Exception as e:
            logger.error("CONF::Kerberos: Unable to remove the '/tmp/tmp_keytab' file: "
                         "If it already exists you should delete it for security reason! "
                         "Reason of failure: {}".format(str(e)))
    return response


def import_keytab(logger, keytab):
    """ Method used to check keytab content
    :param keytab: String base64 encoded keytab
    """
    response = False
    tmp_keytab = '/tmp/tmp_keytab'

    try:
        #decoded_keytab = b64decode(keytab)
        with open(tmp_keytab, 'wb') as f:
            f.write(b64decode(keytab))

        proc = Popen(['/usr/local/bin/sudo', '-u', 'vlt-sys', '/usr/local/bin/sudo',
                                 '/home/vlt-sys/scripts/copy_keytab.sh', tmp_keytab],
                                stdout=PIPE,
                                stderr=PIPE)
        res, errors = proc.communicate()
        if not errors:
            response = True
            logger.debug("CONF::Kerberos: Copy of {} to /etc/krb5.keytab stdout :{}".format(str(tmp_keytab),str(res)))
        else:
            logger.error("CONF::Kerberos: Fail to import keytab, reason : {}".format(str(errors)))
    except Exception as e:
        logger.info("CONF::Kerberos: Fail to import keytab, reason : {}".format(str(e)))

    return response



