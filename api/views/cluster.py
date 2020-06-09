from __future__ import unicode_literals
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
__doc__ = 'Django views dedicated to Vulture Cluster API'

import json
import ipaddress
from bson.objectid import ObjectId

from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseForbidden, JsonResponse
from mongoengine.queryset import DoesNotExist

from gui.models.system_settings import Cluster, Node
from vulture_toolkit.network import net_utils
from vulture_toolkit.system.replica_set_client import ReplicaSetClient, ReplicaAddFailure, ReplicaConnectionFailure
from vulture_toolkit.update_api.update_utils import UpdateUtils, UpdateAPIError
from vulture_toolkit.system import rc_conf
from vulture_toolkit.system import krb5_conf
from gui.models.template_settings import portalTemplate

# Logger configuration
import logging
import logging.config


logger = logging.getLogger('cluster')

@csrf_exempt
def node_configuration(request):
    """Return Node Certificate for node which are joining cluster

    :param request:
    :return:
    """
    # Retrieving POST data
    try:
        raw_data = request.POST.get('data')
        data = json.loads(raw_data)
        node_name = data['nodename']
    except TypeError as e:
        logger.error("Bad request, POST data are malformed. POST "
                     "data : " + str(request.POST))
        return HttpResponseForbidden()
    except ValueError as e:
        logger.error("Bad request, JSON string is malformed : " + raw_data)
        return HttpResponseForbidden()
    except Exception as e:
        logger.error("Unexpected error")
        logger.exception(e)

    # Secret verification
    cluster = Cluster.objects.get()
    temporary_secret = data.get('secret')
    response = {}
    error_msg = "Unable to join cluster, reason: {}"
    # Try to retrieve Node configuration, if it was already created
    if net_utils.is_valid_hostname(node_name):
        try:
            node = Node.objects.get(name=node_name,
                                    temporary_key=temporary_secret)
            logger.info("Successfull secret verification for node : " + node_name)
            # Retrieving certificates
            client_cert = node.certificate.as_pem(cert=True, key=False)
            client_key = node.certificate.as_pem(cert=False, key=True)
            ca_cert = cluster.ca_certificate.as_pem(cert=True)
            response['status'] = True
            response['client_cert'] = {
                'cert': client_cert,
                'key': client_key
            }
            response['ca_cert'] = ca_cert
            response['email'] = UpdateUtils.get_api_email()
            return JsonResponse(response)
        except DoesNotExist as e:
            error = error_msg.format("Node doesn't exist in database or temporary "
                                     "key is invalid")
            logger.error(error)
        except UpdateAPIError as e:
            error = error_msg.format(e)
            logger.error(error)
        except Exception as e:
            error = error_msg.format(e)
            logger.error(e)
            logger.exception(e)
    else:
        error = error_msg.format("Not a valid hostname")
    response['status'] = False
    response['err_msg'] = error
    return HttpResponseForbidden(json.dumps(response),
                                 content_type="application/json")


@csrf_exempt
def node_initialization(request):
    """ Initialize node into Cluster, during this phase Node is added to mongoDB
    replicaSet

    :param request:
    :return:
    """
    # Retrieving POST data
    try:
        raw_data        = request.POST.get('data')
        data            = json.loads(raw_data)
        node_name       = data.get('nodename')
        default_ipv4_gw = data.get('default_ipv4_gw')
        default_ipv6_gw = data.get('default_ipv6_gw')
        ip_address      = data.get('ip_address')

        try:
            ipaddress.IPv4Address(ip_address)
            ipv6 = False
        except:
            try:
                ipaddress.IPv6Address(ip_address)
                ipv6 = True
            except:
                return JsonResponse({
                    'status': False,
                    'error': 'IP address not an IPv4 or IPv6 address'
                })

    except TypeError as e:
        logger.error("Bad request, POST data are malformed. POST "
                     "data : " + str(request.POST))
        return HttpResponseForbidden()
    except ValueError as e:
        logger.error("Bad request, JSON string is malformed : " + raw_data)
        return HttpResponseForbidden()
    except Exception as e:
        logger.exception(e)
        return HttpResponseForbidden()

    response = dict()

    # Check if Node exist
    if net_utils.is_valid_hostname(node_name):
        db_node = Node.objects.get(name=node_name)
        logger.info("Good Node name, we can add it into MongoDB replicaSet if"
                    " it doesn't already exist")
        mongodb_port = 9091
        node = node_name, mongodb_port
        # Adding hostname into /etc/hosts if it is not resolvable
        if not net_utils.is_resolvable_hostname(node_name):
            net_utils.make_hostname_resolvable(node_name, ip_address)
        # Add Node into replicaSet
        try:
            replica_set = ReplicaSetClient(ipv6=ipv6)
            if node not in replica_set.hosts:
                logger.info("Node {}:{} doesn't appear in replicaSet, we can add it"
                            .format(node_name, mongodb_port))
                # Contacting Primary MongoDB replica to add new replica
                added = replica_set.add_replica_to_mongodb(node_name)
                if added:
                    logger.info("Node {}:{} successfully added in replicaSet"
                                .format(node_name, mongodb_port))
                    response['status'] = True
                    db_node.temporary_key = ''
                    db_node.default_ipv4_gw = default_ipv4_gw
                    db_node.default_ipv6_gw = default_ipv6_gw
                    db_node.save(bootstrap=True)

                    """ Update cluster to add this new node in mongodb.conf """
                    cluster = Cluster.objects.get()
                    cluster.api_request("/api/cluster/replica/update/", exclude=node_name)
            else:
                err_msg = "Node already exist in replicaSet"
                logger.info(err_msg)
                response['status'] = False
                response['err_msg'] = err_msg

        except DoesNotExist as e:
            err_msg = "Node doesn't exist in database, please add it before " \
                      "try to join cluster"
            response['status'] = False
            response['err_msg'] = err_msg
            logger.error(err_msg)
        except ReplicaConnectionFailure as e:
            response['status'] = False
            response['err_msg'] = str(e)
            logger.error("Unable to add node {}:{} to replicaSet, database "
                         "connection failed".format(node_name, mongodb_port))
        except ReplicaAddFailure as e:
            response['status'] = False
            response['err_msg'] = str(e)
            logger.error("Unable to add node {}:{} to replicaSet, please check"
                        " mongodb_event.log for additional information"
                        .format(node_name, mongodb_port))
        except Exception as e:
            response['status'] = False
            response['err_msg'] = str(e)
            logger.error("Unable to add node {}:{} to replicaSet, error: {}"
            .format(node_name, mongodb_port, e))
    else:
        logger.warning("Nodename provided is not a valid hostname, nodename: {}"
                       "".format(node_name))
        return HttpResponseForbidden()

    return JsonResponse(response)


def update_replicalist(request):
    """API call used to update mongodb.conf file, this file contain hostname:port
    of replicaSet members

    :return:
    """
    error_msg = "An error occurred during update of configuration file, " \
                 "error: {}"
    try:
        logger.info("Starting update of mongodb.conf")

        #30sec is refreshing time of pymongo replicaSet monitor
        #time.sleep(30)

        replica_set = ReplicaSetClient()
        replica_hosts = replica_set.hosts
        logger.debug("ReplicaSet hosts are: {}".format(replica_hosts))  # TODO Use another logger ??
        for replica in replica_hosts:
            hostname = replica[0]
            port = replica[1]
            # Adding hostname into /etc/hosts if it is not resolvable
            if not net_utils.is_resolvable_hostname(hostname):
                node = Node.objects.get(name=hostname)
                ip_address = node.get_management_listener().ip
                net_utils.make_hostname_resolvable(hostname, ip_address)
            ReplicaSetClient.add_replica_to_configuration_file(hostname, port)
        logger.info("mongodb.conf successfully updated")

        results = {
            'status': True
        }
        return JsonResponse(results)

        #return HttpResponse() # TODO OK response ???

    except ReplicaConnectionFailure as e:
        error_msg = error_msg.format(e)
        logger.error(error_msg)
    except Exception as e:
        error_msg = error_msg.format(e)
        logger.error(error_msg)
        logger.exception(e)
    return HttpResponseForbidden()


def refresh_rc_conf(request):
    """ Check if rc.conf.local has changed. Rewrite it if any change is detected

    :param request: Django request object
    :return:
    """
    try:
        results = {'changed': rc_conf.check_status()}
    except Exception as e:
        results = {'error': str(e)}
        logger.error("An error as occurred during rc.conf.local check")
        logger.exception(e)

    return JsonResponse(results)


def refresh_krb5_conf(request):
    """ Check if krb5.conf has changed. Rewrite it if any change is detected
    :param request: Django request object
    :return:
    """
    try:
        results = {'changed': krb5_conf.check_status()}
    except Exception as e:
        results = {'error': str(e)}
        logger.error("An error as occurred during krb5.conf check")
        logger.exception(e)
    return JsonResponse(results)


def refresh_portal_template_conf(request, template_id=None):
    """
    Write the templates on disk
    :param request: Django request object
    :return:
    """
    if not template_id:
        response = {'error': "Wrong template id."}
        return JsonResponse(response)

    try:
        template = portalTemplate.objects.with_id(ObjectId(template_id))
        if not template:
            raise Exception("Unable to find template in internal database")
        template.write_on_disk()
        response = {'changed': True}
    except Exception as e:
        response = {'error': str(e)}

    return JsonResponse(response)


def node_status(request):
    """ Method used to determine if Node is up.

    :param request:
    :return: Always a dict with 'status': True
    """
    results = {
        'status': True
    }
    return JsonResponse(results)


def node_version(request):
    from vulture_toolkit.update_api.gui_updater import GUIUpdater
    from vulture_toolkit.update_api.engine_updater import EngineUpdater
    gui_updater = GUIUpdater()
    engine_updater = EngineUpdater()
    result = {'gui-version': gui_updater.current_version, 'engine-version': engine_updater.current_version}
    return JsonResponse(result)


def node_upgrade(request, update_type):
    import subprocess

    try:
        subprocess.Popen(['/usr/local/bin/sudo', '-u', 'vlt-sys', '/usr/local/bin/sudo',
                                 '/home/vlt-sys/scripts/install_updates',
                                 update_type])
    except Exception as e:
        logger.exception(e)

    """
    from vulture_toolkit.update_api.update_utils import UpdateUtils
    node = Cluster.objects.get().get_current_node()
    version = getattr(node.version, "{}_last_version".format(update_type))
    updater = UpdateUtils.get_updater(update_type)
    try:
        status = updater.install(version)
    except Exception as e:
        logger.error("An error as occurred during installation of {}".format(version))
        logger.exception(e)
        status = False
    if status:
        setattr(node.version, '{}_version'.format(update_type), updater.current_version)
        node.save()
    """
    return JsonResponse({})
