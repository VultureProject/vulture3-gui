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
__author__ = "Florian Hagniel"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = ''

import os
import sys

from pymongo import MongoClient, ReadPreference

sys.path.append("/home/vlt-gui/vulture")
os.environ['DJANGO_SETTINGS_MODULE'] = 'vulture.settings'
from django.conf import settings
from vulture_toolkit.system import ssl_utils
from vulture_toolkit.network import net_utils
from vulture_toolkit.system.mongo_base import MongoBase

class DataBaseClient(MongoBase):
    """

    """
    def __init__(self, *args, **kwargs):
        """Initialize connection to database

        :param host: string (ex: vulture-node1:9091) or tuple
        (ex: ('vulture-node1',9091))
        :return:
        """
        super(DataBaseClient, self).__init__(*args, **kwargs)
        if kwargs.get('host') is not None:
            host = kwargs.get('host')
            if isinstance(host, tuple):
                host = '{}:{}'.format(host[0], host[1])
            self.connection_uri = 'mongodb://{}'.format(host)
            #a.connection['local']['system.replset'].find_one()
        else:
            self.connection_uri = self.get_mongodb_connection_uri()
        try:
            c = MongoClient(host=self.connection_uri, ssl=True,
                            ssl_certfile=ssl_utils.get_pem_path(),
                            ssl_ca_certs=ssl_utils.get_ca_cert_path(),
                            read_preference=ReadPreference.SECONDARY_PREFERRED)

            self.hosts = list()
            self.primary_host = None
            self.connection = c
        except Exception as e:
            raise Exception("Database connection failed")

    def replica_initialization(self):
        """Configure the replica set on a primary Node, ie execute the command
        replSetInitiate

        """
        replica_host = "{}:{}".format(net_utils.get_hostname(), settings.MONGODBPORT)
        self.logger.info("Trying to initiate replicaSet on {}"
                         .format(replica_host))
        res = self.connection.admin.command("replSetInitiate", 'Vulture',
                                          [replica_host])
        #TODO test Exception and log events
        self.logger.info("ReplicaSet successfully initialized on {}"
                         .format(replica_host))
        self.connection.close()
