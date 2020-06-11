#!/home/vlt-gui/env/bin/python2.7
# coding:utf-8

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
__author__     = "Hugo Soszynski"
__credits__    = []
__license__    = "GPLv3"
__version__    = "3.0.0"
__maintainer__ = "Vulture Project"
__email__      = "contact@vultureproject.org"
__doc__        = """This migration script get the default gateway from config file"""

import os
import sys

sys.path.append('/home/vlt-gui/vulture')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", 'vulture.settings')

import django
django.setup()

from gui.models.system_settings import Cluster
from vulture_toolkit.system.replica_set_client import ReplicaSetClient
from vulture_toolkit.system.redis_svc import RedisSvc
from vulture_toolkit.network.interface import Interface as InterfaceHelper
from vulture_toolkit.network import net_utils


if __name__ == '__main__':

    cluster = Cluster.objects.get()
    current_node = cluster.get_current_node()

    """ Fixing the /etc/hosts with right ip for the machine hostname """
    with open('/etc/hosts', 'r') as f:
        content = f.read()

    hostname = net_utils.get_hostname()
    device_lst = net_utils.get_devices()
    is_gui_defined = False
    for device in device_lst:
        intf = InterfaceHelper(device)
        for index, inet in enumerate(intf.inet_list):
            if device != 'lo0' and not is_gui_defined:
                ip = inet.str_ip_address

    pattern = '127.0.0.1 ' + str(hostname)
    replacement = str(ip) + ' ' + str(hostname)

    content = content.replace(pattern, replacement)

    with open('/etc/hosts', 'w') as f:
        f.write(content)

    """ Fixing the redis cluster """
    replica_set = ReplicaSetClient()
    service = RedisSvc()

    primary_ip = ''

    status = replica_set.get_replica_status(current_node.name + ':9091')

    if status == 'PRIMARY':
        service.create_master_conf()
        service.restart_service()

    elif status == 'SECONDARY':
        for node in cluster.members:
            status = replica_set.get_replica_status(node.name + ':9091')
            if status == 'PRIMARY':
                primary_ip = node.name

        service.create_slave_conf(primary_ip)
        service.restart_service()
