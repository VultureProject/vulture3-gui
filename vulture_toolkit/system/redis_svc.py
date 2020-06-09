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
__author__ = "Florian Hagniel"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = 'Redis Toolkit'

import sys

sys.path.append("/home/vlt-gui/vulture")

import logging
import logging.config

from vulture_toolkit.system.service_base import ServiceBase
from vulture_toolkit.templates import tpl_utils
from vulture_toolkit.system.sys_utils import write_in_file


logger = logging.getLogger('services_events')


class RedisSvc(ServiceBase):

    def __init__(self):
        self.service_name = 'redis'

    @staticmethod
    def create_master_conf():
        """ Method in charge to build configurations files of a
        master Redis host (redis.conf + sentinel.conf)

        :return:
        """
        from vulture_toolkit.network.net_utils import get_hostname
        master_ip = get_hostname()
        parameters = {
            'is_redis_master': True,
            'master_ip': master_ip,
        }
        tpl, path = tpl_utils.get_template('redis')
        conf = tpl.render(conf=parameters)
        try:
            f = open(path, 'r')
            orig_conf = f.read()
        except IOError:
            orig_conf = None
        # Configuration file differs => writing new version
        if orig_conf != conf:
            write_in_file(path, conf)
        # Creating Sentinel conf
        tpl, path = tpl_utils.get_template('sentinel')
        conf = tpl.render(conf=parameters)
        try:
            f = open(path, 'r')
            orig_conf = f.read()
        except IOError:
            orig_conf = None
        # Configuration file differs => writing new version
        if orig_conf != conf:
            write_in_file(path, conf)

    @staticmethod
    def create_slave_conf(master_ip):
        """ Method in charge to build configurations files of a
        slave Redis host (redis.conf + sentinel.conf)

        :param master_ip: IP Address or hostname of Master host
        :return:
        """

        parameters = {
            'is_redis_master': False,
            'master_ip': master_ip,
        }
        # Creating Redis.conf
        tpl, path = tpl_utils.get_template('redis')
        conf = tpl.render(conf=parameters)
        try:
            f = open(path, 'r')
            orig_conf = f.read()
        except IOError:
            orig_conf = None
        # Configuration file differs => writing new version
        if orig_conf != conf:
            write_in_file(path, conf)
        # Creating Sentinel conf
        tpl, path = tpl_utils.get_template('sentinel')
        conf = tpl.render(conf=parameters)
        try:
            f = open(path, 'r')
            orig_conf = f.read()
        except IOError:
            orig_conf = None
        # Configuration file differs => writing new version
        if orig_conf != conf:
            write_in_file(path, conf)

    def get_master_ip(self):
        """ Method used to retrieve IP Address or hostname of
        Redis master host

        :return:
        """
        from redis import Redis
        try:
            redis = Redis()
            redis_info = redis.info()
            if redis_info.get('role') == 'master':
                from vulture_toolkit.network.net_utils import get_hostname
                return get_hostname()
            elif redis_info.get('role') == 'slave':
                return redis_info.get('master_host')
        except Exception as e:
            logger.exception(e)

    def start_service(self, service_name=None):
        svc_lst = ('redis', 'sentinel')
        for svc in svc_lst:
            super(RedisSvc, self).start_service(svc)

    def stop_service(self, service_name=None):
        svc_lst = ('redis', 'sentinel')
        for svc in svc_lst:
            super(RedisSvc, self).stop_service(svc)

    def restart_service(self, service_name=None):
        self.stop_service()
        self.start_service()