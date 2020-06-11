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
__doc__ = 'RadiusClient authentication wrapper'


# Django project imports
from gui.backends                    import Backend

# Required exceptions imports
from vulture_toolkit.auth.exceptions import AuthenticationError
from radius import SocketError




class RadiusBackend(Backend):
    def __init__(self, settings):
        super(RadiusBackend, self).__init__("RADIUS", settings)


    def search_user_by_email(self, email):
        raise NotImplementedError("Search user by mail is not implemented on Radius repository")


    def authenticate (self, username, password, **kwargs):
        logger = kwargs.get('logger')
        try:
            return self.set_authentication_results(self.client.authenticate(username, password))

        except SocketError as e:
            logger.error("RADIUS_BACKEND::authenticate: Timeout reached while trying to authenticate user '{}' : {}".format(username, e))
            raise AuthenticationError("Timeout reached while trying to authenticate user {}".format(username))

        except Exception as e:
            logger.error("RADIUS_BACKEND::authenticate: Error while trying to authenticate user '{}' : {}".format(username, e))
            raise AuthenticationError("Error during authentication of user {}".format(username))

