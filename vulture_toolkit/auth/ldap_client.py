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
__doc__ = 'LDAP authentication client wrapper'

import logging

import ldap
import ldap.modlist as modlist

logger = logging.getLogger('portal_authentication')
#TODO Copyright https://github.com/ametaireau/django-auth-ldap
from .exceptions import AuthenticationError, ChangePasswordError, UserNotFound, LDAPSizeLimitExceeded
from .base_auth import BaseAuth


class LDAPClient(BaseAuth):

    def __init__(self, settings):
        """ Instantiation method

        :param settings:
        :return:
        """
        # Connection settings
        self.host = settings.ldap_host
        self.port = settings.ldap_port

        self.user = settings.ldap_connection_dn
        self.password = settings.ldap_password
        self.base_dn = settings.ldap_base_dn
        self._connection_settings = {
            ldap.OPT_PROTOCOL_VERSION: settings.ldap_protocol,
            ldap.OPT_REFERRALS: 0,
            ldap.OPT_TIMEOUT: 5  # Set timeout = 5s to prevent Gateway Timeout in GUI/Portal
        }
        # User related settings
        self.user_dn = settings.ldap_user_dn

        self.user_scope = settings.ldap_user_scope

        self.user_filter = settings.ldap_user_filter
        self.user_attr = settings.ldap_user_attr
        self.user_account_locked_attr = settings.ldap_user_account_locked_attr
        self.user_change_password_attr = settings.ldap_user_change_password_attr
        self.user_mobile_attr = settings.ldap_user_mobile_attr
        self.user_email_attr = settings.ldap_user_email_attr
        self.user_groups_attr = settings.ldap_user_groups_attr
        # Group related settings
        self.group_dn = settings.ldap_group_dn

        self.group_scope = settings.ldap_group_scope
        if not self.group_scope:
            self.group_scope = 2 # Subtree by default

        self.group_filter = settings.ldap_group_filter
        self.group_attr = settings.ldap_group_attr
        self.group_member_attr = settings.ldap_group_member_attr
        if not self.group_member_attr:
            self.group_member_attr="member"

        self.attributes_list = list()
        if self.user_mobile_attr:
            self.attributes_list.append(str(self.user_mobile_attr))
        if self.user_email_attr:
            self.attributes_list.append(str(self.user_email_attr))
        self.scope = None

        self.enable_oauth2 = settings.enable_oauth2
        try:
            self.oauth2_attributes = settings.oauth2_attributes.split(",")
        except Exception as e:
            self.oauth2_attributes = list()
        self.oauth2_type_return = settings.oauth2_type_return
        self.oauth2_token_return = settings.oauth2_token_return
        self.oauth2_token_ttl = settings.oauth2_token_ttl

        proto = 'ldap'
        self.start_tls = False
        if settings.ldap_encryption_scheme == 'start-tls':
            self.start_tls = True
            self._connection_settings[ldap.OPT_X_TLS_CACERTDIR] = '/home/vlt-sys/Engine/conf/certs'
            self._connection_settings[ldap.OPT_X_TLS_REQUIRE_CERT] = ldap.OPT_X_TLS_NEVER
            self._connection_settings[ldap.OPT_X_TLS_NEWCTX]=0
            self._connection_settings[ldap.OPT_DEBUG_LEVEL]=255

        elif settings.ldap_encryption_scheme == 'ldaps':
            proto = 'ldaps'
            self._connection_settings[ldap.OPT_X_TLS_CACERTDIR] = '/home/vlt-sys/Engine/conf/certs'
            self._connection_settings[ldap.OPT_X_TLS_REQUIRE_CERT] = ldap.OPT_X_TLS_NEVER
            self._connection_settings[ldap.OPT_X_TLS_NEWCTX]=0
            self._connection_settings[ldap.OPT_DEBUG_LEVEL]=255

        if (self.host).find(':') != -1:
            self.host='[' + self.host + ']'

        self.ldap_uri = "{}://{}:{}".format(proto, self.host, self.port)
        self._ldap_connection = None

    def _get_connection(self):
        """ Internal method used to initialize/retrieve LDAP connection

        :return: LDAPObject object
        """

        if self._ldap_connection is None:
            self._ldap_connection = ldap.initialize(self.ldap_uri)
            for opt, value in self._connection_settings.items():
                self._ldap_connection.set_option(opt, value)
            # Start-TLS support
            if self.start_tls:
                logger.info("Starting Start-TLS connection")
                self._ldap_connection.start_tls_s()

        return self._ldap_connection


    def _bind_connection(self, bind_username, bind_password):
        """ Try a bind operation over LDAP connection

        :param bind_username: String with username
        :param bind_password: String with password
        :return:Nothing
        """
        logger.debug("Trying to bind connection for username {}"
                     .format(bind_username))
        self._get_connection().simple_bind_s(bind_username,
                                             bind_password)


    def unbind_connection(self):
        self._ldap_connection.unbind_s()
        self._ldap_connection = None


    def _search(self, dn, ldap_query, username):
        """ Private method used to perform a search operation over LDAP

        :param ldap_query: String with LDAP query filter
        :param username: String with username
        :return: An list with results if query match, None otherwise
        """
        # Defining searched attributes
        attributes_list = self.attributes_list
        # Bind with svc account and look for provided username
        self._bind_connection(self.user, self.password)
        logger.debug("Searching for email/username/groups {}".format(username))
        logger.debug("LDAP filter: basedn: {}, scope: {}, searchdn: {}, "
                     "attributes: {}".format(dn, self.user_scope, ldap_query,
                                             attributes_list))
        # Create pagination control
        page_control = ldap.controls.SimplePagedResultsControl(True, size=100, cookie='')
        result = []
        while True:
            # Make query with server control pagination
            msgid = self._get_connection().search_ext(dn, self.scope,
                                                     ldap_query,
                                                     attributes_list,
                                                     serverctrls=[page_control])
            try:
                rtype, rdata, rmsgid, serverctrls = self._get_connection().result3(msgid)
            except ldap.SIZELIMIT_EXCEEDED as e:
                raise LDAPSizeLimitExceeded(len(result), result)
            result.extend(rdata)
            controls = [control for control in serverctrls
                        if control.controlType == ldap.controls.SimplePagedResultsControl.controlType]
            if not controls:
                logger.error('The server ignores RFC 2696 control, quitting query.')
                break
            if not controls[0].cookie:
                break
            page_control.cookie = controls[0].cookie
        result = self._process_results(result)
        logger.debug("LDAP search_s result is: {}".format(result))
        if len(result) > 0:
            return result
        else:
            return None


    def _search_oauth2(self, username):
        """ Private method used to perform a search operation over LDAP

        :param ldap_query: String with LDAP query filter
        :param username: String with username
        :return: An list with results if query match, None otherwise
        """
        base_dn = self._get_user_dn()
        # Defining user search filter
        query_filter = "({}={})".format(self.user_attr, username)
        if self.user_filter:
            query_filter = "(&{}{})".format(query_filter, self.user_filter)
        # Bind with svc account and look for provided username
        self._bind_connection(self.user, self.password)
        logger.debug("Searching for email/username/groups {}".format(username))
        logger.debug("LDAP filter: basedn: {}, scope: {}, searchdn: {}, attributes: {}".
                     format(base_dn, self.user_scope, query_filter, self.oauth2_attributes))
        oauth2_attributes = list()
        for attr in self.oauth2_attributes:
            oauth2_attributes.append(str(attr))
        result = self._get_connection().search_s(base_dn, self.scope, query_filter, oauth2_attributes)
        result = self._process_results(result)
        logger.debug("LDAP oauth2 search_s result is: {}".format(result))
        if len(result) > 0:
            return result
        else:
            return None


    def search_user(self, username):
        """ Method used to search for a user inside LDAP repository

        :param username: String with username
        :return: An list with results if query match, None otherwise
        """
        # Defining user search filter
        query_filter = "({}={})".format(self.user_attr, username)
        if self.user_filter:
            query_filter = "(&{}{})".format(query_filter, self.user_filter)
        dn = self._get_user_dn()
        self.scope = self.user_scope
        return self._search(dn, query_filter, username)

    def enumerate_users(self):
        lst=list()
        lst.append(self.user_dn)
        lst.append(self.base_dn)
        try:
            res = self.search_user("*")
        except LDAPSizeLimitExceeded as e:
            logger.warning("Size limit exceeded ({}), partial results are returned.".format(e.max_size))
            res = e.partial_results
        if res:
            for result in res:
                lst.append(result[0])
        return lst

    def enumerate_groups(self):
        lst=list()
        lst.append(self.group_dn)
        lst.append(self.base_dn)
        try:
            res = self.search_group("*")
        except LDAPSizeLimitExceeded as e:
            logger.warning("Size limit exceeded ({}), partial results are returned.".format(e.max_size))
            res = e.partial_results
        if res:
            for result in res:
                lst.append(result[0])
        return lst


    def search_user_by_email(self, email):
        """ Method used to search for a user inside LDAP repository

        :param email: String with email address
        :return: An list with results if query match, None otherwise
        """

        # Defining user search filter
        query_filter = "({}={})".format(self.user_email_attr, email)
        if self.user_filter:
            query_filter = "(&{}{})".format(query_filter, self.user_filter)
        dn = self._get_user_dn()
        self.scope = self.user_scope

        brut_result = self._search(dn, query_filter, email)

        if not brut_result:
            raise UserNotFound("User not found in database for email '{}'".format(email))

        return brut_result[0][0].split(",")[0].split('=')[1]


    def update_password (self, username, old_password, cleartext_password):
        """ Update a user password inside LDAP Repo

        :param username: String with username
        :param cleartext_password: String with cleartext password
        :return: True if Success, False otherwise
        """

        logger.info("Updating password for username {}".format(username))

        """ First search for user """
        found = self.search_user(username)
        if found:
            cn = found[0][0]
            self._bind_connection(self.user, self.password)
            try:
                old_password=None
                result = self._get_connection().passwd_s(cn, old_password, cleartext_password)
                if result == (None, None):
                    return result

                result = self._process_results(result)
                logger.debug("LDAP passwd_s result is: {}".format(result))
            except Exception as e:
                logger.error ("LDAP passwd_s error: {}".format(e))
                logger.exception(e)
                raise ChangePasswordError(str(e))

            if len(result):
                return result

        raise ChangePasswordError("Cannot find user '{}'".format(username))


    def search_group(self, groupname):
        """ Method used to search a group inside LDAP repository

        :param groupname: String with groupname
        :return: An list with results if query match, None otherwise
        """
        # Defining group search filter
        query_filter = "({}={})".format(self.group_attr, groupname)
        if self.group_filter:
            query_filter = "(&{}{})".format(query_filter, self.group_filter)
        dn = self._get_group_dn()
        self.scope = self.group_scope
        group_member_attr = str(self.group_member_attr.lower())
        self.attributes_list.append(group_member_attr)
        results = self._search(dn, query_filter, groupname)
        self.attributes_list.remove(group_member_attr)
        return results

    def search_user_groups(self, username, gui=False):
        """ Method used to retrieve user's group

        :param username: String with username
        :return: List of Distinguished Name (DN) group's user
        """

        if not self.user_groups_attr and not self.group_member_attr:
            return 'N/A'
        group_list = list()

        logger.debug("Looking for {}'s groups".format(username.encode('utf-8')))

        if self.user_groups_attr:
            """ Search "memberOf style" groups inside the given user entry """
            user_groups_attr = str(self.user_groups_attr.lower())
            self.attributes_list.append(user_groups_attr)

        user_info = self.search_user(username)

        if user_info:
            userdn=user_info[0][0]
            if self.user_groups_attr:
                group_list = user_info[0][1].get(user_groups_attr)
                #This can return None
                if not group_list:
                    group_list=list()
        if self.user_groups_attr:
            self.attributes_list.remove(user_groups_attr)

        logger.debug("{}'s groups are: {}".format(username.encode('utf-8'), group_list))

        # If no group was found with memberOf style, loop over all groups to retrieve members
        """ Search "member style" membership of the given user user inside groups entries """
        error = None
        if not group_list and self.group_member_attr:
            group_membership_attr = str(self.group_member_attr.lower())
            self.attributes_list.append(group_membership_attr)
            try:
                groups = self.search_group("*")
            except LDAPSizeLimitExceeded as e:
                error = e
                groups = e.partial_results
                if not gui:
                    logger.warning("Size limit exceeded, partial results are performed.")
            if groups:
                for group_info in groups:
                    group_dn=group_info[0]
                    members=group_info[1].get(self.group_member_attr.lower())
                    if members:
                        for member in members:
                            if member.lower()==userdn.lower() and group_dn not in group_list:
                                group_list.append(group_dn)
            self.attributes_list.remove(group_membership_attr)
        if error and gui:
            raise LDAPSizeLimitExceeded(e.max_size, group_list)
        return group_list

    def _get_user_dn(self):
        """ Return search DN of User. DN of user is a concatenation of Base DN
         and user DN

        :return: String with DN
        """
        dn = ""
        if self.base_dn and self.user_dn:
            dn = "{},{}".format(self.user_dn, self.base_dn)
        elif self.base_dn:
            dn = self.base_dn
            logger.info(dn)
        elif self.user_dn:
            dn = self.user_dn
            logger.info(dn)
        return dn

    def _get_group_dn(self):
        """ Return search DN of Group. DN of group is a concatenation of Base DN
         and group DN

        :return: String with DN
        """
        dn = ''
        if self.base_dn and self.group_dn:
            dn = "{},{}".format(self.group_dn, self.base_dn)
        elif self.base_dn:
            dn = self.base_dn
        elif self.user_dn:
            dn = self.group_dn
        return dn

    def is_user_account_locked(self, username):
        """Method used to check if a user account is locked

        :param username: String with username
        :return:True if account is locked, False otherwise
        """

        username=username.encode('utf-8')

        if not self.user_account_locked_attr:
            return False
        logger.debug("Looking if {} account is blocked".format(username))
        query_filter = "({}={})".format(self.user_attr, username)
        if self.user_filter:
            query_filter = "(&{}{}{})".format(query_filter, self.user_filter,
                                              self.user_account_locked_attr)
        dn = self._get_user_dn()
        self.scope = self.user_scope
        logger.debug(query_filter)
        result = self._search(dn, query_filter, username)
        if result is not None:
            logger.info("{} account is blocked".format(username))
            return True
        else:
            logger.info("{} account is not blocked".format(username))
            return False

    def is_password_expired(self, username):
        """ Method used to search if a user account need to change its password

        :param username: String with username
        :return: True if user account need to change its password, False otherwise
        """

        username=username.encode('utf-8')

        if not self.user_change_password_attr:
            return False
        logger.debug("Looking if {} account needs to change its password"
                    .format(username))
        query_filter = "({}={})".format(self.user_attr, username)
        if self.user_filter:
            query_filter = "(&{}{}{})".format(query_filter, self.user_filter,
                                              self.user_change_password_attr)
        dn = self._get_user_dn()
        self.scope = self.user_scope
        result = self._search(dn, query_filter, username)
        if result is not None:
            logger.info("{} account need to change its password"
                        "".format(username))
            return True
        else:
            logger.info("{} account doesn't need to change its password"
                        "".format(username))
            return False


    def authenticate (self, username, password, **kwargs):
        """Authentication method of LDAP repository, which returns dict of specified attributes:their values
        :param username: String with username
        :param password: String with password
        :param oauth2_attributes: List of attributes to retrieve
        :return:
        """
        return_status = kwargs.get('return_status', False)
        logger.debug("Trying to authenticate username {}".format(username.encode('utf-8')))
        # Prevent bind with empty password. As wrote in RFC 4511 LDAP server
        # won't raise an error message at bind
        if len(password) == 0:
            raise AuthenticationError("Empty password is not allowed")
        # Looking for user DN, if found we can try a bind
        found = self.search_user(username)

        if found is not None:
            dn = found[0][0]
            logger.debug("User {} was found in LDAP, its DN is: {}"
                        .format(username.encode('utf-8'), dn))
            self._bind_connection(dn, password)
            # Auth check
            if type(self._ldap_connection.whoami_s()) is None:
                raise AuthenticationError("LDAP bind failed for username {}".format(username.encode('utf-8')))
            else:
                logger.debug("Successful bind for username {}".format(username.encode('utf-8')))
                if return_status is True:
                    return True

                phone, email = 'N/A', 'N/A'
                if self.user_mobile_attr:
                    phone = found[0][1].get(self.user_mobile_attr, 'N/A')
                    if isinstance(phone, list):
                        phone = phone[0]
                if self.user_email_attr:
                    email = found[0][1].get(self.user_email_attr, 'N/A')
                    if isinstance(email, list):
                        email = email[0]

                result = {
                    'dn'              : dn,
                    'user_phone'      : phone,
                    'user_email'      : email,
                    'password_expired': self.is_password_expired(username),
                    'account_locked'  : self.is_user_account_locked(username),
                    'user_groups'     : self.search_user_groups(username)
                }

                if self.enable_oauth2:
                    oauth2_found = self._search_oauth2(username)

                    if str(self.oauth2_type_return) == 'dict':
                        oauth2_scope = dict()
                    elif self.oauth2_type_return == 'list':
                        oauth2_scope = list()
                    else:
                        logger.error("LDAP::authenticate: Oauth2 type return is not dict nor list for user {}".format(dn))
                        return result

                    if self.oauth2_attributes:
                        """ Return attributes needed for OAuth2 scopes """
                        for attr in self.oauth2_attributes:
                            try:
                                if attr.lower() == 'dn':
                                    attr_value = str(oauth2_found[0][0])
                                else:
                                    attr_value = oauth2_found[0][1].get(attr, None)
                                    if attr_value is None:
                                        logger.error("Unable to find oauth2 attribute named {} for user {} ".format(attr, dn))
                                        attr_value = 'N/A'

                                if str(self.oauth2_type_return) == 'dict':
                                    oauth2_scope[attr] = attr_value

                                elif str(self.oauth2_type_return) == 'list':
                                    oauth2_scope.append(str(attr_value))

                            except Exception as e:
                                logger.error("Unable to find oauth2 attribute named {} for user {} : {}".format(attr, dn, e))
                    else:
                        oauth2_scope = '{}'

                    oauth2_result = {
                        'token_ttl': self.oauth2_token_ttl,
                        'token_return_type': self.oauth2_token_return,
                        'scope': oauth2_scope
                    }
                    result['oauth2'] = oauth2_result

                return result
        else:
            logger.error("Unable to found username {} in LDAP repository"
                         "".format(username.encode('utf-8')))
            raise UserNotFound("Unable to found {}".format(username.encode('utf-8')))


    def _process_results(self, results):
        """
        Returns a sanitized copy of raw LDAP results. This scrubs out
        references, decodes utf8, etc.
        :param results: result to parse
        """
        results = _DeepStringCoder('utf-8').decode(results)
        return results

    def test_ldap_connection(self):
        """ Method used to test LDAP connectivity. In order to test it, LDAP
         connection is initialized then a bind with service account is done
        """
        response = {
            'status': None,
            'reason': None
        }
        try:
            self._bind_connection(self.user, self.password)
            response['status'] = True
        except ldap.LDAPError as e:
            response['status'] = False
            response['reason'] = str(e)
        return response

    def test_user_connection(self, username, password):
        """ Method used to perform test search over LDAP Repository
        :param username: String with username
        :param password: String with password
        """
        response = {
            'status': None,
            'reason': None
        }
        try:
            password = password.encode('utf-8')
            user_info = self.search_user(username)
            response['status'] = self.authenticate(username, password, return_status=True)
            response['account_locked'] = self.is_user_account_locked(username)
            response['password_expired'] = self.is_password_expired(username)
            try:
                response['user_groups'] = self.search_user_groups(username, gui=True)
            except LDAPSizeLimitExceeded as e:
                response['user_groups'] = e.partial_results
                response['warning'] = "Size limit exceeded ({}), groups are truncated.".format(e.max_size)
            if user_info and self.user_mobile_attr is not None:
                phone_info = user_info[0][1].get(self.user_mobile_attr.lower())
                response['user_phone'] = phone_info
            else:
                response['user_phone'] = 'N/A'

            if user_info and self.user_email_attr is not None:
                email_info = user_info[0][1].get(self.user_email_attr.lower())
                response['user_email'] = email_info
            else:
                response['user_email'] = 'N/A'

        except ldap.INVALID_CREDENTIALS:
            response['status'] = False
            if response.get('account_locked') == True:
                response['reason'] = "Account locked"
            elif response.get('password_expired') == True:
                response['reason'] = "Password expired"
            else:
                response['reason'] = "Invalid credentials"
        except UserNotFound as e:
            response['status'] = False
            response['reason'] = "User doesn't exist"
        except (ldap.LDAPError, Exception) as e:
            logger.exception(e)
            response['status'] = False
            response['reason'] = str(e)
        return response

    def test_group_search(self, group_name):
        response = {
            'status': None,
            'reason': None,
            'groups': []
        }
        try:
            group_info = self.search_group(group_name)
            if group_info:
                for group in group_info:
                    response['groups'].append({
                        'group_dn': group[0],
                        'group_members': group[1].get(self.group_member_attr.lower(), [])
                    })
            response['status'] = True
        except Exception as e:
            logger.exception(e)
            response['status'] = False
            response['reason'] = str(e)
        return response

    def get_user_infos(self, username):

        found = self.search_user(username)

        if found is not None:
            dn = found[0][0].encode('utf-8')
            logger.debug("User {} was found in LDAP, its DN is: {}"
                         .format(username.encode('utf-8'), dn))

            phone, email = '', ''
            if self.user_mobile_attr:
                phone = found[0][1].get(self.user_mobile_attr, '')
                if isinstance(phone, list):
                    phone = phone[0]
            if self.user_email_attr:
                email = found[0][1].get(self.user_email_attr, '')
                if isinstance(email, list):
                    email = email[0]

            return {
                'login': dn,
                'phone': phone,
                'email': email,
                'password_expired': self.is_password_expired(username),
                'account_locked': self.is_user_account_locked(username),
                'groups': self.search_user_groups(username)
            }
        else:
            logger.error("Unable to found username {} in LDAP repository"
                         "".format(username.encode('utf-8')))
            raise UserNotFound("User '{}' not found in database.".format(username.encode('utf-8')))

    def add_new_user(self, username, password, email, phone, group, update_group):

        self._bind_connection(self.user, self.password)

        # Concatenate username with group ou and cn
        dn = "cn="+str(username)
        for g in group.split(',')[1:]:
            dn += ","+str(g)

        attrs = {
            'objectClass': ['inetOrgPerson', 'top'],
            'sn': str(username),
            self.user_attr: str(username),
            'userPassword' : str(password),
            'description' : "User automatically registrered by Vulture"
        }

        if self.user_groups_attr:
            attrs[self.user_groups_attr] = str(group)
        if self.user_mobile_attr:
            attrs[self.user_mobile_attr] = str(phone)
        if self.user_email_attr:
            attrs[self.user_email_attr] = str(email)

        # Convert our dict to nice syntax for the add-function using modlist-module
        ldif = modlist.addModlist(attrs)

        logger.debug("LDAP::add_new_user: Adding new user '{}' in ldap database".format(dn))
        # Do the actual synchronous add-operation to the ldapserver
        self._get_connection().add_s(dn, ldif)
        logger.info("LDAP::add_new_user: User '{}' successfully added in ldap database".format(dn))

        if update_group and self.group_member_attr:
            attrs = [(ldap.MOD_ADD, self.group_member_attr, dn)]
            logger.debug("LDAP::add_new_user: Adding user '{}' to group '{}'".format(dn, group))
            self._get_connection().modify_s(group, attrs)
            logger.info("LDAP::add_new_user: User '{}' successfully added to group '{}'".format(dn, group))

        # Its nice to the server to disconnect and free resources when done
        self.unbind_connection()

    def update_field(self, username, field_name, field_value):
        """ Update a user field inside LDAP Repo

        :param username: String with username
        :param field_name: String with field name to update
        :param field_value: String with field value to set
        :return: True if Success, False otherwise
        """
        logger.info("Updating {} for username {}".format(field_name, username))

        """ First search for user """
        found = self.search_user(username)
        if found:
            cn = found[0][0]
            self._bind_connection(self.user, self.password)
            attrs = [(ldap.MOD_REPLACE, field_name, field_value)]
            logger.debug("LDAP::update_field: Updating user '{}' {}".format(cn, attrs))
            # Do the actual modification
            result = self._get_connection().modify_s(cn, attrs)
            logger.debug("LDAP modify_s result is: {}".format(result))
            # Its nice to the server to disconnect and free resources when done
            self.unbind_connection()
        else:
            logger.error("Unable to found username {} in LDAP repository"
                         "".format(username.encode('utf-8')))
            raise UserNotFound("User '{}' not found in database.".format(username.encode('utf-8')))

    def update_phone(self, username, phone):
        """  """
        if self.user_mobile_attr:
            return self.update_field(username, self.user_mobile_attr, phone)
        else:
            logger.error("Cannot update phone for user {}, phone column is empty.".format(username))

    def update_email(self, username, email):
        """  """
        if self.user_email_attr:
            return self.update_field(username, self.user_email_attr, email)
        else:
            logger.error("Cannot update email for user {}, email column is empty.".format(username))

    def delete_user(self, username):

        self._bind_connection(self.user, self.password)

        # Looking for user DN, if found we can try a bind
        found = self.search_user(username)

        if found is not None:
            dn = found[0][0]
            logger.debug("User {} was found in LDAP, its DN is: {}"
                         .format(username.encode('utf-8'), dn))
            self._get_connection().delete_s(dn)
        else:
            logger.error("Unable to found username {} in LDAP repository"
                         "".format(username.encode('utf-8')))
            raise UserNotFound("Unable to found {}".format(username.encode('utf-8')))

        # Its nice to the server to disconnect and free resources when done
        self.unbind_connection()


class _DeepStringCoder(object):
    """
    Encodes and decodes strings in a nested structure of lists, tuples, and
    dicts. This is helpful when interacting with the Unicode-unaware
    python-ldap.
    """
    def __init__(self, encoding):
        self.encoding = encoding

    def decode(self, value):
        try:
            if isinstance(value, bytes):
                value = value.decode(self.encoding)
            elif isinstance(value, list):
                value = self._decode_list(value)
            elif isinstance(value, tuple):
                value = tuple(self._decode_list(value))
            elif isinstance(value, dict):
                value = self._decode_dict(value)
        except UnicodeDecodeError:
            pass

        return value

    def _decode_list(self, value):
        return [self.decode(v) for v in value]

    def _decode_dict(self, value):
        # Attribute dictionaries should be case-insensitive. python-ldap
        # defines this, although for some reason, it doesn't appear to use it
        # for search results.
        decoded = ldap.cidict.cidict()

        for k, v in value.items():
            decoded[self.decode(k)] = self.decode(v)

        return decoded