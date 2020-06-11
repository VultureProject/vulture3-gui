import datetime
import os
import sys

import django
import redis

from testing.core.testing_module import TestingModule

sys.path.append('/home/vlt-gui/vulture')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", 'vulture.settings')
django.setup()

from gui.models.system_settings import Cluster
from portal.system.redis_sessions import REDISBase
from vulture_toolkit.system.replica_set_client import ReplicaSetClient
from django.conf import settings


class Module(TestingModule):

    def __init__(self):
        super(Module, self).__init__()
        self.log_level = 'warning'

    def __str__(self):
        return "Cluster Interconnection"

    @staticmethod
    def nodes_connection():
        """
        Send an API request to each node to check the status of the cluster
        """
        cluster = Cluster.objects.get()
        members = cluster.members

        dead_nodes = []
        for node in members:
            if not node.temporary_key:
                try:
                    response = node.api_request("/api/cluster/node/status/")
                    if not response:
                        dead_nodes.append(node.name)
                except:
                    dead_nodes.append(node.name)

        assert (not dead_nodes), "Unable to contact the api for the following nodes: {}".format(dead_nodes)

    @staticmethod
    def redis_node_connect():
        """
        Try to connect to the redis server on each node
        """
        cluster = Cluster.objects.get()
        members = cluster.members

        dead_nodes = []
        for node in members:
            if not node.temporary_key:
                try:
                    redis_session = redis.Redis(host=node.name, port=settings.REDISPORT, db=0, socket_timeout=5)
                    res = redis_session.execute_command('PING')
                    if not res:
                        dead_nodes.append(node.name)
                except:
                    dead_nodes.append(node.name)

        assert (not dead_nodes), "Unable to connect to the Redis server for the following nodes: {}".format(dead_nodes)

    @staticmethod
    def redis_cluster_write():
        """
        Try to connect to the cluster's redis MASTER node and create /delete a key
        """

        r=REDISBase()
        assert (r), "Unable to connect to the Redis master node"
        s=r.set("test","test")
        assert (s), "Unable to create a key on the Redis master node"
        s=r.delete("test")
        assert (s), "Unable to delete key on the Redis master node"

    @staticmethod
    def redis_sentinel_connect():
        """
        Try to connect to the sentinel server on each node
        """
        cluster = Cluster.objects.get()
        members = cluster.members

        dead_nodes = []
        for node in members:
            if not node.temporary_key:
                try:
                    redis_session = redis.Redis(host=node.name, port=settings.SENTINELPORT, db=0, socket_timeout=5)
                    res = redis_session.execute_command('PING')
                    if not res:
                        dead_nodes.append(node.name)
                except:
                    dead_nodes.append(node.name)

        assert (not dead_nodes), "Unable to connect to the Sentinel server for the following nodes: {}".format(dead_nodes)

    @staticmethod
    def mongo_replicaset_connect():
        """
        Try to connect to the MongoDB ReplicaSet member of each node
        """
        replica_set = ReplicaSetClient()
        cluster = Cluster.objects.get()
        members = cluster.members

        dead_nodes = []
        for node in members:
            if not node.temporary_key:
                try:
                    status = replica_set.get_replica_status(node.name + ':9091')
                    if not status:
                        dead_nodes.append(node.name)
                except:
                    dead_nodes.append(node.name)

        assert (not dead_nodes), "Unable to connect to the MongoDB replica of the following nodes: {}".format(dead_nodes)

    @staticmethod
    def nodes_ntp_sync():
        """
        Make an API request to get the current time of each node.
        """
        cluster = Cluster.objects.get()
        nodes = cluster.members

        not_sync_nodes = []
        for node in nodes:
            if not node.temporary_key:
                try:
                    response = node.api_request('/api/supervision/system_time/')
                    if response['status']:
                        now = datetime.datetime.now()
                        tdelta = now - datetime.datetime.strptime(response['time'], "%Y-%m-%dT%H:%M:%SZ")
                        if tdelta.total_seconds() > 300 or tdelta.total_seconds() < datetime.timedelta(seconds=-300).total_seconds():
                            not_sync_nodes.append(node.name)
                except:
                    pass

        assert (not not_sync_nodes), "The system time difference with the following nodes is higher than 5 min: {}".format(not_sync_nodes)
