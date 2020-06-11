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
__author__ = "Jérémie Jourdin"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ =  ''

import os
import sys

# Django setup part
sys.path.append("/home/vlt-gui/vulture/")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", 'vulture.settings')

import django
django.setup()
import logging
logger = logging.getLogger('cluster')

from gui.models.ssl_certificate import SSLCertificate
from gui.models.system_settings import Cluster
from M2Crypto import X509
from redis import Redis
import subprocess
import time

""" This script is supposed to be run once a Week

 - We need to query Let's encrypt once: We check if we are the MongoDB master for that purpose
 - If we are master: Renew cert + Update MongoDB + Write Files + reload Vulture
 - If we are slave: Wait 15 seconds + Writes Files + reload Vulture
"""

cluster = Cluster.objects.get()
current_node = cluster.get_current_node()

is_master = current_node.is_mongodb_primary()

# Call acme-client to generate the Let's Encrypt challenge
proc = subprocess.Popen(['/usr/local/bin/sudo', '-u', 'vlt-sys', '/usr/local/bin/sudo', '/usr/local/bin/sudo',
                         '/usr/local/sbin/acme.sh', '--cron', '--home', '/usr/local/etc/ssl/acme'],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, env={'PATH': "/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin"})
success, error = proc.communicate()

if error:
    logger.error("Let's encrypt renew error: {}".format(error))
    print("Let's encrypt Error: {}".format(error))
else:
    logger.info("Let's encrypt certificates renewed : {}".format(success))

for cert in SSLCertificate.objects(issuer="LET'S ENCRYPT", status__ne="R"):

    if is_master:
        print("Renewing certificate {}".format(cert.name))

        """ At this point, the certificate is ondisk: We need to store it into MongoDB """
        proc = subprocess.Popen(['/usr/local/bin/sudo', '-u', 'vlt-sys', '/usr/local/bin/sudo', '/usr/local/bin/sudo',
                            '/bin/cat', '/usr/local/etc/ssl/acme/{}/{}.key'.format(cert.cn, cert.cn)],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        private_key, error = proc.communicate()
        if error:
            logger.error("Let's encrypt Error: Unable to read private key : {}".format(error))
            print("Let's encrypt Error: Unable to read private key: {}".format(error))
            continue

        proc = subprocess.Popen(['/usr/local/bin/sudo', '-u', 'vlt-sys', '/usr/local/bin/sudo', '/usr/local/bin/sudo',
                            '/bin/cat', '/usr/local/etc/ssl/acme/{}/{}.cer'.format(cert.cn, cert.cn)],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        certificate, error = proc.communicate()
        if error:
            logger.error("Let's encrypt Error: Unable to read certificate : {}".format(error))
            print("Let's encrypt Error: Unable to read certificate : {}".format(error))
            continue

        proc = subprocess.Popen(['/usr/local/bin/sudo', '-u', 'vlt-sys', '/usr/local/bin/sudo', '/usr/local/bin/sudo',
                            '/bin/cat', '/usr/local/etc/ssl/acme/{}/ca.cer'.format(cert.cn)],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        ca, error = proc.communicate()
        if error:
            logger.error("Let's encrypt Error: Unable to read CA certificate : {}".format(error))
            print("Let's encrypt Error: Unable to read CA certificate : {}".format(error))
            continue

        # Store the certificate
        x509Cert = X509.load_cert_string (certificate)

        cert.cert      = str(certificate.decode('utf8'))
        cert.key       = str(private_key.decode('utf8'))
        cert.name      = str(x509Cert.get_subject())
        cert.status    = 'V'
        cert.issuer    = str("LET'S ENCRYPT")
        cert.validfrom = str(x509Cert.get_not_before().get_datetime())
        cert.validtill = str(x509Cert.get_not_after().get_datetime())

        if x509Cert.check_ca():
            cert.is_ca = True
        else:
            cert.is_ca = False

        cert.serial = str(x509Cert.get_serial_number())
        cert.chain  =  str(ca.decode('utf8'))
        cert.save()

    print("Updating certificate {}".format(cert.name))
    cert.write_certificate()

""" Let's reload Apache's processes """
subprocess.Popen(['/usr/local/bin/sudo', '-u', 'vlt-sys', '/usr/local/bin/sudo', 'service', 'vulture', 'reload'])

