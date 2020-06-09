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
__doc__ = 'Authentication backend wrapper'


# Django project imports
from gui.backends import Backend




class VultureMailBackend(Backend):
    def __init__(self, settings):
        super(VultureMailBackend, self).__init__("VULTUREMAIL", settings)


    """ Overrided method because "set_authentication_results" is not called """
    def authenticate(self, user_id, key, **kwargs):
        return self.client.authenticate(user_id, key)


    def register_authentication(self, **kwargs):
        recipient = kwargs.get('user_mail')
        sender = kwargs.get('sender')
        return self.client.register_authentication(sender, recipient)

