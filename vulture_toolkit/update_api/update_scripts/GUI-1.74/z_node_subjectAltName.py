#!/usr/bin/env /home/vlt-gui/env/bin/python
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
__doc__ = """This migration script create indexes in Mongo database to prevent COLLSCAN searches """

import os
import sys

sys.path.append('/home/vlt-gui/vulture')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", 'vulture.settings')

import django
django.setup()

from gui.models.system_settings import Cluster
from gui.models.modssl_settings import ModSSL
from vulture_toolkit.system import ssl_utils

from M2Crypto import X509


if __name__ == '__main__':

    ca_cert = X509.load_cert(ssl_utils.get_ca_cert_path())

    C = ""
    ST = ""
    L = ""
    O = ""
    OU = ""
    for i in ca_cert.get_subject().as_text().split(','):
        i = i.strip()
        print(i)
        if i[:2] == "C=":
            C = i[2:]
        elif i[:3] == "ST=":
            ST = i[3:]
        elif i[:2] == "L=":
            L = i[2:]
        elif i[:2] == "O=":
            O = i[2:]
        elif i[:3] == "OU=":
            OU = i[3:]

    cluster = Cluster.objects.get()
    serial = cluster.ca_serial
    serial += 1

    node = cluster.get_current_node()

    crt, key = ssl_utils.mk_signed_cert_files(ssl_utils.get_ca_cert_path(),
                                        ssl_utils.get_ca_key_path(),
                                        node.name,
                                        C,
                                        ST,
                                        L,
                                        O,
                                        OU,
                                        serial)

    cluster.ca_serial = serial
    cluster.save()

    certificate = node.certificate
    certificate.name = str(crt.get_subject())
    certificate.c = C
    certificate.st = ST
    certificate.l = L
    certificate.o = O
    certificate.ou = OU
    certificate.cert = crt.as_pem().decode('utf8')
    certificate.key = key.as_pem(cipher=None).decode('utf8')
    certificate.status = 'V'
    certificate.issuer = str(crt.get_issuer())
    certificate.validfrom = str(crt.get_not_before().get_datetime())
    certificate.validtill = str(crt.get_not_after().get_datetime())

    certificate.serial = str(serial)
    certificate.is_ca = False
    certificate.save()

    node.certificate = certificate
    node.save()

    for mod_ssl in ModSSL.objects.filter(certificate=certificate):
        print("[+] Writing certificate files for TLSProfile named '{}'".format(mod_ssl.name))
        mod_ssl.writeConf()

    # Restart mongodb, to take certificate changes
    print("[+] Restarting Mongodb")
    os.system("/usr/sbin/service mongod restart")
