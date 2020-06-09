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
__doc__ = 'System Utils Database Toolkit'

import json
import os
import re
import subprocess
import sys
import time

import ipaddress
from mongoengine import connect
from pymongo import ReadPreference

sys.path.append("/home/vlt-gui/vulture")
os.environ['DJANGO_SETTINGS_MODULE'] = 'vulture.settings'
from django.conf import settings

from vulture_toolkit.system import ssl_utils
from vulture_toolkit.system.mongo_base import MongoBase
from vulture_toolkit.system.database_client import DataBaseClient



# Custom exceptions definitions

class ReplicaAddFailure(Exception):
    """ Add node to ReplicaSet failure Exception
    """
    def __init__(self, message):
        super(Exception, self).__init__(message)


class ReplicaConnectionFailure(Exception):
    """ Connection to ReplicaSet failure Exception
    """
    def __init__(self, message):
        super(Exception, self).__init__(message)



# Main class definition

class ReplicaSetClient(MongoBase):

    def __init__(self, *args, **kwargs):
        """Initialize connection to database

        :return:
        """
        super(ReplicaSetClient, self).__init__(*args, **kwargs)
        self.connection_uri = self.get_mongodb_connection_uri()

        self.ipv6 = False
        if kwargs:
            self.ipv6 = kwargs.get('ipv6', False)
        if not self.ipv6:
            try:
                from gui.models.system_settings import Cluster
                node = Cluster.objects.get().get_current_node()
                manag_listener = node.get_management_listener()
                try:
                    ipaddress.IPv4Address(manag_listener.ip)
                    self.ipv6 = False
                except:
                    try:
                        ipaddress.IPv6Address(manag_listener.ip)
                        self.ipv6 = True
                    except:
                        self.ipv6 = False

            except:
                self.ipv6 = False

        try:
            c = connect('vulture', host=self.connection_uri, replicaSet='Vulture',
                        ssl=True, ssl_certfile=ssl_utils.get_pem_path(),
                        ssl_ca_certs=ssl_utils.get_ca_cert_path(),
                        read_preference=ReadPreference.SECONDARY_PREFERRED
                        )

            self.logger.debug("ReplicaSet hosts are : {}".format(c.hosts))
            self.hosts = c.nodes
            self.logger.debug("Primary host is : {}".format(c.primary))
            self.primary_host = c.primary
            self.connection = c

        except Exception as e:
            if 'Port number must be an integer' in str(e):
                self.logger.warning("No configuration available")
                pass  # we need to pass, if didn't we can't create conf
            elif 'is not a member of replica set' in str(e):
                self.logger.error("Oups, this node is not a member of replicaset")
                self.logger.error("Need to do rs.add (\"<this_member>:9091\") on the PRIMARY member")
                pass
            else:
                self.logger.error("Unable to connect to the database : " + str(e))
                raise ReplicaConnectionFailure("Database connection failed, "
                                               "error: {}".format(e))

    def get_database(self, db_name):
        """ Get pymongo Database object by its name
        :param db_name  Name of the database
        :return  pymongo.database.Database
        """
        return self.connection.get_database(name=db_name)


    def get_replica_set_status(self):
        """Return status of ReplicaSet

        :return:
        """
        status = dict()
        res = self.connection.admin.command("replSetGetStatus")
        for member in res['members']:
            replica_name = member['name']
            member.pop('name', None)
            status[replica_name] = dict()
            status[replica_name] = member
        return status

    def get_replica_status(self, replica_name):
        """Return status of a replica

        :param replica_name: Name of replica
        :return: Status of replica (http://docs.mongodb.org/manual/reference/replica-states/)
        or None if we can't determine status
        """
        member_status = self.get_replica_set_status().get(replica_name)
        if member_status is not None:
            return member_status.get('stateStr')
        else:
            return None

    def promote(self, replica_name):
        """ Promote a replica_name to PRIMARY

        :param replica_host: Name of replica
        :return: response, error
        """

        port = settings.MONGODBPORT
        replica_host = "{}:{}".format(replica_name, port)

        """ Always connect to the primary to promote a secondary """
        res = self.execute_command("JSON.stringify(rs.conf())")

        """ Find the secondary node to promote and set its priority to an higher value """
        rs_reconfig="cfg=rs.conf()\n"
        i=0
        for member in res[0].get('members'):
            if member['host'] == replica_host:
                rs_reconfig=rs_reconfig+"cfg.members["+str(i)+"].priority=1\n"
            else:
                rs_reconfig=rs_reconfig+"cfg.members["+str(i)+"].priority=0.5\n"
            i=i+1
        rs_reconfig=rs_reconfig+"rs.reconfig(cfg)\n"

        """ Prepare a new configuration """
        response, error = self.execute_command(rs_reconfig)

        """ Wait 10 seconds to avoid displaying 2 SECONDARY in GUI """
        time.sleep(10)

        return response, error

    def execute_command(self, cmd, host=None, database="test"):
        """Connect to a mongodb instance using mongo client,to execute a command

        :param cmd: command to execute
        :param host: Target host, if not defined primary host is used
        :return:
        """
        if host is not None:
            hostname = host[0]
            port = str(host[1])
        else:
            hostname = self.primary_host[0]
            port = str(self.primary_host[1])

        """ Send mongo command """
        if not self.ipv6:
            params_cmd = ["/usr/local/bin/mongo", "--quiet", "--ssl",
                          "--sslPEMKeyFile", ssl_utils.get_pem_path(),
                          "--sslCAFile", ssl_utils.get_ca_cert_path(),
                          "{}:{}/{}".format(hostname, port, database),
                          "--eval", cmd]

        else:
            params_cmd = ["/usr/local/bin/mongo", "--quiet",  "--ipv6", "--ssl",
                          "--sslPEMKeyFile", ssl_utils.get_pem_path(),
                          "--sslCAFile", ssl_utils.get_ca_cert_path(),
                          "{}:{}/{}".format(hostname, port, database),
                            "--eval", cmd]

        proc    = subprocess.Popen(params_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        res     = proc.communicate()
        success = res[0]
        error   = res[1]
        if success:
            """Extracting response from entire string 
            """
            raw_response = success.replace(b"\t", b"").replace(b"\n", b"").replace(b"\r", b"")
            try:
                response = json.loads(raw_response)
            except ValueError:
                pattern = re.compile(b".*reconnected to server after rs command "
                                     b"\(which is normal\).*", re.S)
                """We can encounter an error when executing command, it's normal
                we just need to retry command"""
                if pattern.match(raw_response):
                    response, error = self.execute_command(cmd, host)#TODO Care to infinite loops
                    return response, error
                else:
                    response = None
                    self.logger.error("Unexpected error : {}".format(raw_response))
                    self.logger.error ("Command was: {}".format (cmd))
        else:
            self.logger.error(error)
        return response, error

    def add_arbiter_to_mongodb(self, arbiter_name):
        """Add an arbiter instance to ReplicaSet

        :param arbiter_name: Hostname of arbiter instance
        :return:
        """
        port = settings.MONGODBARBPORT
        replica_host = "{}:{}".format(arbiter_name, port)
        cmd = "JSON.stringify(rs.addArb('{}'))".format(replica_host)
        res = self._process_add_mongodb_instance(replica_host, cmd)
        if res:
            up_state = ('ARBITER')
            return self._check_member_state(replica_host, up_state)
        else:
            return False

    def add_replica_to_mongodb(self, replica_name):
        """ Add a replica instance to ReplicaSet

        :param replica_name: Hostname of replica instance
        :return:
        """
        port = settings.MONGODBPORT
        replica_host = "{}:{}".format(replica_name, port)
        cmd = "JSON.stringify(rs.add('{}'))".format(replica_host)
        res = self._process_add_mongodb_instance(replica_host, cmd)
        if res:
            up_state = ('PRIMARY', 'SECONDARY')
            return self._check_member_state(replica_host, up_state)
        else:
            return False

    def remove_replica_from_mongodb(self, replica_name):
        """ Remove a replica instance from ReplicaSet

        :param replica_name: Hostname of replica instance
        :return:
        """

        port = settings.MONGODBPORT
        replica_host = "{}:{}".format(replica_name, port)

        cmd = "JSON.stringify(rs.remove('{}'))".format(replica_host)
        response, error = self.execute_command(cmd)

        """ Wait 10 seconds to avoid displaying Wring information in GUI """
        time.sleep(10)

        return response, error

    def mongod_is_alive(self, replica_host):
        """Try to connect to mongod instance in order to see if mongod is
        up and running properly

        :param replica_host: replica name (ex : vulture-node1:9091)
        :return:True if replica_host is alive, False otherwise
        """
        try:
            test_connect = DataBaseClient(host=replica_host)
            if test_connect.connection.server_info():
                test_connect.connection.close()
                return True
        except Exception as e:
            self.logger.error(e)
        return False

    def _process_add_mongodb_instance(self, replica_host, cmd):
        """Internal Method used to add an instance to mongodb, instance can be
         Replica or Arbiter

        :param replica_host: replica name (ex : vulture-node1:9091)
        :param cmd: Command passed to mongoDB instance
        :return: True if replica_host was successfully added, False otherwise
        """

        # Try to connect to new replica before add it into replicaSet
        self.logger.info("Testing {} connectivity before adding it into "
                         "replicaSet".format(replica_host))
        up = self.mongod_is_alive(replica_host)
        if up:
            self.logger.info("{} is alive, we can add it into replicaSet"
                             .format(replica_host))
        else:
            self.logger.error("Unable to contact {}, please ensure host is up "
                              "and mongoDB started".format(replica_host))
            return False

        self.logger.info("Trying to add {} to replicaSet".format(replica_host))
        response, error = self.execute_command(cmd)

        if error:
            self.logger.error(error)
            return False
        else:
            err_msg = response.get('errmsg')
            down_msg = response.get('down')

            # Handle mongodb answer
            if err_msg is not None:
                self.logger.error("Unable to add {} to replicaSet, reason: {}"
                                  "".format(replica_host, err_msg))
                self.logger.error("Will try again...")
                response, error = self.execute_command(cmd)
                if error:
                    self.logger.error(error)
                    return False
                else:
                    err_msg = response.get('errmsg')
                    down_msg = response.get('down')
                    if err_msg is not None:
                        self.logger.error("Unable to add {} to replicaSet, reason: {}"
                                          "".format(replica_host, err_msg))
                        raise ReplicaAddFailure(err_msg)
                    elif down_msg is not None:
                        self.logger.warning("{} successfully added, but host seems"
                                            " to be down".format(replica_host))
                    else:
                        self.logger.info("{} successfully added to replicaSet"
                                         .format(replica_host))

            elif down_msg is not None:
                self.logger.warning("{} successfully added, but host seems"
                                    " to be down".format(replica_host))
            else:
                self.logger.info("{} successfully added to replicaSet"
                                 .format(replica_host))

            return True

    def _check_member_state(self, replica_host, up_state):
        """Inspect replicaSet state during 1 minute to determine if new
        replica_host is up and running into replicaSet,

        :param replica_host: replica name (ex : vulture-node1:9091)
        :param up_state: list of up status (PRIMARY OR SECONDARY in case of
        new replica instance, ARBITER in case of new arbiter instance)
        :return: True if up, False otherwise
        """

        timeout = time.time() + 60
        self.logger.info("Checking status for host {}".format(replica_host))
        while True:
            status = self.get_replica_status(replica_host)
            if status in up_state:
                self.logger.info("{} is now up in replicaSet, status : {}"
                                 .format(replica_host, status))
                return True
            elif time.time() > timeout:
                self.logger.error("Unable to see {} up, status : {}"
                                  .format(replica_host, status))
                return False
            time.sleep(5)
            self.logger.debug(status)

    def monitor_replica_set(self):
        """ Method in charge to monitor ReplicaSet status. It look if
        cluster got a primary Replica. If not, it try to fix it by
        reconfiguring ReplicaSet

        :return:
        """
        # Looking Cluster state, ie if we have a primary host
        primary = self.connection.primary
        if primary is None:
            self.logger.error("Missing primary in replicaset, trying to recover")
            self._recover_replica_set()
        # Looking if we need to reintegrate replica member
        else:
            dead_host = self.get_mongodb_dead_hosts()
            for host in dead_host:
                # Checking if host is now up
                if self.mongod_is_alive(host):
                    hostname, port = host
                    self.add_replica_to_mongodb(hostname)
                    self.add_replica_to_configuration_file(hostname, port)
                    self.remove_dead_replica_from_configuration_file(hostname, port)

    def _recover_replica_set(self):
        """If a majority of replica aren't up, replicaSet can be in unstable
        state without primary replica. This function is used to reconfigure
        replica set

        :return:
        """
        dead_hosts = self.get_hosts_by_type('DEAD')
        up_hosts = self.get_hosts_by_type('UP')
        if len(up_hosts) > 0:
            cmd = "JSON.stringify(rs.conf())"
            response, error = self.execute_command(cmd, up_hosts[0])
            if error:
                self.logger.error(error)
                return False
            else:
                # Identify dead host and delete them from replicaSet conf
                for member in list(response['members']):
                    hostname, port = member['host'].split(':')
                    exist = [host for host in dead_hosts if '{}:{}'.format(host[0], host[1]) == member['host']]
                    if len(exist) > 0:
                        response['members'].remove(member)
                        self.remove_replica_from_configuration_file(hostname, port)
                        self.add_dead_replica_to_configuration_file(hostname, port)
                self._reconfigure_replica_set(response)

    def _reconfigure_replica_set(self, conf):
        """Launch an rs.reconfig operation on replicaset

        :param conf: configuration of replicaSet
        :return:
        """
        up_hosts = self.get_hosts_by_type('UP')
        cmd = "JSON.stringify(rs.reconfig(%s, {force : true}))" % (json.dumps(conf))
        self.logger.debug("Trying to reconfigure replicaset with: {}".format(conf))
        success, error = self.execute_command(cmd, up_hosts[0])
        if error:
            self.logger.error("An error has occured during ReplicaSet"
                              "reconfiguration, error: {}".format(error))
