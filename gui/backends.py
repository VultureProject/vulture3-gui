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
__doc__ = 'Authentication backends wrapper'


# Django system imports

# Django project imports
from gui.models.user_document                import VultureUser as User
from vulture_toolkit.auth.authy_client       import AuthyClient
from vulture_toolkit.auth.kerberos_client    import KerberosClient
from vulture_toolkit.auth.ldap_client        import LDAPClient
from vulture_toolkit.auth.mongodb_client     import MongoDBClient
from vulture_toolkit.auth.radius_client      import RadiusClient
from vulture_toolkit.auth.sql_client         import SQLClient
from vulture_toolkit.auth.totp_client        import TOTPClient
from vulture_toolkit.auth.vulturemail_client import VultureMailClient

# Logger configuration
import logging
#logging.config.dictConfig(settings.LOG_SETTINGS)
logger = logging.getLogger('portal_authentication')


class Backend(object):
    def __init__(self, client_type, settings):
        clients = {
            "LDAP"        : LDAPClient,
            "SQL"         : SQLClient,
            "KERBEROS"    : KerberosClient,
            "MONGODB"     : MongoDBClient,
            "RADIUS"      : RadiusClient,
            "AUTHY"       : AuthyClient,
            "VULTUREMAIL" : VultureMailClient,
            "TOTP"        : TOTPClient
        }

        self.client = clients[client_type](settings)
        self.repository = "{} ({})".format(settings.repo_name, settings.__class__.__name__)
        self.repository_id = settings.id

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    def set_authentication_results(self, auth_results):
        return {
            'data'              : auth_results,
            'backend'           : self,
            'token_return_type' : self.client.oauth2_token_return if hasattr(self.client, 'oauth2_token_return') else 'header',
            'token_ttl'         : self.client.oauth2_token_ttl if hasattr(self.client, 'oauth2_token_ttl') else 3600
        }

    def authenticate(self, user, passwd, **kwargs):
        return self.set_authentication_results(self.client.authenticate(user, passwd, backend_id=self.repository_id))

    def search_user(self, username):
        try:
            return self.client.search_user(username)
        except AttributeError:
            raise NotImplementedError("Search user is not implemented on this repository.")

    def get_user_infos(self, username):
        try:
            return self.client.get_user_infos(username)
        except AttributeError:
            raise NotImplementedError("Search user is not implemented on this repository.")

    def search_user_by_email(self, email):
        username = self.client.search_user_by_email(email)
        return {
            'user'    : username,
            'backend' : self
        }

    def add_new_user(self, username, password, email, phone, **kwargs):
        try:
            return self.client.add_new_user(username, password, email, phone)
        except AttributeError:
            raise NotImplementedError("Adding new user is not implemented on this repository.")

    def update_user(self, username, email="", phone=""):
        try:
            if email:
                self.client.update_email(username, email)
            if phone:
                self.client.update_phone(username, phone)
            return True
        except AttributeError as e:
            logger.exception(e)
            raise NotImplementedError("Updating user is not implemented on this repository.")

    def delete_user(self, username):
        try:
            self.client.delete_user(username)
            return True
        except AttributeError:
            raise NotImplementedError("Deleting user is not implemented on this repository.")
