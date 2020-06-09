#!/bin/sh
#
# This migration script update to Python3 the scripts in /home/vlt-sys/scripts/
#

# If this script is not ran as root
if [ $(/usr/bin/whoami) != "root" ]; then
    # Echo error message in stderr
    /bin/echo "[/] This script must be run as root" >&2
fi

/bin/echo -n "[+] Updating /home/vlt-sys/scripts/add_to_etc_hosts ..."

/bin/echo "#!/usr/bin/env /home/vlt-gui/env/bin/python
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
import re
import ipaddress

nb_args = len(sys.argv)
if nb_args == 3:
    hostname = sys.argv[1]
    ip = sys.argv[2]
    # Testing IP Address validity
    try:
        ipaddress.ip_address(unicode(ip))
    except Exception as e:
        print(\"INCORRECT IP\", file=sys.stderr)
        sys.exit(2)
    # Testing hostname validity
    pattern = \"^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$\"
    reg = re.compile(pattern)
    if not reg.match(hostname):
        print(\"INCORRECT HOSTNAME\", file=sys.stderr)
        sys.exit(2)
    #Inputs are good, we can process them
    f = open(\"/etc/hosts\", 'r')
    content = f.read()
    f.close()
    #Looking if host already exist, if yes we replace its ip address
    pattern = re.compile(\"^[a-z0-9:\.]+\s+{}$\".format(hostname), re.M)
    if pattern.search(content):
        content = pattern.sub(\"{}\t{}\".format(ip, hostname), content)
    #Host doesnt exist, we add it
    else:
        content += \"\n{}\t{}\n\".format(ip, hostname)
    #Writing result into /etc/hosts
    f = open('/etc/hosts', 'w')
    f.write(content)
    f.close()
    print(\"Host successfully added\")
    sys.exit(0)
else:
    print(\"ARGS ERROR\", file=sys.stderr)
    sys.exit(2)
" > /home/vlt-sys/scripts/add_to_etc_hosts

/bin/echo "OK"
/bin/echo -n "[+] Updating /home/vlt-sys/scripts/check_updates.hour ..."

/bin/echo "#!/usr/bin/env /home/vlt-gui/env/bin/python
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

# Django setup part
sys.path.append(\"/home/vlt-gui/vulture/\")
os.environ.setdefault(\"DJANGO_SETTINGS_MODULE\", 'vulture.settings')

import django
django.setup()
import logging
logger = logging.getLogger('cluster')

from vulture_toolkit.update_api.update_utils import UpdateUtils
from gui.models.system_settings import Cluster

try:
    logger.info(\"Starting check updates process\")
    cluster = Cluster.objects.get()
    node = cluster.get_current_node()
    update_status = UpdateUtils.check_updates()
    gui_version = update_status.get('GUI')
    if gui_version != 'UP2DATE':
        node.version.gui_last_version = gui_version
        logger.info(\"New version available for GUI: {}\".format(gui_version))
    engine_version = update_status.get('Engine')
    if engine_version != 'UP2DATE':
        node.version.engine_last_version = engine_version
        logger.info(\"New version available for Engine: {}\".format(engine_version))
    node.save()
    logger.info(\"Ending check updates process\")
except Exception as e:
    logger.error(\"An error has occurred during check updates process\")
    logger.exception(e)
" > /home/vlt-sys/scripts/check_updates.hour

/bin/echo "OK"
/bin/echo -n "[+] Updating /home/vlt-sys/scripts/get_content ..."

/bin/echo "#!/usr/bin/env /home/vlt-gui/env/bin/python
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

nb_args = len(sys.argv)
if nb_args == 2:
    file_name = sys.argv[1]
    allowed_files = {
        'api_key': '/home/vlt-sys/.dl.apikey',
        'priv_key': '/home/vlt-sys/.dl.privkey',
        'api_email': '/home/vlt-sys/.dl.email',
    }
    file_path = allowed_files.get(file_name)
    if file_path:
        with open(file_path) as f:
            content = f.read()
            print(content)
    else:
        print(\"NOT ALLOWED\", file=sys.stderr)
        sys.exit(2)
else:
    print(\"ARGS ERROR\", file=sys.stderr)
    sys.exit(2)
" > /home/vlt-sys/scripts/get_content

/bin/echo "OK"
/bin/echo -n "[+] Updating /home/vlt-sys/scripts/get_tgt ..."

/bin/echo "#!/usr/bin/env /home/vlt-gui/env/bin/python
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
__author__ = \"Kevin Guillemot\"
__credits__ = []
__license__ = \"GPLv3\"
__version__ = \"3.0.0\"
__maintainer__ = \"Vulture Project\"
__email__ = \"contact@vultureproject.org\"
__doc__ = ''
import sys
import kerberos
import os

nb_args = len(sys.argv)
if nb_args == 3:
    file_name = sys.argv[1]
    service_name = sys.argv[2]
    if file_name.startswith(\"/tmp/krb5cc_\") and len(file_name) == 52 :
        os.environ[\"KRB5CCNAME\"] = \"FILE:\"+file_name
        try:
            ignore, ctx = kerberos.authGSSClientInit(service_name)
            ignore = kerberos.authGSSClientStep(ctx,'')
            tgt = kerberos.authGSSClientResponse(ctx)
        except Exception as e:
            print(\"KERBEROS: Error while retrieving ticket for service {} : {}\".format(service_name,str(e)), file=sys.stderr)
            sys.exit(2)
        print(\"TGT=\"+tgt)
    else:
        print(\"NOT ALLOWED\", file=sys.stderr)
        sys.exit(2)
else:
    print(\"ARGS ERROR\", file=sys.stderr)
    sys.exit(2)
" > /home/vlt-sys/scripts/get_tgt

/bin/echo "OK"
/bin/echo -n "[+] Updating /home/vlt-sys/scripts/install_updates ..."

/bin/echo "#!/usr/bin/env /home/vlt-gui/env/bin/python
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


nb_args = len(sys.argv)
if nb_args == 2:
    update_type = sys.argv[1]
    allowed_updates = (
        'gui',
        'engine'
    )
    if update_type in allowed_updates:
        import logging
        logger = logging.getLogger('cluster')
        # Django setup part
        sys.path.append(\"/home/vlt-gui/vulture/\")
        os.environ.setdefault(\"DJANGO_SETTINGS_MODULE\", 'vulture.settings')
        import django
        django.setup()

        from vulture_toolkit.update_api.update_utils import UpdateUtils
        from gui.models.system_settings import Cluster

        node = Cluster.objects.get().get_current_node()
        version = getattr(node.version, \"{}_last_version\".format(update_type))
        updater = UpdateUtils.get_updater(update_type)
        try:
            status = updater.install(version)
        except Exception as e:
            logger.error(\"An error as occurred during installation of {}\".format(version))
            logger.exception(e)
            status = False
        if status:
            # Re-retrieve node, to prevent error if new attributes has been added during maj
            node = Cluster.objects.get().get_current_node()
            setattr(node.version, '{}_version'.format(update_type), updater.current_version)
            node.save()
            print(\"Successfull Vulture upgrade\", file=sys.stdout)
            sys.exit(0)
    else:
        print(\"This kind of update is not allowed, {}\".format(update_type), file=sys.stderr)
print(\"An error has occurred during upgrade process\", file=sys.stderr)
sys.exit(2)
" > /home/vlt-sys/scripts/install_updates

/bin/echo "OK"
/bin/echo -n "[+] Updating /home/vlt-sys/scripts/update_interface ..."

/bin/echo "#!/usr/bin/env /home/vlt-gui/env/bin/python
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
        print(\"Interface '{}' found.\".format(device))
        try:
            db_intf = Interface.objects.get(device=device, alias='if_' + device)
            print(\"Interface {} already exists.\".format(device))
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
                print(\"IP address {}/{} ({}) already exists.\".format(listener.ip,
                                                                     listener.prefixlen,
                                                                     listener.version))
                continue
            except Listener.DoesNotExist:
                pass
            listener = Listener()
            listener.ip = inet.str_ip_address
            listener.prefixlen = inet.netmask
            listener.version = str(inet.ip_address.version)
            listener.is_physical = True

            listener.save(bootstrap=True)
            print(\"IP address {} inserted.\".format(listener.ip))
            db_intf.inet_addresses.append(listener)
        db_intf.save()
        print(\"Interface {} inserted.\".format(device))
        node.interfaces.append(db_intf)
    node.save(bootstrap=True)
" > /home/vlt-sys/scripts/update_interface

/bin/echo "OK"
/bin/echo -n "[+] Updating /home/vlt-sys/scripts/vulture_apps_starter ..."

/bin/echo "#!/usr/bin/env /home/vlt-gui/env/bin/python
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
            if status == True:
                print(\"Listener {}:{} successfully started\".format(listen_address.address.ip, listen_address.port))
            else:
                print(\"Unable to start listener {}:{}, errors: {}\".format(listen_address.address.ip, listen_address.port, status))


def stop_applications(node):
    done = []
    for listen_address in node.get_listen_addresses():
        token = node.name + listen_address.address.ip + str(listen_address.port)
        if token not in done:
            status = listen_address.stop()
            done.append(token)
            if status == True:
                print(\"Listener {}:{} successfully stopped\".format(listen_address.address.ip, listen_address.port))
            else:
                print(\"Unable to stop listener {}:{}, errors: {}\".format(listen_address.address.ip, listen_address.port, status))


def reload_applications(node):
    done = []
    for listen_address in node.get_listen_addresses():
        token = node.name + listen_address.address.ip + str(listen_address.port)
        if token not in done:
            done.append(token)
            status = listen_address.graceful()
            if status.get('status') == True:
                print(\"Listener {}:{} successfully reload\".format(listen_address.address.ip, listen_address.port))
            else:
                print(\"Unable to graceful listener {}:{}, errors: {}\".format(listen_address.address.ip, listen_address.port, status.get('error')))


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
            print(\"{} : Unknown command\".format(cmd))
            sys.exit(2)
    elif time.time() > timeout:
        print(\"Unable to {} Vulture apps\".format(cmd))
        sys.exit(3)

" > /home/vlt-sys/scripts/vulture_apps_starter

/bin/echo "OK"
/bin/echo -n "[+] Updating /home/vlt-sys/scripts/write_configuration_file ..."

/bin/echo "#!/usr/bin/env /home/vlt-gui/env/bin/python
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
__doc__ = \"\"
import sys

nb_args = len(sys.argv)
if nb_args == 3:
    filename = sys.argv[1]
    content = sys.argv[2]
    allowed_files = ('/etc/resolv.conf',
                     '/etc/ntp.conf',
                     '/etc/mail/mailer.conf',
                     '/usr/local/etc/ssmtp/ssmtp.conf',
                     '/usr/local/etc/fluentd/fluent.conf',
                     '/usr/local/etc/redis.conf',
                     '/usr/local/etc/pf.conf',
                     '/usr/local/etc/sentinel.conf',
                     '/usr/local/etc/logrotate.d/vulture.conf',
                     '/usr/local/etc/vlthaproxy.conf',
                     '/etc/rc.conf.local',
                     '/etc/krb5.conf',
                     '/usr/local/etc/rsyslog.d/rsyslog.conf',
                     '/usr/local/etc/loganalyzer.json',
                     '/home/vlt-sys/Engine/conf/gui-httpd.conf',
                     '/home/vlt-sys/Engine/conf/portal-httpd.conf',
                     '/usr/local/etc/ipsec.conf',
                     '/usr/local/etc/ipsec.secrets',
                     '/usr/local/etc/strongswan.conf',
                     '/usr/local/etc/zabbix4/zabbix_agentd.conf',
                     '/usr/local/etc/zabbix4/pki/ca_cert.crt',
                     '/usr/local/etc/zabbix4/pki/cert.crt',
                     '/usr/local/etc/zabbix4/pki/cert.key',
                     '/usr/local/etc/zabbix4/pki/cert.crl',
                     '/usr/local/etc/zabbix4/pki/psk.key'
                    )
    # Verify if asked file is allowed
    if filename in allowed_files:
        f = open(filename, 'w')
        f.write(content)
        f.close()
    else:
        print(\"NOT ALLOWED\", file=sys.stderr)
        sys.exit(2)
else:
    print(\"ARGS ERROR\", file=sys.stderr)
    sys.exit(2)
" > /home/vlt-sys/scripts/write_configuration_file

