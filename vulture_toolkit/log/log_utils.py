#!/usr/bin/python
# -*- coding: utf-8 -*-
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
__author__ = "Olivier de Régis"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = ''

import datetime
import logging

# logger configuration
# import logging
# from vulture_toolkit.log.settings import LOG_SETTINGS
# logging.config.dictConfig(LOG_SETTINGS)
# logger = logging.getLogger('debug')

from gui.models.system_settings import Cluster
from gui.models.monitor_settings import Monitor
from vulture_toolkit.log.mongodb_client import MongoDBClient
from vulture_toolkit.log.elasticsearch_client import ElasticSearchClient
from gui.models.repository_settings import BaseAbstractRepository


class DatabaseHandler(logging.StreamHandler):
    """
    A handler class which writes formatted logging records to disk files.
    """
    def __init__(self, type_logs):
        """
        Open the specified file and use it as the stream for logging.
        """
        # keep the absolute path, otherwise derived classes which use this
        # may come a cropper when the current directory changes
        self._name   = "Database Handler"
        self.filters = []
        self.lock    = None

        cluster = Cluster.objects.get()
        try:
            logs_repository = cluster.system_settings.global_settings.repository
            if not logs_repository:
                for logs_repository in BaseAbstractRepository.get_data_repositories():
                    if logs_repository.is_internal:
                        break
        except:
            for logs_repository in BaseAbstractRepository.get_data_repositories():
                if logs_repository.is_internal:
                    break

        if logs_repository.type_uri == 'mongodb':
            self.client = MongoDBClient(logs_repository)
        elif logs_repository.type_uri == 'elasticsearch':
            self.client = ElasticSearchClient(logs_repository)

        self.type_logs = type_logs

    def _check_diagnostic_change(self, data):
        """
        Check if the status of a test changed
        :param data: The log data
        :return: True if the test result changed, False otherwise
        """
        # Determine limits of today for Elastic search
        start_day = datetime.date.today().strftime("%Y-%m-%dT00:00:00Z")
        end_day   = datetime.date.today().strftime("%Y-%m-%dT23:59:59Z")

        # Getting the last fail for comparison
        if data['test_name'] == 'All':
            params = {
                'start'       : 0,
                'length'      : 1,
                'sorting'     : 'time',
                'type_sorting': 'desc',
                'dataset'     : True,
                'type_logs'   : 'diagnostic',
                'filter'      : {
                    'check_diagnostic': True,
                    'startDate'       : start_day,
                    'endDate'         : end_day,
                    'node_name'       : data['node_name'],
                    'test_module'     : data['test_module'],
                }
            }
            last_fail_log = self.client.search(params)

        else:
            params = {
                'start'       : 0,
                'length'      : 1,
                'sorting'     : 'time',
                'type_sorting': 'desc',
                'dataset'     : True,
                'type_logs'   : 'diagnostic',
                'filter'      : {
                    'check_diagnostic': True,
                    'startDate'       : start_day,
                    'endDate'         : end_day,
                    'node_name'       : data['node_name'],
                    'test_module'     : data['test_module'],
                    'test_name'       : data['test_name'],
                }
            }
            last_fail_log = self.client.search(params)

        # Getting the last success for comparison
        params = {
            'start': 0,
            'length': 1,
            'sorting': 'time',
            'type_sorting': 'desc',
            'dataset': True,
            'type_logs': 'diagnostic',
            'filter': {
                'check_diagnostic': True,
                'startDate'       : start_day,
                'endDate'         : end_day,
                'node_name'       : data['node_name'],
                'test_module'     : data['test_module'],
                'test_name'       : 'All',
            }
        }
        last_success_log = self.client.search(params)

        if not last_fail_log['data'] and not last_success_log['data']:
            return True

        if last_fail_log['data'] and last_fail_log['data'][0]['test_name'] == 'All':
            return False

        # Let's compare the last logs to determine if we need to log the new event recorded
        if data['test_name'] == 'All':
            if not last_success_log['data']:
                return True

            elif not last_fail_log['data']:
                return False

            else:
                if last_success_log['data'][0]['time'] > last_fail_log['data'][0]['time']:
                    return False
                else:
                    return True

        else:
            if not last_success_log['data']:
                if data['message'] == last_fail_log['data'][0]['message']:
                    return False
                return True

            elif not last_fail_log['data']:
                return True

            else:
                if last_success_log['data'][0]['time'] > last_fail_log['data'][0]['time']:
                    return True
                else:
                    if data['message'] == last_fail_log['data'][0]['message']:
                        return False
                    return True

    def emit(self, record):
        """
        Emit a record.
        Save the log into the repository
        """

        try:
            data = {
                '@timestamp': datetime.datetime.now(),
                'time'      : datetime.datetime.now(),
                'log_level' : record.levelname,
                'filename'  : record.filename,
                'message'   : record.msg,
            }

            if self.type_logs == 'diagnostic':
                data['test_module'] = record.test_module
                data['test_name']   = record.test_name
                data['traceback']   = record.traceback
                data['node_name']   = record.node_name

                if not self._check_diagnostic_change(data):
                    return

            elif self.type_logs == 'vulture':
                data['log_name'] = record.name

            self.client.logs(self.type_logs, data)
        except:
            pass


class LogRotate:
    def __init__(self):
        cluster = Cluster.objects.get()

        for logs_repository in BaseAbstractRepository.get_data_repositories():
            if logs_repository.is_internal:
                break

        self.log_rotate = cluster.system_settings.global_settings.log_rotate
        self.client = MongoDBClient(logs_repository)

    def delete_logs(self):
        if self.log_rotate == 0:
            return True

        lastDate = (datetime.datetime.now() - datetime.timedelta(days=self.log_rotate-1))
        self.client.delete_logs(lastDate)

        lastDate = (datetime.datetime.now() - datetime.timedelta(days=30))
        [m.delete() for m in Monitor.objects.get(time__lt=lastDate)]
        return True
