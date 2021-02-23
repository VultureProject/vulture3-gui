#!/home/vlt-gui/env/bin/python
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
__author__ = "Kevin Guillemot"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = """This migration script rewrite HAProxy certificates on disk """

import os
import sys

sys.path.append('/home/vlt-gui/vulture')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", 'vulture.settings')

import django
django.setup()

from gui.models.network_settings import Loadbalancer
from gui.models.ssl_certificate import SSLCertificate


if __name__ == '__main__':

    # If HAProxy used
    if Loadbalancer.objects.count() == 0:
        print("No load-balancer configured.")
        sys.exit(0)

    for cert in SSLCertificate.objects():
        cert.write_certificate()
        print("Cert {} reloaded".format(cert.name))

    print("Certificates reloaded")
