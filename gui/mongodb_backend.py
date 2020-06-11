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
__author__ = "Florian Hagniel, Kevin Guillemot"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = 'MongoDBClient authentication wrapper'


# Django project imports
from gui.backends                        import Backend




class MongoDBBackend(Backend):
    def __init__(self, settings):
        super(MongoDBBackend, self).__init__("MONGODB", settings)


    def update_password (self, username, hashed_password):
        return self.client.update_password(username, hashed_password)


    def get_password_hash (self, password):
        return self.client._get_password_hash(password)


    def change_password(self, username, old_password, new_password, **kwargs):
        hashed_password = self.client._get_password_hash(new_password)
        return self.client.update_password(username, hashed_password)


    def get_user_column (self):
        return self.client.user_column

    # Function moved in mother-class : gui.backends.Backend
    # def authenticate (self, username, password, **kwargs):
    #     user = None
    #     try:
    #         attributes = self.client.authenticate(username, password)
    #         print "attributes",attributes
    #         return self.set_authentication_results(attributes)
    #     except AuthenticationError as e:
    #         raise AuthenticationError("Authentication error for user {} : {}".format(username, str(e)))
    #     except User.DoesNotExist:
    #         raise AuthenticationError("Username {} not found in MongoDB database".format(username))
    #     raise AuthenticationError("Error during authentication of user {}".format(username))

