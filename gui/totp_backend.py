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


from gui.backends import Backend



class TOTPBackend(Backend):
	def __init__(self, settings):
		super(TOTPBackend, self).__init__("TOTP", settings)


	def get_captcha(self, user_id, email):
		return self.client.generate_captcha(user_id, email)


	def authenticate(self, user_id, key, **kwargs):
		return self.client.authenticate(user_id, key, **kwargs)


	def register_authentication(self, **kwargs):
		app_id = kwargs['app']
		app_name = kwargs['app_name']
		backend_id = kwargs['backend']
		login = kwargs['login']
		return self.client.register_authentication(app_id, app_name, backend_id, login)
