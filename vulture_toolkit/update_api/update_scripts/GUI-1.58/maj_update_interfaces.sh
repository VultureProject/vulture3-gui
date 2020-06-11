#!/bin/sh
#
# This migration script write new update_interface script
#  in /home/vlt-sys/scripts directory
#

script="/home/vlt-sys/scripts/update_interface"

/bin/echo -n "[+] Writing $script ..."

/bin/echo "#!/usr/bin/env /home/vlt-gui/env/bin/python2.7
# coding:utf-8

\"\"\"This file is part of Vulture 3.

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
\"\"\"
__author__ = \"Jérémie JOURDIN, Kevin Guillemot\"
__credits__ = []
__license__ = \"GPLv3\"
__version__ = \"3.0.0\"
__maintainer__ = \"Vulture Project\"
__email__ = \"contact@vultureproject.org\"
__doc__ = \"\"\"Script used to insert network interface into MongoDB\"\"\"


import os
import sys

sys.path.append('/home/vlt-gui/vulture')
os.environ.setdefault(\"DJANGO_SETTINGS_MODULE\", 'vulture.settings')

import django
django.setup()

from gui.models.network_settings import Interface, Listener
from gui.models.system_settings import Cluster, Node
from vulture_toolkit.network import net_utils
from vulture_toolkit.network.interface import Interface as InterfaceHelper


if __name__ == '__main__':

    cluster = Cluster.objects.get()
    node = cluster.get_current_node()

    # Insertion of information relative to network interfaces
    device_lst = net_utils.get_devices()
    is_gui_defined = False
    for device in device_lst:
        if device == \"lo0\":
            continue
        print \"Interface '{}' found.\".format(device)
        try:
            db_intf = Interface.objects.get(device=device, alias='if_' + device)
            print \"Interface {} already exists.\".format(device)
            continue
        except Interface.DoesNotExist:
            db_intf = Interface(device=device, alias='if_' + device)
        except Interface.MultipleObjectsReturned:
            continue
        intf = InterfaceHelper(device)
        for index, inet in enumerate(intf.inet_list):
            try:
                listener = Listener.objects.filter(ip=inet.str_ip_address,
                                                   prefixlen=inet.netmask,
                                                   version=str(inet.ip_address.version),
                                                   is_physical=True)
                print \"IP address {}/{} ({}) already exists.\".format(listener.ip,
                                                                     listener.prefixlen,
                                                                     listener.version)
                continue
            except Listener.DoesNotExist:
                pass
            listener = Listener()
            listener.ip = inet.str_ip_address
            listener.prefixlen = inet.netmask
            listener.version = str(inet.ip_address.version)
            listener.is_physical = True

            listener.save(bootstrap=True)
            print \"IP address {} inserted.\".format(listener.ip)
            db_intf.inet_addresses.append(listener)
        db_intf.save()
        print \"Interface {} inserted.\".format(device)
        node.interfaces.append(db_intf)
    node.save(bootstrap=True)
" > "$script"

/bin/chmod 550 "$script"
/usr/sbin/chown vlt-sys:vlt-sys "$script"

/bin/echo "OK"
