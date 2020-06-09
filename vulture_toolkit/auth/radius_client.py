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
__doc__ = 'Radius authentication client wrapper'

# Logger configuration
import logging
#logging.config.dictConfig(settings.LOG_SETTINGS)
logger = logging.getLogger('portal_authentication')

# Import pyrad (radius python library)
from radius import Radius, ATTR_REPLY_MESSAGE, CODE_ACCESS_ACCEPT, SocketError

from .exceptions import AuthenticationError
from .base_auth import BaseAuth


class RadiusClient(BaseAuth):

    def __init__(self, settings):
        """ Instantiation method

        :param settings:
        :return:
        """
        # Connection settings
        self.host = settings.radius_host
        self.port = settings.radius_port
        self.nas_id = settings.radius_nas_id
        self.secret = settings.radius_secret
        self.max_retry = settings.radius_retry
        self.max_timeout = settings.radius_timeout

    def authenticate(self, username, password, **kwargs):
        # """Authentication method of LDAP repository, which returns dict of specified attributes:their values
        # :param username: String with username
        # :param password: String with password
        # :param oauth2_attributes: List of attributes to retrieve
        # :return: None and raise if failure, server message otherwise
        # """
        logger.debug("Trying to authenticate username {}".format(username.encode('utf-8')))
        # try:
        # Create client
        srv = Radius(self.secret, host=self.host, port=self.port, retries=self.max_retry, timeout=self.max_timeout)

        # Authentication
        if not srv.authenticate(username, password):
            logger.error("RADIUS_CLI::authenticate: Authentication failure for user '{}'".format(username))
            raise AuthenticationError("Authentication failure on Radius backend for user '{}'".format(username))

        logger.info("RADIUS_CLI::authenticate: Autentication succeed for user '{}'".format(username))
        # except Timeout:
        #     raise Timeout
        # except Exception, e:
        #     logger.error("Unable to authenticate username {} : exception : {}".format(username, str(e)))

        return {
            'dn': username,
            'user_phone': 'N/A',
            'user_email': 'N/A',
            'password_expired': False,
            'account_locked': False
        }


    def test_user_connection(self, username, password):
        """ Method used to perform test search over RADIUS Repository
        :param username: String with username
        :param password: String with password
        """
        logger.debug("Radius_authentication_test::Trying to authenticate username {}".format(username.encode('utf-8')))
        response = {
            'status': None,
            'reason': None
        }
        try:
            # Create client
            srv = Radius(self.secret, host=self.host, port=self.port, retries=self.max_retry, timeout=self.max_timeout)

            # We do NOT use authenticate, to retrieve the server' answer
            reply = srv.send_message(srv.access_request_message(username, password))

            logger.debug("Radius_authentication_test:: Username:{}, return code:{}".format(username, reply.code))

            msg = ""
            if reply.code == CODE_ACCESS_ACCEPT:
                response['status'] = True
                reply_msg = reply.attributes.get(ATTR_REPLY_MESSAGE)
                if not isinstance(reply_msg, list):
                    reply_msg = [reply_msg]
                for r in reply_msg:
                    if isinstance(r, bytes):
                        msg += r.decode('utf8')

                logger.info("RADIUS::Auth: Authentication succeed for user {}, reply = {}".format(username, msg))
            else:
                response['status'] = False
                msg = "Authentication failed"
                logger.info("RADIUS::Auth: Authentication failure for user {}".format(username))

            response['reason'] = msg

        except SocketError:
            response['status'] = False
            logger.info("RADIUS::Auth: Authentication failure for user {} : Timeout expired while connecting".format(username))
            response['reason'] = "Timeout expired while connecting"

        except Exception as e:
            response['status'] = False
            logger.error("Radius_authentication_test::Unable to authenticate username:{}, exception:{}".format(username, str(e)))
            response['reason'] = "Exception : " + str(e)

        return response
