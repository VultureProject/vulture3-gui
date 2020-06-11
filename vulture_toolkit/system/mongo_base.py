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
__doc__ = 'System Utils Database Toolkit'

import configparser
import os
import subprocess

os.environ['DJANGO_SETTINGS_MODULE'] = 'vulture.settings'
from vulture_toolkit.templates import tpl_utils

# Logger configuration
import logging
import logging.config
MONGODBCONFPATH = "/home/vlt-gui/vulture/vulture/mongodb.conf"


class MongoBase(object):
    """Base class for database wrapper

    """
    def __init__(self, *args, **kwargs):
        """Initialize connection to database

        :return:
        """
        self.logger = logging.getLogger('mongodb_events')

    def get_mongodb_connection_uri(self):
        """ Construct MongoDB connection URI, from mongodb.conf file
        this uri is used by Django

        :returns: A string containing a MongoDB connection URI
        """
        cfg = configparser.ConfigParser()
        uri = "mongodb://"
        try:
            cfg.read(MONGODBCONFPATH)
            for hostname in cfg.sections():
                for item in cfg.options(hostname):
                    ports = cfg.get(hostname, item).split(',')
                    for port in ports:
                        uri += hostname + ':' + port + ','
            return uri[:-1]
        except Exception as e:
            self.logger.error(e)

    def get_mongodb_hosts(self):
        """ Return list of mongodb hosts from mongodb.conf file

        :returns: A list containing hosts+port (eg: vulture-node1:9091)
        """
        cfg = configparser.ConfigParser()
        hosts_lst = list()
        try:
            cfg.read(MONGODBCONFPATH)
            for hostname in cfg.sections():
                for item in cfg.options(hostname):
                    ports = cfg.get(hostname, item).split(',')
                    for port in ports:
                        hosts_lst.append((hostname, int(port),))
            return hosts_lst
        except Exception as e:
            self.logger.error(e)

    def get_mongodb_dead_hosts(self):
        """ Return list of dead mongodb hosts from mongodb.conf file

        :returns: A list containing hosts+port (eg: vulture-node1:9091)
        """
        path = MONGODBCONFPATH + '.dead'
        cfg = configparser.ConfigParser()
        hosts_lst = list()
        try:
            cfg.read(path)
            for hostname in cfg.sections():
                for item in cfg.options(hostname):
                    ports = cfg.get(hostname, item).split(',')
                    for port in ports:
                        hosts_lst.append((hostname, int(port),))
            return hosts_lst
        except Exception as e:
            self.logger.error(e)

    def get_hosts_by_type(self, type):
        """Return list of host which satisfy condition given in parameter

        :param type: two values are allowed : DEAD (host not up) or UP (host up)
        :return: A list of tuple ('hostname', port)
        """
        hosts = self.get_mongodb_hosts() + self.get_mongodb_dead_hosts()
        dead_hosts = list()
        up_hosts = list()
        # Identify which hosts are UP.
        for host in hosts:
            up = self.mongod_is_alive(host)
            if not up:
                dead_hosts.append(host)
            else:
                up_hosts.append(host)
        if type == 'DEAD':
            return dead_hosts
        elif type == 'UP':
            return up_hosts
        else:
            raise Exception("You need to specify which type of host you are"
                            "looking for")

    @staticmethod
    def create_mongodb_conf():
        """Create the configuration of mongodb in /usr/local/etc/mongodb.conf
        """
        tpl, path = tpl_utils.get_template("mongodb")
        mongodb_conf = tpl.render()
        f = open(path, "w") #TODO ?
        f.write(mongodb_conf)
        f.close()

    @staticmethod
    def start_service():
        """ Start MongoDB Service

        :returns: True if success, False otherwise
        """
        # Executing service MongoDB start as vlt-sys user
        proc = subprocess.Popen(
            ['/usr/local/bin/sudo', '-u', 'vlt-sys', '/usr/local/bin/sudo',
             'service', 'mongod', 'start'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        res = proc.communicate()
        success = res[0]
        error = res[1]
        """
        if success:
            logger.info("MongoDB Service started")
        else:
            pattern = 'already running'
            reg = re.compile(pattern)
            if reg.search(error):
                logger.info("Service already started")
            else:
                logger.error(error)
                return False
        return True"""

    @staticmethod
    def stop_service():
        """

        :return:
        """
        pass

    @staticmethod
    def restart_service():
        """

        :return:
        """
        pass

    @staticmethod
    def add_replica_to_configuration_file(hostname, port):
        """ Add a MongoDB replica to mongodb.conf file,
        !! WARNING !!
        This method only add replica to configuration file used
        by pymongo, it don't add it to MongoDB ReplicaSet

        :param hostname: hostname of MongoDB server
        :param port: listening port on MongoDB server
        """
        port = str(port)
        cfg = configparser.ConfigParser()
        cfg.read(MONGODBCONFPATH)
        # Create new hostname and adding it's port
        # FIXME enable logger
        try:
            if isinstance(hostname, bytes):
                hostname = hostname.decode('utf8')
            cfg.add_section(hostname)
            cfg.set(hostname, 'port', port)
            #self.logger.info("New replica added : " + hostname)
        # Hostname already in configuration, adding port if not already exist
        except configparser.DuplicateSectionError:
            options = cfg.get(hostname, 'port').split(',')
            if port not in options:
                options.append(port)
                #self.logger.info("New replica added : " + hostname)
            cfg.set(hostname, 'port', ','.join(options))
        except Exception as e:
            pass#FIXME
            #self.logger.error(e)
        cfg.write(open(MONGODBCONFPATH, 'w'))

    @staticmethod
    def remove_replica_from_configuration_file(hostname, port):
        port = str(port)
        cfg = configparser.ConfigParser()
        cfg.read(MONGODBCONFPATH)
        # Create new hostname and adding it's port
        try:
            cfg.remove_section(hostname)
        except Exception as e:
            pass#FIXME
            #self.logger.error(e)
        cfg.write(open(MONGODBCONFPATH, 'w'))

    @staticmethod
    def remove_dead_replica_from_configuration_file(hostname, port):
        port = str(port)
        path = MONGODBCONFPATH + '.dead'
        cfg = configparser.ConfigParser()
        cfg.read(path)
        # Create new hostname and adding it's port
        try:
            cfg.remove_section(hostname)
        except Exception as e:
            pass#FIXME
            #self.logger.error(e)
        cfg.write(open(path, 'w'))

    @staticmethod
    def add_dead_replica_to_configuration_file(hostname, port):
        """ Add a MongoDB replica to mongodb.conf.dead file,

        :param hostname: hostname of MongoDB server
        :param port: listening port on MongoDB server
        """
        path = MONGODBCONFPATH + '.dead'
        port = str(port)
        cfg = configparser.ConfigParser()
        cfg.read(path)
        # Create new hostname and adding it's port
        # FIXME enable logger
        try:
            cfg.add_section(hostname)
            cfg.set(hostname, 'port', port)
            #self.logger.info("New replica added : " + hostname)
        # Hostname already in configuration, adding port if not already exist
        except ConfigParser.DuplicateSectionError:
            options = cfg.get(hostname, 'port').split(',')
            if port not in options:
                options.append(port)
                #self.logger.info("New replica added : " + hostname)
            cfg.set(hostname, 'port', ','.join(options))
        except Exception as e:
            pass#FIXME
            #self.logger.error(e)
        cfg.write(open(path, 'w'))