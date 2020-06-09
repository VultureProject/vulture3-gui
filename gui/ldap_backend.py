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
__author__ = "Kevin Guillemot, Florian Hagniel"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = 'LDAPClient authentication wrapper'


# Django project imports
from gui.backends                     import Backend
from gui.models.user_document         import VultureUser as User

# Required exceptions imports
from ldap                             import INVALID_CREDENTIALS
from portal.system.exceptions         import ACLError
from vulture_toolkit.auth.exceptions  import AccountLocked, AuthenticationError, UserNotFound



class LDAPBackend(Backend):
    def __init__(self, settings):
        super(LDAPBackend, self).__init__("LDAP", settings)


    def close_connection(self, logger):
        try:
            self.client.unbind_connection()
        except Exception as e:
            logger.error("LDAP_BACKEND::close_connection: Error while closing ldap connection : '{}'".format(e))


    def enumerate_users (self):
        return self.client.enumerate_users()


    def enumerate_groups (self):
        return self.client.enumerate_groups()


    def update_password (self, username, old_password, hashed_password):
        return self.client.update_password(username, old_password, hashed_password)


    def change_password(self, username, old_password, new_password, **kargs):
        # No cypher for passwords
        return self.update_password(username, old_password, new_password)


    """ Override method because LDAP implements ACLs """
    def authenticate(self, username, password, **kwargs):
        acls = kwargs.get('acls', None)
        logger = kwargs.get('logger', None)
        try:
            attributes = self.client.authenticate(username, password)
            if attributes.get('account_locked'):
                raise AccountLocked("Locked account")
            logger.info("LDAP_BACKEND::authenticate: Authentication succeed for user '{}'".format(username))
            if acls and attributes:
                for acl in acls:
                    assert( self.verify_acl_user(logger, attributes['dn'], acl) and self.verify_acl_group(logger, attributes['dn'], acl) )
            self.close_connection(logger)
            return self.set_authentication_results(attributes)

        except INVALID_CREDENTIALS:
            raise AuthenticationError("LDAP_BACKEND::authenticate: Invalid credentials for user {}".format(username))

        except (UserNotFound, User.DoesNotExist) as e:
            raise AuthenticationError("LDAP_BACKEND::authenticate: Username {} not found in LDAP base".format(username))

        except AssertionError:
            self.close_connection(logger)
            raise ACLError("User '{}' does not satisfy with any ACL".format(username))

        except Exception as e:
            self.close_connection(logger)
            logger.exception(e)
            logger.error("LDAP_BACKEND::authenticate: Error while trying to authenticate user '{}' : {}".format(username, e))
            raise e
            #raise AuthenticationError("Error during authentication of user '{}' : {}".format(username, e))


    def users_group_search(self, group_name):
        return self.client.test_group_search(group_name)['groups']


    def get_users_in_group(self, logger, group):
        group_cn = group.split(',')[0].split('=')[1]
        for group_infos in self.users_group_search(group_cn):
            if group_infos['group_dn'] == group:
                return group_infos.get('group_members', [])
        logger.info("LDAP_BACKEND::get_group: No group '{}' found in the LDAP directory".format(group))
        return []


    def verify_acl_user(self, logger, user_dn, acl):
        if acl.user_list and user_dn not in acl.user_list.split('|'):
            return False
        elif acl.user_list:
            logger.info("LDAP_BACKEND::verify_acl_user: Username '{}' successfully pass the ACL '{}'".format(user_dn, acl.name))
        return True


    def verify_acl_group(self, logger, user_dn, acl):
        if acl.group_list:
            users = []
            try:
                for group in acl.group_list.split('|'):
                    for user in self.get_users_in_group(logger, group):
                        try:
                            users.append(user.lower())
                        except Exception as e:
                            logger.debug("Unable to encode username '{}' in utf-8 : {}".format(user, e))
                            users.append(user)

                # To let IN and not OUT of 'try' because we do not want to return True if something went wrong
                if users and user_dn.lower() not in users:
                    return False

                elif users:
                    logger.info("LDAP_BACKEND::verify_acl_group: Username '{}' successfully pass the ACL '{}'".format(user_dn, acl.name))

            except Exception as e:
                logger.error("LDAP_BACKEND::verify_acl_user: Error while trying to verify ACL for user '{}' : {}".format(user_dn, e))
                logger.exception(e)
                return False

        return True


    def add_new_user(self, username, password, email, phone ,**kwargs):
        group = kwargs['group']
        update_group = kwargs['update_group']
        return self.client.add_new_user(username, password, email, phone, group, update_group)

