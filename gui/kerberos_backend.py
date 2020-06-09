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
__author__ = "Kevin Guillemot, Jeremie Jourdin"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = 'KerberosClient authentication wrapper'


# Django project imports
from gui.backends                         import Backend

# Required exceptions imports
from vulture_toolkit.auth.exceptions      import AuthenticationError

# Extern modules imports
from hashlib                              import sha1




class KerberosBackend(Backend):
    def __init__(self, settings):
        super(KerberosBackend, self).__init__("KERBEROS", settings)


# from mongoengine.django.auth import Group
# from gui.models.user_document import VultureUser as User
    # def authenticate(self, username, password, **kwargs):
    #     user = None
    #     try:
    #         success = self.client.authenticate(username, password, self.repository.id)
    #         if success:
    #             user = User.objects.get(username=username,
    #                                     auth_backend=self.auth_backend)
    #         else:
    #             raise AuthenticationError
    #     except User.DoesNotExist:
    #         guest_grp = Group.objects.get(name='guest')
    #         user = User(username=username)
    #         user.groups.append(guest_grp)
    #         user.auth_backend = self.auth_backend
    #         user.save()
    #     return user


    def change_password(self, username, old_password, new_password, **kwargs):
        if not old_password:
            raise NotImplementedError("Reset password on Kerberos backend is not possible")

        ccname = "/tmp/krb5cc_" + sha1("{}{}".format(self.repository_id, username).encode('utf8')).hexdigest()

        return self.client.change_password(username, old_password, new_password, ccname, kwargs.get('krb5_service'))


    def authenticate_token(self, logger, token):
        result = self.client.verify_token(logger, token)
        if not result:
            logger.error("KRB5_BACKEND::authenticate_token: Authenticate krb5 token returned Null")
            raise AuthenticationError("Authentication failed for given token")
        else:
            return self.set_authentication_results(result)

    def create_tgt(self, backend_id, username, password, service=None):
        ccname = "/tmp/krb5cc_" + sha1("{}{}".format(backend_id, username).encode('utf8')).hexdigest()
        return self.client.create_tgt_from_creds(username, password, ccname, service)

