#!/bin/sh
#
# This migration script update /home/vlt-sys/scripts/vulture_apps_starter
#
#

script_filename="/home/vlt-sys/scripts/vulture_apps_starter"

/bin/echo -n "[+] Updating file $script_filename ..."

/bin/echo "#!/usr/bin/env /home/vlt-gui/env/bin/python2.7
# -*- coding: utf-8 -*-
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
__author__ = \"Florian Hagniel\"
__credits__ = []
__license__ = \"GPLv3\"
__version__ = \"3.0.0\"
__maintainer__ = \"Vulture Project\"
__email__ = \"contact@vultureproject.org\"
__doc__ = ''

import sys
import os
import time

# Django setup part
sys.path.append(\"/home/vlt-gui/vulture/\")
os.environ.setdefault(\"DJANGO_SETTINGS_MODULE\", 'vulture.settings')


# Check initial call
if len(sys.argv) != 2:
    sys.exit(1)
else:
    cmd = sys.argv[1]

import django
django.setup()

from gui.models.system_settings import Cluster


def start_applications(node):
    done = []
    for listen_address in node.get_listen_addresses():
        token = node.name + listen_address.address.ip + str(listen_address.port)
        if token not in done:
            status = listen_address.start()
            done.append(token)
            if status.get('status') == True:
                print \"Listener {}:{} successfully started\".format(listen_address.address.ip, listen_address.port)
            else:
                print \"Unable to start listener {}:{}, errors: {}\".format(listen_address.address.ip, listen_address.port, status)


def stop_applications(node):
    done = []
    for listen_address in node.get_listen_addresses():
        token = node.name + listen_address.address.ip + str(listen_address.port)
        if token not in done:
            status = listen_address.stop()
            done.append(token)
            if status.get('status') == True:
                print \"Listener {}:{} successfully stopped\".format(listen_address.address.ip, listen_address.port)
            else:
                print \"Unable to stop listener {}:{}, errors: {}\".format(listen_address.address.ip, listen_address.port, status)


def reload_applications(node):
    done = []
    for listen_address in node.get_listen_addresses():
        token = node.name + listen_address.address.ip + str(listen_address.port)
        if token not in done:
            done.append(token)
            status = listen_address.graceful()
            if status.get('status') == True:
                print \"Listener {}:{} successfully reload\".format(listen_address.address.ip, listen_address.port)
            else:
                print \"Unable to graceful listener {}:{}, errors: {}\".format(listen_address.address.ip, listen_address.port, status)


cluster = Cluster.objects.get()
node = cluster.get_current_node()

timeout = time.time() + 60
while True:
    time.sleep(1)
    if node.is_up():
        if cmd == 'start':
            start_applications(node)
            sys.exit(0)
        elif cmd == 'stop':
            stop_applications(node)
            sys.exit(0)
        elif cmd == 'restart':
            stop_applications(node)
            start_applications(node)
            sys.exit(0)
        elif cmd == 'reload':
            reload_applications(node)
            sys.exit(0)
        else:
            print \"{} : Unknown command\".format(cmd)
            sys.exit(2)
    elif time.time() > timeout:
        print \"Unable to start Vulture apps\"
        sys.exit(3)
" > "$script_filename"

/bin/echo "OK"
