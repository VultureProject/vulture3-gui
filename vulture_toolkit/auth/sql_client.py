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
__doc__ = 'SQL authentication client wrapper'


# Django system imports

# Django project imports
from .base_auth import BaseAuth

# Required exceptions imports
from .exceptions import AuthenticationError, UserNotFound

# Extern modules imports
import MySQLdb
from sqlalchemy import create_engine
import urllib

# Logger configuration imports
import logging
logger = logging.getLogger('portal_authentication')


class SQLClient(BaseAuth):

    def __init__(self, settings, **kwargs):
        """ Instantiation method

        :param settings:
        :return:
        """
        if len(kwargs) != 0 :
            super(SQLClient, self).__init__(**kwargs)

        # Connection settings
        self.db_type = settings.db_type
        self.host = settings.db_host
        self.port = settings.db_port
        self.db_name = settings.db_name
        self.user = settings.db_user
        self.password = settings.db_password
        self._connection_settings = {
        }
        # User related settings
        self.user_table = settings.db_table
        self.user_column = settings.db_user_column
        self.password_column = settings.db_password_column
        self.password_hash_algo = settings.db_password_hash_algo
        self.password_salt = settings.db_password_salt
        self.password_salt_position = settings.db_password_salt_position
        self.change_pass_column = settings.db_change_pass_column
        self.change_pass_value = settings.db_change_pass_value
        self.locked_column = settings.db_locked_column
        self.locked_value = settings.db_locked_value
        self.user_phone_column = settings.db_user_phone_column
        self.user_phone = None
        self.user_email_column = settings.db_user_email_column
        self.user_email = None

        self._sql_connection = None

        self.enable_oauth2 = settings.enable_oauth2
        try:
            self.oauth2_attributes = settings.oauth2_attributes.split(",")
        except Exception as e:
            self.oauth2_attributes = list()
        self.oauth2_type_return = settings.oauth2_type_return
        self.oauth2_token_return = settings.oauth2_token_return
        self.oauth2_token_ttl = settings.oauth2_token_ttl

    def _get_connection(self):
        """ Internal method used to initialize/retrieve SQL connection

        :return:
        """
        if self._sql_connection is None:
            engineTest = self._get_engine()
            self._sql_connection = engineTest.connect()
            return self._sql_connection
        else:
            return self._sql_connection

    def _get_engine(self):
        """ Create an SQLAlchemy engine object, in order to connect to the DB

        :return: SQLAlchemy engine object
        """
        url = '{}://{}:{}@{}:{}/{}'.format(self.db_type, urllib.parse.quote_plus(self.user),
                                           urllib.parse.quote_plus(self.password),
                                           self.host, self.port,
                                           urllib.parse.quote_plus(self.db_name))

        engine = create_engine(url)
        return engine

    def _get_query(self):
        """ Build SQL query from configuration parameters

        :return: String with SQL query
        """
        query = "SELECT {} FROM {} WHERE {}=%s;".format(self._get_selected_fields(), self.user_table, self.user_column)
        return query

    def _get_selected_fields(self):
        """Internal method used to get SQL selected fields

        :return: String with list of fields (separated with
        comma)
        """
        fields = [
            self.user_column,
            self.password_column,
            self.change_pass_column,
            self.user_phone_column,
            self.user_email_column
        ]
        selected_fields = filter(None, fields)
        return ', '.join(selected_fields)

    def _search(self, query, param):
        """ Protected method used to execute SQL query

        :param query: String with SQL Query
        :param param: String with parameters used in SQL query
        :return: Query result if exists, None otherwise
        """
        logger.debug("SQL Query: {}".format(query))
        result = self._get_connection().execute(query, (param))
        if result.rowcount >= 1:
            return result
        else:
            return None

    def search_user (self, username):
        """ Search an user inside SQL Database

        :param username: String with username
        :return: Dict with result of SQL query
        """
        logger.info("Searching for username {}".format(username))
        username = MySQLdb.escape_string(username).decode('utf8')
        #query = self._get_query()
        # Creating query with oauth2_attributes
        query = "SELECT * FROM {} WHERE {}=%s;".format(self.user_table, self.user_column)
        # try:
        user_info = self._search(query, username)
        return user_info
        # except Exception as e:
        #     logger.error("Error during user search operation. Invalid SQL query")
        #     logger.exception(e)
        #     return None

    def get_user_infos(self, username):
        """ Search user into database, and return a dict with columns filled-in 
        If multiple users exists with the same username, return the first
        """
        users_infos = self.search_user(username)
        if users_infos:
            user_infos = dict(users_infos.fetchone())
            return {
                'login': user_infos[self.user_column],
                'phone': user_infos.get(self.user_phone_column, "") if self.user_phone_column else "",
                'email': user_infos.get(self.user_email_column, "") if self.user_email_column else "",
                'password_expired': self._is_password_expired(user_infos),
                'account_locked': self._is_user_account_locked(user_infos)
            }
        else:
            logger.error("Unable to found username {}".format(username))
            raise UserNotFound("User '{}' not found in database.".format(username))

    def update_password (self, username, hashed_password):
        """ Update a user password inside SQL Database

        :param username: String with username
        :param hashed_password: String with hashed password
        :return: True if Success, None otherwise
        """
        logger.info("Updating password for username {}".format(username))
        username = MySQLdb.escape_string(username)
        hashed_password = MySQLdb.escape_string(hashed_password)
        if self.change_pass_column:
            query = "UPDATE {} SET {}=%s, {}=%s WHERE {}=%s".format(self.user_table, self.password_column, self.change_pass_column, self.user_column)
        else:
            query = "UPDATE {} SET {}=%s WHERE {}=%s".format(self.user_table, self.password_column, self.user_column)

        if self.change_pass_column:
            self._search(query, (hashed_password, 0, username))
        else:
            self._search(query, (hashed_password, username))

        return True

    def update_field(self, username, field_name, field_value):
        """ Update a field inside SQL Database

        :param username: String with username
        :param field_name: String with field name to update
        :param field_value: String with field value to set
        :return: True if Success, None otherwise
        """
        logger.info("Updating password for username {}".format(username))
        username = MySQLdb.escape_string(username)
        field_name = MySQLdb.escape_string(field_name)
        field_value = MySQLdb.escape_string(field_value)
        query = "UPDATE {} SET {}=%s WHERE {}=%s".format(self.user_table, field_name, self.user_column)
        self._search(query, (field_value, username))

    def update_phone(self, username, phone):
        """  """
        if self.user_phone_column:
            return self.update_field(username, self.user_phone_column, phone)
        else:
            logger.error("Cannot update phone for user {}, phone column is empty.".format(username))

    def update_email(self, username, email):
        """  """
        if self.user_email_column:
            return self.update_field(username, self.user_email_column, email)
        else:
            logger.error("Cannot update email for user {}, email column is empty.".format(username))

    def search_user_by_email (self, email):
        """ Search an user inside SQL Database

        :param email: String with email adddress
        :return: Dict with result of SQL query
        """
        logger.info("Searching for email address {}".format(email))
        email = MySQLdb.escape_string(email)

        query = "SELECT {} FROM {} WHERE {}=%s ORDER BY {} LIMIT 1;".format(self.user_column, self.user_table, self.user_email_column, self.user_column)

        user_info = self._search(query, email)

        if not user_info:
            raise UserNotFound("User not found in database for email '{}'".format(email))

        return dict(user_info.fetchone())[self.user_column]

    def _get_hashed_password(self, user_info):
        try:
            hashed_password = user_info[self.password_column]
            return hashed_password
        except Exception as e:
            logger.error("Unable to retrieve password from database")
            logger.exception(e)
            raise AuthenticationError("Unable to retrieve password from "
                                      "database, please ensure '{}' column "
                                      "exist".format(self.password_column))

    def authenticate (self, username, password, **kwargs):
        """ Authentication method for SQL backend

        :param username: String with username
        :param password: String with password
        :return: Dictionnary of user's attributes : value in database
        """
        return_status = kwargs.get('return_status', False)
        user_info = self.search_user (username)
        # User exist, we can now check if password match
        if user_info is not None:
            logger.info("Trying to authenticate username {}".format(username))
            for row in user_info :
                hashed_password = self._get_hashed_password(row)
                is_valid_password = self._check_password(password, hashed_password)
                if is_valid_password:

                    logger.info("Successful authentication for username {}".format(username))
                    if return_status is True:
                        return True

                    # Transform SQL result in Dict()
                    row_data = dict()
                    for key, value in row.items():
                        row_data[key] = value

                    phone, email = 'N/A', 'N/A'
                    if self.user_phone_column is not None:
                        phone = row_data.get(self.user_phone_column, 'N/A')
                    if self.user_email_column is not None:
                        email = row_data.get(self.user_email_column, 'N/A')

                    result = {
                        'dn'               : row[self.user_column],
                        'user_phone'       : phone,
                        'user_email'       : email,
                        'password_expired' : self._is_password_expired(row),
                        'account_locked'   : self._is_user_account_locked(row)
                    }


                    if self.enable_oauth2:
                        if str(self.oauth2_type_return) == 'dict':
                            oauth2_scope = dict()
                        elif str(self.oauth2_type_return) == 'list':
                            oauth2_scope = list()
                        else:
                            logger.error("SQL::authenticate: Oauth2 type return is not dict nor list for user {}".format(username))
                            return result

                        if self.oauth2_attributes:
                            """ Return attributes needed for OAuth2 scopes """
                            for attr in self.oauth2_attributes:
                                try:
                                    attr_value = row_data.get(attr, None)
                                    if attr_value is None:
                                        logger.error("Unable to find oauth2 attribute name '{}' for user '{}'".format(attr, username))
                                        attr_value = 'N/A'

                                    if str(self.oauth2_type_return) == 'dict':
                                        oauth2_scope[attr] = attr_value

                                    elif self.oauth2_type_return == 'list':
                                        oauth2_scope.append(attr_value)

                                except Exception as e:
                                    logger.error("Unable to retrieve field {} for username {} : {}".format(attr, username, str(e)))

                        else:
                             oauth2_scope = '{}'

                        oauth2_result = {
                            'token_ttl': self.oauth2_token_ttl,
                            'token_return_type': self.oauth2_token_return,
                            'scope': oauth2_scope
                        }
                        result['oauth2'] = oauth2_result

                    return result

            logger.error("Unable to authenticate username {}".format(username))
            raise AuthenticationError("Invalid credentials")
        else:
            logger.error("Unable to found username {}".format(username))
            raise UserNotFound("{} doesn't exist in database".format(username))

    def test_sql_connection(self):
        """ Method used to test SQL connectivity.
        """
        response = {
            'status': None,
            'reason': None
        }
        try:
            self._get_connection()
            response['status'] = True
        except Exception as e:
            logger.exception(e)
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
            'reason': None,
            'password_expired': False,
            'account_locked': False
        }

        try:
            data = self.authenticate(username, password, return_status=False)

            if data:
                response['status'] = True

                try:
                    response['user_phone'] = data['user_phone']
                except:
                    pass
                try:
                    response['user_email'] = data['user_email']
                except:
                    pass
                try:
                    response['account_locked'] = data['account_locked']
                except:
                    pass
                try:
                    response['password_expired'] = data['password_expired']
                except:
                    pass

        except AuthenticationError as e:
            response['status'] = False
            response['reason'] = str(e)
        except Exception as e:
            logger.exception(e)
            response['status'] = False
            response['reason'] = str(e)

        return response

    def add_new_user(self, username, password, email, phone):
        """ Public method used to insert a new user inside MongoDB repository

        :param username: String with username
        :return: String with username if found, None otherwise
        """
        #logger.info("Searching for username {}".format(username))
        username = MySQLdb.escape_string(username)
        email    = MySQLdb.escape_string(email)
        phone    = MySQLdb.escape_string(phone)
        hashed_password = MySQLdb.escape_string(self._get_password_hash(password))

        #"INSERT INTO users(login,password,locked,changepass,phone,email) VALUES ('test', 'test', 0, 0, '0601234567', 'test@google.com');"

        query = "INSERT INTO {}({},{}".format(self.user_table, self.user_column, self.password_column)
        end_query = " VALUES (%s, %s"
        params = [username, hashed_password]

        if self.change_pass_column:
            query += ",{}".format(self.change_pass_column)
            end_query += ",%s"
            if self.change_pass_value == "false":
                params.append("false")
            else:
                params.append("0")

        if self.locked_column:
            query += ",{}".format(self.locked_column)
            end_query += ",%s"
            if self.locked_value == "false":
                params.append("false")
            else:
                params.append("0")

        if self.user_phone_column:
            query += ",{}".format(self.user_phone_column)
            end_query += ",%s"
            params.append(phone)

        if self.user_email_column:
            query += ",{}".format(self.user_email_column)
            end_query += ",%s"
            params.append(email)

        query += ")" + end_query + ");"
        logger.debug("SQL query is: {}".format(query))

        return self._search(query, params)

    def delete_user(self, username):
        """ Delete user with given username """
        logger.info("Deleting user having username {}".format(username))
        username = MySQLdb.escape_string(username)
        query = "DELETE FROM {} WHERE {}=%s".format(self.user_table, self.user_column)
        self._search(query, (username))
