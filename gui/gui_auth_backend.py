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
from django.contrib.auth import get_user_model
User = get_user_model()

from gui.models.system_settings import Cluster


class GuiAuthBackend(object):

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    def authenticate(self, username=None, password=None):
        """Wrapper to authenticate method provided by other Backend

        :param username:
        :param password:
        :return:
        """
        user = None
        cluster = Cluster.objects.get()
        repositories = cluster.get_authentication_repositories()
        for repo in repositories:
            auth_backend = repo.get_backend()
            res = auth_backend.authenticate(username, password)
            if res is not None:
                return res
        return user