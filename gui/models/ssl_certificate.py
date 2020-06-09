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
__doc__ = 'Django models dedicated to SSL certificate'


import os
from datetime import datetime

import OpenSSL
from django.conf import settings
from mongoengine import DynamicDocument, StringField, BooleanField

from vulture_toolkit.system.ssl_utils import get_ca_cert_path

import logging
logger = logging.getLogger('debug')



class SSLCertificate(DynamicDocument):
    """ SSL Certificate model representation
    name: name gave to the certificate
    cert: Certificate file
    key: Key file
    chain : certification chain
    is_ca : Certificate have Certification Authority role ?
    """
    name = StringField(required=False, default='internal')

    cert   = StringField(required=False, default='null')
    key    = StringField(required=False)
    serial = StringField(required=False, default="1")
    chain  = StringField(required=False, default='')
    csr    = StringField(required=False)
    crl    = StringField(required=False, default='')

    cn = StringField(required=True)
    c  = StringField(required=False)
    st = StringField(required=False)
    l  = StringField(required=False)
    o  = StringField(required=False)
    ou = StringField(required=False)

    status        = StringField(required=False, default='V')
    issuer        = StringField(required=False)
    validfrom     = StringField(required=False)
    validtill     = StringField(required=False)
    is_ca         = BooleanField(default=False)
    is_trusted_ca = BooleanField(default=False)

    rev_date = StringField(required=False)

    def __init__(self, *args, **kwargs):
        super(SSLCertificate, self).__init__(*args, **kwargs)

        #If DN is not set and if cert exists, this is a new certificate that comes from Bootstrap

    def as_pem(self, **kwargs):
        """Return certificate as PEM format

        :param kwargs: cert = True to retrieve only certificate, key=True for key
        :return:cert and/or it key in function of kwargs
        """
        pem = ''
        if 'cert' in kwargs.keys() and kwargs['cert']:
            pem += self.cert

        if 'key' in kwargs.keys() and kwargs['key']:
            pem += self.key

        return pem


    def write_MongoCert (self):
        """Save the certificate/key and associated ca on disk for use in mongoDB connection
        MongoDB requires that certificate and key are in the same file

        :return: certificate_path, chain_path
        """
        file_tmp = None
        try:
            file_tmp = open("/home/vlt-sys/Engine/conf/cert-" + str(self.id) + ".pem", "r")
        except Exception as e:
            pass

        # If the file does not exists yet, create it
        if file_tmp is None:
            file = open("/home/vlt-sys/Engine/conf/cert-" + str(self.id) + ".pem", "w")
            file.write(self.cert)
            if self.key:
                file.write("\n")
                #FIXME: Encrypt Key
                file.write(self.key)
            file.close()

            file = open("/home/vlt-sys/Engine/conf/cert-" + str(self.id) + ".key", "w")
            if self.key:
                #FIXME: Encrypt Key
                file.write(self.key)
            file.close()

            file = open("/home/vlt-sys/Engine/conf/cert-" + str(self.id) + ".crt", "w")
            file.write(self.cert)
            file.close()

            # Set permissions to this file
            os.chmod("/home/vlt-sys/Engine/conf/cert-" + str(self.id) + ".pem", 660)
            os.chmod("/home/vlt-sys/Engine/conf/cert-" + str(self.id) + ".key", 660)
            os.chmod("/home/vlt-sys/Engine/conf/cert-" + str(self.id) + ".crt", 660)
            os.system("/usr/bin/chgrp vlt-web /home/vlt-sys/Engine/conf/cert-" + str(self.id) + ".pem")
            os.system("/usr/bin/chgrp vlt-web /home/vlt-sys/Engine/conf/cert-" + str(self.id) + ".key")
            os.system("/usr/bin/chgrp vlt-web /home/vlt-sys/Engine/conf/cert-" + str(self.id) + ".crt")
        else:
            file_tmp.close()

        # If the file already exists, nothing to do
        file_tmp = None
        try:
            file_tmp = open("/home/vlt-sys/Engine/conf/ca-" + str(self.id) + ".pem", "r")
        except Exception as e:
            pass

        if file_tmp is None:
            #Always add the local CA Cert in chain file
            ca_path = get_ca_cert_path()
            file = open(ca_path, "r")
            ca = file.read()
            file.close()

            file = open("/home/vlt-sys/Engine/conf/ca-" + str(self.id) + ".pem", "w")
            file.write(ca)
            file.write("\n")
            file.write(self.chain)
            file.close()

            # Set permissions to this file
            try:
                os.chmod("/home/vlt-sys/Engine/conf/ca-" + str(self.id) + ".pem", 660)
                os.system("/usr/bin/chgrp vlt-web /home/vlt-sys/Engine/conf/ca-" + str(self.id) + ".pem")
            except Exception as e:
                pass
        else:
            file_tmp.close()

        return "/home/vlt-sys/Engine/conf/cert-"+str(self.id)+".pem", "/home/vlt-sys/Engine/conf/ca-" + str(self.id) + ".pem",


    def genCRL(self, rev_date):
        """ Build and return the CRL associated to the certificate
            if self.crl exists: It is an externaly maintained CRL: Just return it
            if not: It is the Vulture internal CRL, build it from the list of all revoked certificate
        """
        if self.crl:
            return self.crl

        CRL = OpenSSL.crypto.CRL()

        # Find all revoked certificates
        certs = SSLCertificate.objects.filter(status='R').order_by('serial')
        for cert in certs:
            rev = OpenSSL.crypto.Revoked()
            rev.set_rev_date(cert.rev_date.encode('utf8'))
            # This method hates 'x' in hexadecimal notation...
            rev.set_serial(b''+bytes(hex(int(cert.serial)).replace('x', ''), encoding='utf8'))
            rev.set_reason(b'cessationOfOperation')
            CRL.add_revoked(rev)

        from gui.models.system_settings import Cluster
        cluster = Cluster.objects.get()

        # Find the internal CA's certificate and private key
        internal = cluster.ca_certificate
        ca_key = OpenSSL.crypto.load_privatekey(OpenSSL.crypto.FILETYPE_PEM, str(internal.key))
        ca_cert = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, str(internal.cert))

        # Now export the CRL into the cluster
        cluster.ca_crl = CRL.export(ca_cert, ca_key, OpenSSL.crypto.FILETYPE_PEM, 365, b"sha256").decode('utf8')
        cluster.save()
        return cluster.ca_crl


    def getCRL(self):
        """
        :return:Return the CRL associated to the certificate
         - Either the CRL manually defined in the cert
         - Or the cluster CRL
        """
        if self.crl:
            return self.crl

        from gui.models.system_settings import Cluster
        cluster = Cluster.objects.get()
        return cluster.ca_crl



    def revoke(self):
        """
        Revoke a certificate. If it's a Trusted CA, just delete-it 
         because we don't have the private key so we can't revoke it.
         Else revoke-it.
        :return: 
        """

        if self.is_trusted_ca:
            self.delete()
            from gui.models.system_settings import Cluster
            cluster = Cluster.objects.get()
            cluster.api_request("/api/certs/remove_ca/{}".format(str(self.id)))
        
        else:
            rev_date = "{:%Y%m%d%H%M%SZ}".format(datetime.now())

            self.status = 'R'
            self.rev_date = rev_date
            self.serial = str(self.serial)
            self.save()
            self.genCRL(rev_date)

            from gui.models.system_settings import Cluster
            cluster = Cluster.objects.get()
            cluster.api_request("/api/certs/remove/{}".format(str(self.id)))



    """ Write the certificate in conf directory
    """
    def write_certificate(self):

        #Special directory for ha-proxy
        try:
            os.system("mkdir -p {}haproxy".format(settings.CONF_DIR))
        except Exception as e:
            logger.error("Unable to build configuration. Reason is: " + str(e))
            return None

        if self.cert and self.key:
            try:
                # FIXME
                rsa_key = str(self.key)
                rsa_key = rsa_key.replace("-----BEGIN PRIVATE KEY-----", "-----BEGIN RSA PRIVATE KEY-----")
                rsa_key = rsa_key.replace("-----END PRIVATE KEY-----", "-----END RSA PRIVATE KEY-----")

                with open("%sSSLProxyCertificateFile-%s.txt" % (settings.CONF_DIR, self.id), 'w') as f:
                    f.write(self.cert)
                    f.write('\n')
                    f.write(rsa_key)

                with open("%shaproxy/Certificate-%s.pem" % (settings.CONF_DIR, self.id), 'w') as f:
                    f.write(rsa_key)
                    f.write('\n')
                    f.write(self.cert)
                    # FIXME
                    if self.chain:
                        f.write("\n" + self.chain)

            except Exception as e:
                logger.error("Unable to build configuration. Reason is: " + str(e))
                return None

        try:
            # FIXME
            os.system("/bin/chmod 640 %sSSL*" % settings.CONF_DIR)
            os.system("/usr/sbin/chown vlt-gui:daemon %sSSL*" % settings.CONF_DIR)

            os.system("/usr/sbin/chown -R vlt-gui:daemon %shaproxy" % settings.CONF_DIR)
            os.system("/bin/chmod 770 %shaproxy" % settings.CONF_DIR)
            os.system("/bin/chmod 640 %shaproxy/*" % settings.CONF_DIR)

        except Exception as e:
            logger.error("Unable to build configuration. Reason is: " + str(e))
            return None

        return True

    def __str__(self):
        return "{}" .format(self.name)
