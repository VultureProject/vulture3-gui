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
__doc__ = 'MongoDB authentication client wrapper'

# Django system imports
import logging
import urllib
from json import loads as json_loads, dumps as json_dumps
from pymongo import MongoClient, ReadPreference

logger = logging.getLogger('portal_authentication')
from .exceptions import UserNotFound, ChangePasswordError, AuthenticationError
from .base_auth import BaseAuth


class MongoDBClient(BaseAuth):

    def __init__(self, settings):
        """ Instantiation method

        :param settings:
        :return:
        """
        # Connection settings
        self.is_internal = settings.is_internal
        self.host = settings.db_host
        self.port = settings.db_port
        self.db_name = settings.db_name
        self.user = settings.db_user
        self.password = settings.db_password
        self.db_client_cert = settings.db_client_cert
        self.replicaset = settings.replicaset
        
        if not self.replicaset or self.replicaset == "":
            self.replicaset = None

        # User related settings
        self.user_collection = settings.db_collection_name
        self.user_column = settings.db_user_column
        self.password_column = settings.db_password_column
        self.password_hash_algo = settings.db_password_hash_algo
        self.password_salt = settings.db_password_salt
        self.password_salt_position = settings.db_password_salt_position
        self.change_pass_column = settings.db_change_pass_column
        self.change_pass = None
        self.change_pass_value = settings.db_change_pass_value
        self.user_phone_column = settings.db_user_phone_column
        self.user_phone = None
        self.user_email_column = settings.db_user_email_column
        self.user_email = None

        self._mongodb_connection = None

        self.enable_oauth2 = settings.enable_oauth2
        try:
            self.oauth2_attributes = settings.oauth2_attributes.split(",")
        except Exception as e:
            self.oauth2_attributes = list()
        self.oauth2_type_return = settings.oauth2_type_return
        self.oauth2_token_return = settings.oauth2_token_return
        self.oauth2_token_ttl = settings.oauth2_token_ttl

    def _get_connection(self):
        """ Internal method used to initialize/retrieve MongoDB connection

        :return: MongoClient instance
        """
        if self._mongodb_connection is None:
            self._mongodb_connection = self._get_mongo_client()
            return self._mongodb_connection
        else:
            return self._mongodb_connection

    def _get_mongo_client(self):
        """ Method used in order to obtain a MongoDB connection instance

        :return: MongoClient instance if operation succeed
        """
        logger.debug("Trying to connect to MongoDB server")
        # try:
        if self.is_internal:
            from vulture_toolkit.system.database_client import DataBaseClient
            client = DataBaseClient().connection
        else:
            connection_uri = self._get_mongodb_connection_uri()
            #SSL Connexion is required
            if self.db_client_cert:

                #Store certificate and get path
                certificate_path, chain_path = self.db_client_cert.write_MongoCert ()
                client = MongoClient(connection_uri, ssl=True, ssl_certfile=certificate_path, ssl_ca_certs=chain_path, replicaset=self.replicaset, read_preference=ReadPreference.SECONDARY_PREFERRED)
            else:
                client = MongoClient(connection_uri, replicaset=self.replicaset, read_preference=ReadPreference.SECONDARY_PREFERRED)

        # except PyMongoError as e:
        #     raise AuthenticationError('Unable to connect to MongoDB database')

        return client

    def _get_collection(self, name):
        # try:
        database = getattr(self._get_connection(), self.db_name)
        collection = getattr(database, name)
        return collection
        # except Exception as e:
        #     logger.exception(e)
        #     return None

    def _get_user_filter(self):
        """ Internal method used to generate MongoDB request

        :return:
        """
        attributes = (
            self.user_column,
            self.password_column,
            self.user_phone_column,
            self.user_email_column,
            self.change_pass_column
        )
        qry_filter = {}
        for attr in attributes:
            if attr:
                qry_filter[attr] = 1
        if len(qry_filter) == 0:
            qry_filter = None
        return qry_filter


    def search_user (self, username):
        """ Public method used to search a user inside MongoDB repository

        :param username: String with username
        :return: String with username if found, None otherwise
        """
        logger.info("Searching for username {}".format(username))
        user_collection = self._get_collection(self.user_collection)
        if user_collection:
            query = {self.user_column: username}
            query_filter = self._get_user_filter()
            for attr in self.oauth2_attributes:
                query_filter[attr] = 1
            logger.debug("MongoDB query is: {},{}".format(query, query_filter))
            res = user_collection.find(query, query_filter)
            return res
        else:
            return None


    def search_user_by_email (self, email):
        """ Public method used to search a user inside MongoDB repository

        :param email: String with email address
        :return: String with username if found, None otherwise
        """
        logger.info("Searching for email address {}".format(email))
        user_collection = self._get_collection(self.user_collection)
        if user_collection:
            query = {self.user_email_column: email}
            query_filter = self._get_user_filter()
            logger.debug("MongoDB query is: {},{}".format(query, query_filter))
            res = user_collection.find(query, query_filter)

            if not res.count():
                raise UserNotFound("No result found in database for email '{}'".format(email))

            return res[0][self.user_column]

        raise UserNotFound("Cannot find users collection in Database")


    def update_password (self, username, hashed_password):
        """ Update a user password inside SQL Database

        :param username: String with username
        :param hashed_password: String with hashed password
        :return: True if Success, None otherwise
        """
        logger.info("Updating password for username {}".format(username))

        """ First search for user """
        if self.search_user(username):
            user_collection = self._get_collection(self.user_collection)
            if user_collection:

                if self.change_pass_column:
                    user_collection.update_one ({self.user_column:username},{"$set":{self.password_column:hashed_password, self.change_pass_column:0}})
                else:
                    user_collection.update_one ({self.user_column:username},{"$set":{self.password_column:hashed_password}})
                return True
            else:
                raise ChangePasswordError("Cannot retrieve user's collection")
        else:
            raise UserNotFound("Cannot find user '{}'".format(username))


    def update_field(self, username, field_name, field_value):
        """ Update a user field inside SQL Database

        :param username: String with username
        :param field_name: String with field name to update
        :param field_value: String with field value to set
        :return: True if Success, None otherwise
        """
        logger.info("Updating {} for username {}".format(field_name, username))

        """ First search for user """
        if self.search_user(username):
            user_collection = self._get_collection(self.user_collection)
            if user_collection:
                # Encode and decode JSON to prevent injection
                query = json_loads(json_dumps({self.user_column: username},
                                              {"$set": {field_name: field_value}}))
                user_collection.update_one(query)
                return True
            else:
                raise ChangePasswordError("Cannot retrieve user's collection")
        else:
            raise UserNotFound("Cannot find user '{}'".format(username))

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

    def _get_mongodb_connection_uri(self):
        """ Method used to build MongoDB connection URI

        :return: String with MongoDB URI
        """
        logger.debug("Building MongoDB connection URI")
        uri = "mongodb://{}:{}@{}:{}/{}"
        attributes = ['user', 'password']
        for attr in attributes:
            field = getattr(self, attr)
            if field:
                setattr(self, attr, urllib.parse.quote_plus(field))
            else:
                setattr(self, attr, '')

        uri = uri.format(self.user, self.password, self.host, self.port, self.db_name)
        #If no username there is a problem. URI will be, for example "mongodb://:@127.0.0.1:9091/vulture"
        # The ':@' needs to be removed
        uri = uri.replace ("mongodb://:@", "mongodb://")

        logger.debug("MongoDB connection URI is: {}".format(uri))
        return uri

    def _get_hashed_password(self, user_info):
        try:
            hashed_password = user_info[self.password_column]
        except Exception as e:
            logger.error("Unable to retrieve password from database")
            logger.exception(e)
            raise AuthenticationError("Unable to retrieve password from "
                                      "database, please ensure '{}' field "
                                      "exist".format(self.password_column))
        return hashed_password

    def get_user_infos(self, username):
        """ Search user into database, and return a dict with columns filled-in 
        If multiple users exists with the same username, return the first
        """
        users_infos = self.search_user(username)
        if users_infos and users_infos.count() > 0:
            user_infos = users_infos[0]
            return {
                'login': user_infos[self.user_column],
                'phone': user_infos.get(self.user_phone_column, "") if self.user_phone_column else "",
                'email': user_infos.get(self.user_email_column, "") if self.user_email_column else "",
                'password_expired': self._is_password_expired(user_infos),
                'account_locked': False
            }
        else:
            logger.error("Unable to found username {}".format(username))
            raise UserNotFound("User '{}' not found in database".format(username))


    def authenticate (self, username, password, **kwargs):
        """ Authentication method using MongoDB server as repository

        :param username: String with username
        :param password: String with password
        :return: True if authentication was successful, None otherwise
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

                    # Retrieve mobile and email
                    self.user_phone, self.user_email = 'N/A', 'N/A'
                    if self.user_phone_column is not None:
                        self.user_phone = row.get(self.user_phone_column, 'N/A')
                    if self.user_email_column is not None:
                        self.user_email = row.get(self.user_email_column, 'N/A')
                    if self.change_pass_column is not None:
                        self.change_pass = self._is_password_expired(row)

                    if return_status is True:
                        return True

                    result = {
                        'dn': row[self.user_column],
                        'user_phone': self.user_phone,
                        'user_email': self.user_email,
                        'password_expired': self._is_password_expired(row),
                        'account_locked': False
                    }

                    if self.enable_oauth2:
                        if str(self.oauth2_type_return) == 'dict':
                            oauth2_scope = dict()
                        elif str(self.oauth2_type_return) == 'list':
                            oauth2_scope = list()
                        else:
                            logger.error("Returned type of values selected in GUI is Unknown !")
                            return result

                        if self.oauth2_attributes:
                            for attr in self.oauth2_attributes:
                                try:
                                    attr_value = row.get(attr, None)
                                    if attr_value is None:
                                        logger.error("Unable to find oauth2 attribute name '{}' for user '{}'".format(attr, username))
                                        attr_value = 'N/A'

                                    if str(self.oauth2_type_return) == 'dict':
                                        oauth2_scope[attr] = attr_value
                                    elif self.oauth2_type_return == 'list':
                                        oauth2_scope.append(attr_value)

                                except Exception as e:
                                    logger.error("Unable to retrieve field {} for username {} in MongoDB backend : {}".format(attr,username, str(e)))
                        else:
                            oauth2_scope = '{}'

                        oauth2_result = {
                             'token_ttl': self.oauth2_token_ttl,
                             'token_return_type': self.oauth2_token_return,
                             'scope' : oauth2_scope
                         }
                        result['oauth2'] = oauth2_result

                    return result

            logger.error("Unable to authenticate username {}".format(username))
            raise AuthenticationError("Invalid credentials")
        else:
            logger.error("Unable to found username {}".format(username))
            raise UserNotFound("{} doesn't exist in database".format(username))

    def test_mongodb_connection(self):
        """ Test method of MongoDB connection

        :return: Dict with connection status
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
        """ Method used to perform test search over MongoDB Repository
        :param username: String with username
        :param password: String with password
        """
        response = {
            'status': None,
            'reason': None,
            'password_expired': False
        }

        try:
            response['status'] = self.authenticate(username, password, return_status=True)

        except AuthenticationError as e:
            response['status'] = False
            response['reason'] = str(e)
        except Exception as e:
            response['status'] = False
            response['reason'] = str(e)

        if self.user_phone_column is not None:
            response['user_phone'] = self.user_phone
        if self.user_email_column is not None:
            response['user_email'] = self.user_email
        if self.change_pass_column is not None:
            response['password_expired'] = self.change_pass

        return response

    def add_new_user(self, username, password, email, phone):
        """ Public method used to insert a new user inside MongoDB repository

        :param username: String with username
        :return: String with username if found, None otherwise
        """
        hashed_password = self._get_password_hash(password)
        logger.info("Adding new user with username {}".format(username))
        user_collection = self._get_collection(self.user_collection)
        if user_collection:
            query = {
                self.user_column: username,
                self.password_column: hashed_password
            }
            if self.user_email_column:
                query[self.user_email_column] = email
            if self.user_phone_column:
                query[self.user_phone_column] = phone
            if self.change_pass_column:
                if self.change_pass_value.lower() != "false":
                    query[self.change_pass_column] = "false"
                else:
                    query[self.change_pass_column] = "0"

            logger.debug("MongoDB query is: {}".format(query))
            id = user_collection.insert_one(query)
            return id
        else:
            # RAISE ?
            return None

    def delete_user(self, username):
        """ 
        """
        logger.info("Deleting user having username {}".format(username))

        """ First search for user """
        if self.search_user(username):
            user_collection = self._get_collection(self.user_collection)
            if user_collection:
                user_collection.delete_one({self.user_column: username})
                return True
            else:
                raise ChangePasswordError("Cannot retrieve user's collection")
        else:
            raise UserNotFound("Cannot find user '{}'".format(username))
