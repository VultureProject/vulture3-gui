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
__author__     = "Olivier de Régis"
__credits__    = []
__license__    = "GPLv3"
__version__    = "3.0.0"
__maintainer__ = "Vulture Project"
__email__      = "contact@vultureproject.org"
__doc__        = """This migration script fix PF whitelist configuration"""

import os
import sys

sys.path.append('/home/vlt-gui/vulture')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", 'vulture.settings')

import django

django.setup()

from gui.models.network_settings import Listener
import subprocess


if __name__ == '__main__':

    proc = subprocess.Popen(['/usr/local/bin/sudo', '-u', 'vlt-sys', '/usr/local/bin/sudo', '/usr/local/bin/sudo', 'chown', 'vlt-gui:wheel', '/usr/local/etc/pf.vulturecluster.conf'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res, errors = proc.communicate()

    proc = subprocess.Popen(['/usr/local/bin/sudo', '-u', 'vlt-sys', '/usr/local/bin/sudo', '/usr/local/bin/sudo', 'chown', 'vlt-gui:wheel', '/usr/local/etc/pf.abuse.conf'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res, errors = proc.communicate()

    proc = subprocess.Popen(['/usr/local/bin/sudo', '-u', 'vlt-sys', '/usr/local/bin/sudo', '/usr/local/bin/sudo', 'chown', 'vlt-gui:wheel', '/usr/local/etc/pf.sshabuse.conf'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res, errors = proc.communicate()

    ips = []
    for listener in Listener.objects.all():
        ips.append(listener.ip)

    ips = set(ips)
    with open('/usr/local/etc/pf.vulturecluster.conf', 'w') as wl:
        wl.write('\n'.join(ips))