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
__author__     = "Olivier de Régis"
__credits__    = []
__license__    = "GPLv3"
__version__    = "3.0.0"
__maintainer__ = "Vulture Project"
__email__      = "contact@vultureproject.org"
__doc__        = ''

import datetime
import pytz
import json
import logging
import urllib
import copy

from bson.objectid import ObjectId
from bson import SON
from pymongo import MongoClient
from pymongo import ReadPreference
from pymongo.errors import PyMongoError
from vulture_toolkit.log.reporting_dict import type_of_dict, reporting_dicts
from dateutil.parser import parse

logger = logging.getLogger('debug')
from .base_log import BaseLog
from .exceptions import ClientLogException


class MongoDBClient(BaseLog):
    type_sorting = {
        'asc' : 1,
        'desc': -1
    }

    def __init__(self, settings):
        """ Instantiation method

        :param settings:
        :return:
        """
        # Connection settings
        self.is_internal    = settings.is_internal
        self.host           = settings.db_host
        self.port           = settings.db_port
        self.db_name        = settings.db_name
        self.user           = settings.db_user
        self.password       = settings.db_password
        self.db_client_cert = settings.db_client_cert
        self.replicaset     = settings.replicaset

        if not self.replicaset or self.replicaset == "":
            self.replicaset = None

        self._mongodb_connection = None

        # Log related settings
        if self.is_internal:
            self.db_name = 'logs'

            self.collection_name = {
                'access'       : 'access',
                'packet_filter': 'vulture_pf',
                'vulture'      : 'vulture_logs',
                'diagnostic'   : 'vulture_diagnostic',
            }

        else:
            self.collection_name = {
                'access'       : settings.db_access_collection_name,
                'packet_filter': settings.db_packetfilter_collection_name,
                'vulture'      : settings.db_vulturelogs_collection_name,
                'diagnostic'   : settings.db_diagnostic_collection_name
            }

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
        try:
            if self.is_internal:
                from vulture_toolkit.system.database_client import DataBaseClient
                client = DataBaseClient().connection
            else:
                connection_uri = self._get_mongodb_connection_uri()
                #SSL Connexion is required
                if self.db_client_cert:

                    #Store certificate and get path
                    certificate_path, chain_path = self.db_client_cert.write_MongoCert()
                    client = MongoClient(connection_uri, ssl=True, ssl_certfile=certificate_path, ssl_ca_certs=chain_path, replicaset=self.replicaset, read_preference=ReadPreference.SECONDARY_PREFERRED)
                else:
                    client = MongoClient(connection_uri, replicaset=self.replicaset, read_preference=ReadPreference.SECONDARY_PREFERRED)

        except PyMongoError as e:
            raise ClientLogException('Unable to connect to MongoDB database')

        return client

    def _get_collection(self, name):
        try:
            database   = getattr(self._get_connection(), self.db_name)
            collection = getattr(database, self.collection_name[name])
            return collection
        except Exception as e:
            return None

    def _prepare_filter(self, filter_data, type_logs):
        """ Return a dict formatted for mongoDB filter
        """
        attr = {}
        if type_logs == 'access':

            attr = {
                'app_name': str(filter_data['app']['name']).replace(' ', '_'),
                'time'    : {
                    '$gte': parse(filter_data['startDate']),
                    '$lte': parse(filter_data['endDate'])
                }
            }

        elif type_logs == 'packet_filter':
            attr = {
                'hostname': {'$regex': filter_data['node']},
                'time'    : {
                    '$gte': parse(filter_data['startDate']),
                    '$lte': parse(filter_data['endDate'])
                }
            }

        elif type_logs == 'diagnostic':
            if 'check_diagnostic'in filter_data and filter_data['check_diagnostic']:
                try:
                    attr = {
                        'node_name'  : filter_data['node_name'],
                        'test_module': filter_data['test_module'],
                    }
                    if 'test_name' in filter_data:
                        attr['test_name'] = filter_data['test_name']
                except:
                    pass
            else:
                attr = {
                    'time'    : {
                        '$gte': parse(filter_data['startDate']),
                        '$lte': parse(filter_data['endDate'])
                    }
                }

        attr.update(filter_data.get('rules', {}))
        return attr

    def _prepare_filter_match_daterange(self, params):
        """ Private method, prepare filter for matching data according to a date range. Use aggregate
        :params: apps: applications
        :return: dict of filter for mongoDB
        """
        if params['type_logs'] == 'access':
            match = {
                    '$match': {
                        'app_name': {'$in': [app.name.replace(' ', '_') for app in params['apps']]},
                        'time'    : {
                            '$gte': self.startDate,
                            '$lte': self.endDate
                        }
                    }
                }
        elif params['type_logs'] == 'packet_filter':
            match = {
                '$match': {
                    'hostname': {'$regex': params['node']},
                    'time'    : {
                        '$gte': self.startDate,
                        '$lte': self.endDate
                    }
                }
            }
        return match

    def _prepare_filter_map(self, filters):
        match = {
            '$match': {
                'time'    : {
                    '$gte': filters['startDate'],
                    '$lte': filters['endDate']
                }
            }
        }

        if filters['codes']:
            match['$match']['http_code'] = {"$in": [int(code) for code in filters['codes']]}

        if filters['tags']:
            match['$match']['reputation'] = {"$in": filters['tags']}

        if filters['apps']:
            match["$match"]['app_name'] = {'$in': [app.name.replace(' ', '_') for app in filters['apps']]}

        aggs = [match, {
            "$group": {
                "_id"  : "$country",
                "count": {"$sum": 1},
            }
        }]
        return aggs

    def _check_args(self, attr, function):
        """ Private method, adds more precise columns according to request's timedelta.

        :param attr: attributes for mongo
        :param function: function name of current reporting_dicts
        :returns: attribute filtes for mongo query
        """

        if type_of_dict(function, "date_based"):
            self._set_date_accuracy()

            try:
                group = attr[1]['$group']
            except:
                group = attr[2]['$group']

            if self.date_accuracy == 'minute':
                group['_id'].update({'minute': {'$minute': '$time'}})
                group['_id'].update({'hour': {'$hour': '$time'}})
                group['_id'].update({'day': {'$dayOfMonth': '$time'}})

            elif self.date_accuracy == 'hour':
                group['_id'].update({'day': {'$dayOfMonth': '$time'}})
                group['_id'].update({'hour': {'$hour': '$time'}})

            elif self.date_accuracy == 'day':
                group['_id'].update({'day': {'$dayOfMonth': '$time'}})
        return attr

    def _format_data(self, data, function):
        """ Private method, format data obtained after mongo or els aggregate, format timestamps according
        to request's timedelta

        :param data: data obtained after aggregation
        :param function: function name of current reporting_dicts
        :return: array of filled results
        """
        if type_of_dict(function, "date_based"):
            series = []
            m_series = {}
            for row in data:
                if self.date_accuracy == "minute":
                    date = datetime.datetime(row['name']['year'], row['name']['month'], row['name']['day'], row['name']['hour'], row['name']['minute'], 0)

                elif self.date_accuracy == "hour":
                    date = datetime.datetime(row['name']['year'], row['name']['month'], row['name']['day'], row['name']['hour'], 0, 0)

                elif self.date_accuracy == "day":
                    date = datetime.datetime(row['name']['year'], row['name']['month'], row['name']['day'],0, 0, 0)

                else:
                    date = datetime.datetime(row['name']['year'], row['name']['month'], 1, 0, 0, 0)

                date = date.replace(tzinfo=pytz.UTC)
                result = dict(name=date, value=row["value"])

                if type_of_dict(function, "multiple_series"):
                    try:
                        m_series[row['name']['series']].append(result)
                    except:
                        m_series[row['name']['series']] = [result]

                else:
                    series.append(result)

            return m_series if type_of_dict(function, "multiple_series") else series

        else:
            return data

    def aggregate(self, params):
        """ Public method used to fetch data to build histogram or lines for echarts
        It counts the number of hits and group by desired field over the desired period of time

        :param params: Dict of
        :return: data
        """

        log_collection = self._get_collection(params['type_logs'])
        if not log_collection:
            return None
        try:
            self.startDate = parse(params['startDate']).astimezone(pytz.utc)
            self.endDate   = parse(params['endDate']).astimezone(pytz.utc)

            self.delta     = self.endDate - self.startDate
            self.report_dict  = reporting_dicts[params['reporting_type']]

            date_filter = self._prepare_filter_match_daterange(params)
            data = {}

            for function in self.report_dict.keys():
                try:
                    attr_filter = [date_filter]
                    for key, value in self.report_dict[function]['mongo'].items():
                        if "Pip" in key:
                            filt = {key.split("Pip")[0] : value}
                        else:
                            filt = {key : value}

                        attr_filter.append(copy.deepcopy(filt))

                    filters = self._check_args(attr_filter, function)
                    data[function] = log_collection.aggregate(filters)
                    data[function] = self._format_data(data[function], function)
                except PyMongoError:
                    logger.error("An error occurred during MongodbClient aggregation {}".format(function), exc_info=1)
                    data[function] = {} if type_of_dict(function, "multiple_series") else []
                    raise ClientLogException("An error occurred with Mongodb Client")
            return data
        except Exception as e:
            logger.exception(e)
            logger.error("An error occurred on MongodbClient aggregate()")
            raise ClientLogException("An error occurred with Mongodb Client")

    def search(self, params, id_query=None):
        """ Public method used to search logs data inside MongoDB repository

        :param params: Dict of parameters (application, type of logs, search, order...)
        :param id_query: ID, return only one result
        :return: data
        """
        log_collection = self._get_collection(params['type_logs'])
        if not log_collection:
            return None

        if id_query is None:
            attr_filter = self._prepare_filter(params['filter'], params['type_logs'])
            try:
                if params['start'] is not None:
                    data = [doc for doc in log_collection.find(attr_filter).sort(params['sorting'], self.type_sorting[params['type_sorting']]).limit(params['length']).skip(params['start'])]
                    max_data = log_collection.find(attr_filter).sort(params['sorting'], self.type_sorting[params['type_sorting']]).count()
                else:
                    data     = [doc for doc in log_collection.find(attr_filter)]
                    max_data = log_collection.find(attr_filter).count()

            except Exception:
                logger.error("An error occurred while fetching log", exc_info=1)
                max_data = 0
                data     = []
                raise ClientLogException("An error occurred while fetching logs with Mongodb Client")


            if not params['dataset']:
                for x in data:
                    try:
                        x['request_headers']  = json.dumps(dict(x['request_headers']))
                        x['response_headers'] = json.dumps(dict(x['response_headers']))
                        x['auditLogTrailer']  = json.dumps(dict(x['auditLogTrailer']))
                    except KeyError:
                        pass

        else:
            data = log_collection.find_one({'_id': ObjectId(id_query)})
            max_data = 0

        return {
            'max': max_data,
            'data': data,
        }

    def map(self, params):
        data = {}
        try:
            aggs = self._prepare_filter_map(params)
            log_collection = self._get_collection('access')
            for res in log_collection.aggregate(aggs):
                if res['_id'] not in (None, '-'):
                    try:
                        data[res['_id']] += res['count']
                    except KeyError:
                        data[res['_id']] = res['count']

            return data
        except Exception:
            logger.error("An error occurred during MongoClient map()", exc_info=1)
            raise ClientLogException("An error occurred with MongodbClient")

    def _get_mongodb_connection_uri(self):
        """ Method used to build MongoDB connection URI

        :return: String with MongoDB URI
        """
        uri        = "mongodb://{}:{}@{}:{}/{}"
        attributes = ['user', 'password']

        for attr in attributes:
            field = getattr(self, attr)
            if field:
                setattr(self, attr, urllib.quote(field))
            else:
                setattr(self, attr, '')

        uri = uri.format(self.user, self.password, self.host, self.port, self.db_name)
        #If no username there is a problem. URI will be, for example "mongodb://:@127.0.0.1:9091/vulture"
        # The ':@' needs to be removed
        uri = uri.replace("mongodb://:@", "mongodb://")
        return uri

    def logs(self, type_logs, log):
        log_collection = self._get_collection(type_logs)
        if not log_collection:
            return None

        log_collection.insert_one(log)

        return True

    def delete_logs(self, lastDate):
        for key, value in self.collection_name.items():
            log_collection = self._get_collection(value)
            if not log_collection:
                continue

            log_collection.remove({'time': {'$lt': lastDate}})

        return True
