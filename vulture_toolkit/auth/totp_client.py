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
__author__ = "Kevin Guillemot"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = 'PyOTP wrapper (for TOTP authentication)'


# Django system imports

# Django project imports
from gui.models.repository_settings   import BaseAbstractRepository, SSOProfile
from vulture_toolkit.auth.base_auth   import BaseAuth
from vulture_toolkit.system.aes_utils import AESCipher

# Required exceptions imports
from portal.system.exceptions         import TwoManyOTPAuthFailure
from vulture_toolkit.auth.exceptions  import AuthenticationError, OTPError, RegisterAuthenticationError

# Extern modules imports
from bson import ObjectId
from pyotp                            import random_base32 as pyotp_random_base32, TOTP
from secret_key                       import SECRET_KEY

# Logger configuration
import logging
#logging.config.dictConfig(settings.LOG_SETTINGS)
logger = logging.getLogger('portal_authentication')




class TOTPClient(BaseAuth):
    def __init__(self, settings):
        """ Instantiation method

        :param settings:
        :return:
        """
        # Connection settings
        self.type = settings.otp_type
        self.otp_label = settings.otp_label


    def generate_captcha(self, user_id, email):
        return TOTP(user_id).provisioning_uri(email, issuer_name=self.otp_label)


    # WARNING : Do not touch this method, Big consequences !
    def authenticate(self, user_id, key, **kwargs):
        totp = TOTP(user_id)
        if not totp.verify(key):
            raise AuthenticationError("TOTP taped token is not valid.")

        logger.info("TOTP Token for user {} successfully verified.".format(user_id))

        # If the SSOProfile is not yet in MongoDB, set-it
        app_id = kwargs['app']
        app_name = kwargs['app_name']
        backend_id = kwargs['backend']
        login = kwargs['login']

        try:
            aes = AESCipher("{}{}{}{}{}".format(SECRET_KEY, app_id, backend_id, login, "totp"))
            encrypted_field = aes.key.hex()
            sso_profile = SSOProfile.objects.filter(encrypted_name=encrypted_field, login=login).first()
            if sso_profile:
                decrypted_value = sso_profile.get_data(sso_profile.encrypted_value, app_id, backend_id, login, "totp")
                if decrypted_value:
                    logger.debug("TOTP token for user '{}' retrieven from database.".format(login))
                    return True

            # SSOProfile not found -> Create it
            sso_profile = SSOProfile()
            sso_profile.set_data(app_id, app_name, backend_id,
                                 BaseAbstractRepository.search_repository(ObjectId(backend_id)).repo_name,
                                 login, "totp", user_id)
            logger.info("TOTP token for user {} stored in database.".format(login))
            # Save in Mongo
            sso_profile.store()
        except Exception as e:
            logger.exception(e)
            raise e

        return True


    def register_authentication(self, app_id, app_name, backend_id, login):
        """ This method interract with SSOProfile objects in Mongo """
        """ Try to retrieve the SSOProfile in internal database """
        try:
            aes = AESCipher("{}{}{}{}{}".format(SECRET_KEY, app_id, backend_id, login, "totp"))
            encrypted_field = aes.key.hex()
            sso_profile = SSOProfile.objects.filter(encrypted_name=encrypted_field, login=login).first()
            if sso_profile:
                decrypted_value = sso_profile.get_data(sso_profile.encrypted_value, app_id, backend_id, login, "totp")
                if decrypted_value:
                    return False, decrypted_value
        except Exception as e:
            logger.exception(e)
            raise e

        logger.info("TOTP secret key not found. Creating-it.")

        """ If the SSOProfile does not exists, create-it """
        try:
            # returns a 16 character base32 secret.
            # Compatible with Google Authenticator and other OTP apps
            new_key = pyotp_random_base32()
            return True, new_key
        except Exception as e:
            logger.exception(e)
            raise e
