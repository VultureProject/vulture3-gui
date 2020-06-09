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
import json
import logging
import pytz
from calendar import monthrange
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ElasticsearchException
from vulture_toolkit.log.reporting_dict import type_of_dict, reporting_dicts
from .exceptions import ClientLogException

logger = logging.getLogger('debug')
from .base_log import BaseLog



class ElasticSearchClient(BaseLog):
    def __init__(self, settings):
        """ Instantiation method

        :param settings:
        :return:
        """
        # Connection settings
        self.access_type_name   = settings.es_access_type_name
        self.dateformat         = settings.es_dateformat
        self.index_name         = {
            'access'       : settings.es_access_index_name,
            'packet_filter': settings.es_packetfilter_index_name,
            'vulture'      : settings.es_vulturelogs_index_name,
            'diagnostic'   : settings.es_diagnostic_index_name,
        }

        urls = settings.es_host.split(',')

        # Handle authentication parameters
        user = settings.es_user
        if user:
            credential = (user, settings.es_password)
            self.els = Elasticsearch(urls, send_get_body_as='GET', http_auth=credential)
        else:
            self.els = Elasticsearch(urls, send_get_body_as='GET')

    def _prepare_index_name(self, type_log, start_date, end_date):
        """ Return every index name between two dates
        """
        if (isinstance(start_date, str) and isinstance(end_date, str)) or (isinstance(start_date, unicode) and isinstance(end_date, unicode)):
            start_date = parse(start_date)
            end_date   = parse(end_date)

        delta      = relativedelta(end_date, start_date)
        index_list = []

        if delta.months >= 1:
            wildcard_format = self.dateformat.replace("%d", "*")
            months_nb = 1

            if delta.days + start_date.day > monthrange(start_date.year, start_date.month)[1]:
                months_nb += 1

            for i in range(delta.months + months_nb):
                date_temp = start_date + relativedelta(months=i)
                index_list.append(self.index_name[type_log]+"-"+date_temp.strftime(wildcard_format))

        else:

            hours_nb = 1
            if delta.hours + start_date.hour > 24:
                hours_nb += 1

            for i in range(delta.days + hours_nb):
                date_temp = start_date + datetime.timedelta(days=i)
                index_list.append(self.index_name[type_log]+"-"+date_temp.strftime(self.dateformat))

        return ','.join(index_list)

    def _prepare_filter(self, filter_data, type_log, sort):
        """ Return a string formatted for els filter
            params: filter_date: all filter from the gui
            params: type_logs: type of logs to search
            FORMAT: champs:"valeur"&champs:"valeur"
        """


        if sort['sorting'] == 'time':
            sort['sorting'] = "timestamp"

        q = {
            "sort": {
                sort["sorting"]: {"order": sort['type_sorting']}
            },
            "query": {
                "bool": {
                    "must": {
                        "range": {
                            "timestamp": {
                                "gte"   : parse(filter_data['startDate']),
                                "lte"   : parse(filter_data['endDate'])
                            }
                        }
                    },
                    "filter": {}
                }
            }
        }

        if sort['sorting'] is None and sort['type_sorting'] is None:
            q['sort'] = {}

        if "rules" in filter_data:
            if len(filter_data["rules"]):
                ## IF search, add a query
                rules = filter_data['rules']
                q['query']['bool']['filter'] = rules

        if type_log == "access":
            if 'bool' in q['query']['bool']['filter'].keys():
                if 'must' in q['query']['bool']['filter']['bool'].keys():
                    q['query']['bool']['filter']['bool']['must'].append({
                        'match': {"app_name": str(filter_data['app']['name']).replace(' ', '_')}
                    })
                    return q

                q['query']['bool']['filter']['bool']['must'] = [{'match': {'app_name': str(filter_data['app']['name']).replace(' ', '_')}}]
                return q

            q['query']['bool']['filter']['bool'] = {'must': [{'match': {'app_name': str(filter_data['app']['name']).replace(' ', '_')}}]}
            return q

        elif type_log == 'packet_filter':
            if 'bool' in q['query']['bool']['filter'].keys():
                if 'must' in q['query']['bool']['filter']['bool'].keys():
                    q['query']['bool']['filter']['bool']['must'].append({
                        'match': {"hostname": filter_data['node']}
                    })
                    return q

                q['query']['bool']['filter']['bool']['must'] = [{'match': {'hostname': filter_data['node']}}]
                return q

            q['query']['bool']['filter']['bool'] = {'must': [{'match': {'hostname': filter_data['node']}}]}
            return q

        elif type_log == 'diagnostic':
            if 'check_diagnostic'in filter_data and filter_data['check_diagnostic']:
                if 'bool' in q['query']['bool']['filter'].keys():
                    if 'must' in q['query']['bool']['filter']['bool'].keys():
                        q['query']['bool']['filter']['bool']['must'].extend((
                            {'match': {"node_name": filter_data['node_name']}},
                            {'match': {"test_module": filter_data['test_module']}},
                        ))
                        if 'test_name' in filter_data:
                            q['query']['bool']['filter']['bool']['must'].append(
                                {'match': {"test_name": filter_data['test_name']}}
                            )
                        return q

                    q['query']['bool']['filter']['bool']['must'] = [
                        {'match': {'node_name': filter_data['node_name']}},
                        {'match': {'test_module': filter_data['test_module']}},
                    ]
                    if 'test_name' in filter_data:
                        q['query']['bool']['filter']['bool']['must'].append(
                            {'match': {"test_name": filter_data['test_name']}}
                        )
                    return q

                q['query']['bool']['filter']['bool'] = {
                    'must': [
                        {'match': {"node_name": filter_data['node_name']}},
                        {'match': {"test_module": filter_data['test_module']}},
                    ]
                }
                if 'test_name' in filter_data:
                    q['query']['bool']['filter']['bool']['must'].append(
                        {'match': {"test_name": filter_data['test_name']}}
                    )
                return q

        return q

    def _prepare_sort(self, params):
        """ Return a string
            Format: {'champs': {'order': 'asc/desc'}}
        """
        if params['sorting'] == 'time':
            params['sorting'] = "@timestamp"

        return "{}:{}".format(params['sorting'], params['type_sorting'])

    def _prepare_filter_search(self, function_dict, function, params):
        """ Private method, prepare filter for aggregation on elasticsearch
        :param params: data for search
        :param delta: delta between start date and end date
        :param args: other filter (format: {'match': {'key': 'value'}})
        return: dict filter for elasticsearch
        """
        if params['type_logs'] == 'access':
            search = {
                    "aggs": {
                        function : {
                        "filter": {
                            "terms": {
                                'app_name': [app.name.replace(' ', '_') for app in params['apps']]
                            }
                        },
                        "aggs": {
                            function: {
                                "date_range": {
                                    "field": "timestamp",
                                    "ranges": {
                                            "from": self.startDate, "to": self.endDate
                                        }
                                }
                            }
                        },
                    }
                },
                    "size":0
            }
        elif params['type_logs'] == 'packet_filter':
            search = {
                    "aggs": {
                        function : {
                        "filter": {
                            "regexp": {
                                "hostname" : params['node']
                            }
                        },
                        "aggs": {
                            function: {
                                "date_range": {
                                    "field": "timestamp",
                                    "ranges": {
                                            "from": self.startDate, "to": self.endDate
                                        }
                                }
                            }
                        },
                    }
                },
                    "size":0
            }

        if type_of_dict(function, "date_based"):
            self._set_date_accuracy()
            function_dict['aggs'][function]['date_histogram']['interval'] = self.date_accuracy

        search['aggs'][function]['aggs'][function]['aggs'] = function_dict['aggs']

        try:
            search['query'] = function_dict['query']
        except:
            pass

        return search

    def _format_data(self, data, function):
        """ Private method used to format data after an elastic aggregation. Returned formatted data in the same format as other BaseLog instances

        :param data: List of
        :param function: function name of current reporting_dicts
        :return: formatted data
        """
        formatted_data = []

        try:
            if type_of_dict(function, "date_based"):
                if type_of_dict(function, "multiple_series"):
                    formatted_data = {}
                    for row in data['aggregations'][function][function]['buckets'][0][function]['buckets']:
                        for sub_row in row[function]['buckets']:
                            date = parse(row['key_as_string'])
                            result = {"name": date}


                            if function == 'request_count':
                                result['value'] = sub_row['doc_count']
                            elif sub_row['avg_bucket']['value'] is not None:
                                result['value'] = sub_row['avg_bucket']['value']
                            else:
                                result['value'] = 0

                            try:
                                formatted_data[sub_row['key']].append(result)
                            except:
                                formatted_data[sub_row['key']] = [result]

                else:
                    for row in data['aggregations'][function][function]['buckets'][0][function]['buckets']:
                        date = parse(row['key_as_string'])
                        result = {"name": date}
                        if function.startswith('pf_traffic'):
                            result['value'] = row['doc_count']
                        elif row['avg_bucket']['value'] is not None:
                                result['value'] = row['avg_bucket']['value']
                        else:
                            result['value'] = 0

                        formatted_data.append(result)

            elif function == 'static_requests':
                for row in data['aggregations'][function][function]['buckets'][0][function]['buckets']:
                    for sub_row in row[function]['buckets']:
                        result = {"name": {"uri": sub_row["key"], "app": row['key']}, "value": sub_row['doc_count']}
                        formatted_data.append(result)

            elif function == "reputation_tags":
                for row in data['aggregations'][function][function]['buckets'][0][function]['buckets']:
                    ips = []
                    for sub_row in row[function]['buckets']:
                        ips.append({"ip": sub_row["key"], "value": sub_row['doc_count']})

                    result = {"name": row['key'],"ips" : ips, "value": row['doc_count']}
                    formatted_data.append(result)

            elif type_of_dict(function, "multiple_series"):
                for row in data['aggregations'][function][function]['buckets'][0][function]['buckets']:
                    serie_count = []
                    for sub_row in row[function]['buckets']:
                        serie_count.append({"name": sub_row["key"], "value": sub_row['doc_count']})

                    result = {"name": row['key'],"value" : serie_count}
                    formatted_data.append(result)
            else:
                for row in data['aggregations'][function][function]['buckets'][0][function]['buckets']:
                    result = {"name" : row['key'], "value" : row['doc_count']}
                    formatted_data.append(result)

        except KeyError:
            pass

        return formatted_data

    def aggregate(self, params):
        """ Public method used to fetch data to build histogram or lines for echarts
        It counts the number of hits and group by desired field over the desired period of time

        :param params: Dict of
        :return: data
        """
        try:
            self.startDate = parse(params['startDate']).astimezone(pytz.utc)
            self.endDate   = parse(params['endDate']).astimezone(pytz.utc)

            self.delta     = self.endDate - self.startDate
            self.report_dict  = reporting_dicts[params['reporting_type']]

            index  = self._prepare_index_name(params['type_logs'], self.startDate, self.endDate)
            result = {}
            for function in self.report_dict.keys():
                try:
                    search = self._prepare_filter_search(self.report_dict[function]['elastic'], function, params)
                    data   = self.els.search(index=index, body=search, ignore_unavailable=True)
                    result[function] = self._format_data(data, function)
                except ElasticsearchException:
                    logger.error("An error occurred during ElasticSearch aggregation {}".format(function), exc_info=1)
                    result[function] = {} if type_of_dict(function, "multiple_series") else []
                    raise ClientLogException("An error occurred with ElasticsearchClient")
            return result
        except Exception:
            logger.error("An error occurred with ElasticSearch aggregate()", exc_info=1)
            raise ClientLogException("An error occurred with ElasticsearchClient")

    def search(self, params=None, id_query=None):
        """ Public method used to search logs data inside ElasticSearch repository

        :param params: Dict of
        :return: data
        """
        data     = []
        max_data = 0


        try:
            ### Execute search
            if params is not None:
                ## Construct of search, sort, and the list of index
                sorting = {
                    'sorting': params['sorting'],
                    'type_sorting': params['type_sorting']
                }

                search = self._prepare_filter(params['filter'], params['type_logs'], sorting)
                # sort   = self._prepare_sort(params)
                index  = self._prepare_index_name(params['type_logs'], params['filter']['startDate'], params['filter']['endDate'])

                if params['start'] is not None:
                    page = self.els.search(index=index, from_=params['start'], body=search, size=params['length'], ignore_unavailable=True)
                else:
                    page = self.els.search(index=index, scroll="10m", body=search, ignore_unavailable=True)

                max_data  = page['hits']['total']
                data_temp = page['hits']['hits']

                try:
                    scroll_id   = page['_scroll_id']
                    scroll_size = len(page['hits']['hits'])

                    while (scroll_size > 0):
                        page        = self.els.scroll(scroll_id=scroll_id, scroll='10m')
                        scroll_id   = page['_scroll_id']
                        scroll_size = len(page['hits']['hits'])
                        data_temp.extend(page['hits']['hits'])

                except KeyError:
                    # No enought result to scroll, or no scroll, passing
                    pass

                data = []
                for x in data_temp:
                    temp = {
                        '_id' : x["_id"],
                        'time': x['_source']['timestamp']
                    }

                    for k, v in x['_source'].items():
                        if not params['dataset']:
                            try:
                                temp[k] = json.dumps(dict(v))
                            except:
                                temp[k] = v
                        else:
                            temp[k] = v

                    data.append(temp)

            else:
                search = {
                  "query": {
                    "terms": {
                      "_id": [id_query]
                    }
                  }
                }

                index = ','.join(self.els.indices.get_aliases().keys())
                data = self.els.search(index=index, body=search)

        except Exception as e:
            logger.error("An error occurred while fetching logs", exc_info=1)
            max_data = 0
            data     = []
            raise ClientLogException("An error occurred while fetching logs with Elasticsearch client")

        return {
            'max': max_data,
            'data': data,
        }

    def _prepare_filter_map(self, filters):
        aggs = {
          "size": 0,
          "aggs": {
            "count_by_country": {
              "terms": {
                "field": "country"
              }
            }
          },
          'query': {
            'bool': {
                'must'  : []
            }
          }
        }

        if filters['apps']:
            aggs['query']['bool']['must'].append({"terms": {'app_name': [app.name.replace(' ', '_') for app in filters['apps']]}})

        if filters['codes']:
            aggs['query']['bool']['must'].append({"terms": {'http_code': [int(code) for code in filters['codes']]}})

        if filters['tags']:
            aggs['query']['bool']['must'].append({'terms': {'reputation': filters['tags']}})

        return aggs

    def map(self, params):
        try:
            index = self._prepare_index_name("access", params['startDate'], params['endDate']).split(',')
            aggs  = self._prepare_filter_map(params)
            data  = self.els.search(index=",".join(index), body=aggs, ignore_unavailable=True)

            results = {}

            try:
                for d in data['aggregations']['count_by_country']['buckets']:
                    if d['key'] not in (None, "-"):
                        results[d['key']] = d['doc_count']
            except KeyError:
                pass

            return results
        except Exception:
            logger.error("An error occurred during ElasticsearchClient map()", exc_info=1)
            raise ClientLogException("An error occurred with ElasticsearchClient")

    def logs(self, type_logs, log):
        index = self._prepare_index_name(type_logs, datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))

        self.els.index(index=index, doc_type='logs', body=log)
        return True
