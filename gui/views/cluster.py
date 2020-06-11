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
__doc__ = 'Django views dedicated to Vulture GUI Cluster page'


# Django system imports
from django.conf import settings
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.crypto import get_random_string

# Django project imports
from gui.decorators import group_required
from gui.forms.system_settings import NodeForm, NewNodeForm
from gui.models.system_settings import Cluster, Node
from vulture_toolkit.system.replica_set_client import ReplicaSetClient

# Extern modules imports
from bson.objectid import ObjectId
from json import loads as json_loads
from redis import Redis
from time import sleep

# Logger configuration imports
import logging
logging.config.dictConfig(settings.LOG_SETTINGS)
logger = logging.getLogger('debug')


@group_required('administrator', 'system_manager')
def general_settings(request):
    """ View dedicated to cluster's general settings 
        :param request: Django request object
    """

    """ Get the status of the MongoDB replica SET """
    replica_set = ReplicaSetClient()

    """ Retrieving cluster configuration """
    cluster = Cluster.objects.get()
    node_list = list()
    for node in cluster.members:

        """ Ignore dead nodes and pending nodes"""
        if node.is_dead:
            node.gui_version = 'Unknown'
            node.engine_version = 'Unknown'
        elif not node.temporary_key:
            v = node.api_request("/api/cluster/node/version/")
            try:
                node.gui_version = v['gui-version']
                node.engine_version = v['engine-version']
            except:
                node.gui_version = "Unknown"
                node.engine_version = "Unknown"
        else:
            node.gui_version = 'Unknown'
            node.engine_version = 'Unknown'

        rs_node = node.name, 9091
        if rs_node in replica_set.hosts:
            node.member_of_replicaset = True
        else:
            node.member_of_replicaset = False

        node.status = replica_set.get_replica_status(node.name+':9091')

        """ Get the Redis Cluster status """
        if node.temporary_key:
            node.member_of_redis_cluster = False
            node.redis_status = None
        else:
            try:
                redis_session = Redis(host=node.name, port=settings.REDISPORT, db=0, socket_timeout=5)
                #redis_session = redis.Redis(unix_socket_path='/var/db/redis/redis.sock', db=0)

                res = redis_session.execute_command('ROLE')

                if b"master" in res:
                    node.member_of_redis_cluster = True
                    node.redis_status = 'MASTER'
                elif b"slave" in res:
                    if b"connected" in res:
                        node.member_of_redis_cluster = True
                    else:
                        node.member_of_redis_cluster = False
                    node.redis_status = 'SLAVE'
                else:
                    if b"connected" in res:
                        node.member_of_redis_cluster = True
                    else:
                        node.member_of_redis_cluster = False
                    node.redis_status = 'UNKNOWN (Error)'

            except:
                logger.error("Can't connect to Node's {} Redis Server".format(node.name))

        node_list.append(node)
    return render_to_response('cluster.html',
                              {'node_list': node_list},
                              context_instance=RequestContext(request))


@group_required('administrator', 'system_manager')
def redis_promote(request, object_id=None):
    """ View dedicated to promote a secondary node to primary node inside a Redis cluster

    :param object_id: MongoDB object_id of target Node
    :param request: Django request object
    """
    if not object_id:
        logger.error("Node object_id is None")
        return HttpResponseRedirect('/cluster/')

    node = Node.objects.with_id(ObjectId(object_id))
    if node is None:
        logger.error("Node not found")
        return HttpResponseRedirect('/cluster/')

    try:
        redis_session = Redis(host=node.name, port=settings.SENTINELPORT, db=0, socket_timeout=5)
        redis_session.execute_command('SENTINEL failover mymaster')
        # Sleep 15 seconds to let time for sentinels to sync
        sleep(15)
    except Exception as e:
        logger.error("Unable to promote node {} as MASTER, error: {}".format(node.name, e))

    return HttpResponseRedirect('/cluster/')


@group_required('administrator', 'system_manager')
def promote(request, object_id=None):
    """ View dedicated to promote a secondary node to primary node inside a replicaSet

    :param object_id: MongoDB object_id of target Node
    :param request: Django request object
    """
    if not object_id:
        logger.error("Node object_id is None")
        return HttpResponseRedirect('/cluster/')

    node = Node.objects.with_id(ObjectId(object_id))
    if node is None:
        logger.error("Node not found")
        return HttpResponseRedirect('/cluster/')

    try:
        replica_set = ReplicaSetClient()
        replica_set.promote(node.name)
    except Exception as e:
        logger.exception(e)
        logger.error("Unable to promote node {} as PRIMARY, error: {}".format(node.name, e))

    return HttpResponseRedirect('/cluster/')


@group_required('administrator', 'system_manager')
def remove(request, object_id=None):
    """ View dedicated to remove a secondary node from a replicaSet

    :param object_id: MongoDB object_id of target Node
    :param request: Django request object
    """

    if not object_id:
        logger.error("Node object_id is None")
        return HttpResponseRedirect('/cluster/')

    node = Node.objects.with_id(ObjectId(object_id))
    if node is None:
        logger.error("Node not found")
        return HttpResponseRedirect('/cluster/')
    try:
        replica_set = ReplicaSetClient()
        replica_set.remove_replica_from_mongodb (node.name)
    except Exception as e:
        logger.error("Unable to remove node {} from replicaSet, error: {}".format(node.name, e))

    logger.info ("Node {} has been removed from replicatSet".format(node.name))
    return HttpResponseRedirect('/cluster/')


@group_required('administrator', 'system_manager')
def join(request, object_id=None):
    """ View dedicated to add a secondary node in a replicaSet

    :param object_id: MongoDB object_id of target Node
    :param request: Django request object
    """

    if not object_id:
        logger.error("Node object_id is None")
        return HttpResponseRedirect('/cluster/')

    node = Node.objects.with_id(ObjectId(object_id))
    if node is None:
        logger.error("Node not found")
        return HttpResponseRedirect('/cluster/')

    try:
        replica_set = ReplicaSetClient()
        replica_set.add_replica_to_mongodb (node.name)
        logger.info ("Node {} has been added from replicatSet".format(node.name))
    except Exception as e:
        logger.error("Unable to add node {} to replicaSet, error: {}".format(node.name, e))

    return HttpResponseRedirect('/cluster/')


@group_required('administrator', 'system_manager')
def edit(request, object_id=None):
    """ View dedicated to node management 

    :param object_id: MongoDB object_id of target Node
    :param request: Django request object
    """

    """ Retrieving cluster configuration and creating node_form object """
    cluster = Cluster.objects.get()
    node = Node.objects.with_id(ObjectId(object_id))

    if object_id:
        node_form = NodeForm(request.POST or None, instance=node)
    else:
        node_form = NewNodeForm(request.POST or None)

    """ Saving information into database and redirect to management page """
    if request.method == 'POST' and node_form.is_valid():
        node = node_form.save(commit=False)

        """ Transform \r\n to \n in static_route """
        node.static_route=node.static_route.replace("\r\n","\n")


        if node not in cluster.members:
            temporary_key = get_random_string(8)
            node.temporary_key = temporary_key
            node.create_certificate()
            cluster.members.append(node)
            cluster.save()
            node.save(bootstrap=True)
        else:
            node.save()

        return HttpResponseRedirect('/cluster/')

    return render_to_response('cluster_edit.html',
                              {'node_form': node_form, 'object_id': object_id,
                               'node': node},
                              context_instance=RequestContext(request))


@group_required('administrator', 'system_manager')
def update(request):
    """ View dedicated to update management

    :param request: Django request object
    :return:
    """
    cluster = Cluster.objects.get()
    nodes = cluster.members

    return render_to_response('cluster_update.html',
                              {'nodes': nodes},
                              context_instance=RequestContext(request))


@group_required('administrator', 'system_manager')
def launch_update(request, object_id, update_type):
    node = Node.objects.with_id(ObjectId(object_id))
    api_url = '/api/cluster/update/{}/'.format(update_type)
    res = node.api_request(api_url)
    return JsonResponse(res)


@group_required('administrator', 'system_manager')
def need_update(request):
    cluster = Cluster.objects.get()
    result = {'need_update':  False}
    for node in cluster.members:

        """ BETA-0.2 For some reason, if Node is not properly bootstraped, node.version is Null
            This should be fixed with good bootstraping and node registration
        """

        if node.version and node.version.need_update:
            result['need_update'] = True
            break

    return JsonResponse(result)


@group_required('administrator', 'system_manager')
def check_vulns(request):
    cluster = Cluster.objects.get()
    result = {'need_update': False}

    for node in cluster.members:
        try:
            if node.vulns.need_update:
                result['need_update']   = True
                result['global_vulns']  = node.vulns.global_vulns or ""
                result['kernel_vulns']  = node.vulns.kernel_vulns or ""
                result['distrib_vulns'] = node.vulns.distrib_vulns or ""
                break
            else:
                result['need_update']   = False
                result['global_vulns']  = ""
                result['kernel_vulns']  = ""
                result['distrib_vulns'] = ""
        except:
            pass
    return JsonResponse(result)


@group_required('administrator', 'system_manager')
def get_vulns(request, object_id=None):
    result = {'need_update': False}

    if object_id == None:
        logger.error("Cannot retrieve vulnerabilities infos of node id 'None'")
        return JsonResponse(result)

    cluster = Cluster.objects.get()
    node = Node.objects.with_id(ObjectId(object_id))

    try:
        if node.vulns.need_update:
            result['need_update']  = True
            result['global_vulns']  = node.vulns.global_vulns_verbose or ""
            result['kernel_vulns']  = node.vulns.kernel_vulns_verbose or ""
            result['distrib_vulns'] = node.vulns.distrib_vulns_verbose or ""
        else:
            result['need_update']   = False
            result['global_vulns']  = ""
            result['kernel_vulns']  = ""
            result['distrib_vulns'] = ""
    except:
        pass

    return JsonResponse(result)


@group_required('administrator', 'system_manager')
def check_diagnostic(request):
    """
    Check if everything is ok in the diagnostic of each node
    :param request: The request (thanks captain obvious)
    :return: A Json containing the status of each node
    """

    cluster  = Cluster.objects.get()
    nodes    = cluster.members
    response = {}

    for node in nodes:
        try:
            node_status = json_loads(node.diagnostic)
            response[node.name] = node_status['global_status']
        except:
            response[node.name] = True

    return JsonResponse(response)
