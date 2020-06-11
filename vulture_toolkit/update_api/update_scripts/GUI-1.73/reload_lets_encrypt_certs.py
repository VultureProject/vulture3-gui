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
__author__ = "Kevin Guillemot"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = """This migration script loop over old let's encrypt certificates to reload them with acme.sh """

import os
import sys

sys.path.append('/home/vlt-gui/vulture')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", 'vulture.settings')

import django
django.setup()

from gui.models.ssl_certificate import SSLCertificate
from M2Crypto import X509
import subprocess

if __name__ == '__main__':

    for cert in SSLCertificate.objects(issuer="LET'S ENCRYPT", status__ne="R"):

        print "Updating certificate {}".format(cert.cn)
        # Call acme-client to generate the Let's Encrypt challenge
        proc = subprocess.Popen(['/usr/local/sbin/acme.sh', '--issue', '-d', cert.cn, '--webroot',
                                 '/home/vlt-sys/Engine/conf',
                                 '--cert-home', '/usr/local/etc/ssl/acme'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                env={'PATH': "/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin"})
        success, error = proc.communicate()

        if error:
            print "Let's encrypt Error: {}".format(error)
            continue
        else:
            print "Let's encrypt certificate was issued for '{}".format(cert.cn)

            """ At this point, the certificate is ondisk: We need to store it into MongoDB """
            proc = subprocess.Popen(
                ['/bin/cat', '/usr/local/etc/ssl/acme/{}/{}.key'.format(cert.cn, cert.cn)],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            private_key, error = proc.communicate()
            if error:
                print "Let's encrypt Error: Unable to read private key : {}".format(error)
                continue

            proc = subprocess.Popen(
                ['/bin/cat', '/usr/local/etc/ssl/acme/{}/ca.cer'.format(cert.cn)],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            ca, error = proc.communicate()
            if error:
                print "Let's encrypt Error: Unable to read CA : {}".format(error)
                continue

            proc = subprocess.Popen(
                ['/bin/cat', '/usr/local/etc/ssl/acme/{}/{}.cer'.format(cert.cn, cert.cn)],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            certificate, error = proc.communicate()
            if error:
                print "Let's encrypt Error: Unable to read certificate : {}".format(error)
                continue

            # Store the certificate
            x509Cert = X509.load_cert_string(certificate)

            cert.cert = str(certificate)
            cert.key = str(private_key)
            cert.name = str(x509Cert.get_subject())
            cert.status = 'V'
            cert.issuer = str("LET'S ENCRYPT")
            cert.validfrom = str(x509Cert.get_not_before().get_datetime())
            cert.validtill = str(x509Cert.get_not_after().get_datetime())
            if x509Cert.check_ca():
                cert.is_ca = True
            else:
                cert.is_ca = False
            cert.serial = str(x509Cert.get_serial_number())
            cert.chain = str(ca)
            cert.save()

            cert.write_certificate()
