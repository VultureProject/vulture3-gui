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
__author__ = "Florian Hagniel"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = 'Authentication backend wrapper'


# Django project imports
from gui.backends import Backend

# Required exceptions imports
from vulture_toolkit.auth.exceptions  import AccountLocked, AuthenticationError, UserNotFound


class SQLBackend(Backend):
    def __init__(self, settings):
        super(SQLBackend, self).__init__("SQL", settings)


    def update_password (self, username, hashed_password):
        return self.client.update_password (username, hashed_password)


    def get_password_hash (self, password):
        return self.client._get_password_hash(password)


    def change_password(self, username, old_password, new_password, **kwargs):
        hashed_password = self.get_password_hash(new_password)
        return self.update_password(username, hashed_password)

    def get_user_column (self):
        return self.client.user_column

    def authenticate(self, user, passwd, **kwargs):
        """ Override method authenticate of Backend """
        attributes = self.client.authenticate(user, passwd, backend_id=self.repository_id)
        if attributes.get('account_locked'):
            raise AccountLocked("Locked account")
        return self.set_authentication_results(attributes)
