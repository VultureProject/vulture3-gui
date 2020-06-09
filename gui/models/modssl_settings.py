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
__author__ = "Jérémie Jourdin"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = 'Django models dedicated to Apache mod_ssl'

import logging
import os
from datetime import datetime

from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from mongoengine import BooleanField, DynamicDocument, IntField, PULL, ReferenceField, StringField
from gui.models.ssl_certificate import SSLCertificate

logger = logging.getLogger('debug')


class ModSSL(DynamicDocument):
    """ Vulture mod_ssl model representation
    name:       A friendly name for the mod_ssl profile

    """

    name = StringField(required=True, help_text=_('Friendly Name to reference this SSL Profile'))
    engine = StringField(required=False, help_text=_('SSL accelerator, if available on your system'))
    certificate = ReferenceField('SSLCertificate', required=True, reverse_delete_rule=PULL, help_text=_('X509 certificate to use for this SSL profile'))
    protocols = StringField(required=True, help_text=_('Accepted TLS Protocols'))
    ciphers = StringField(required=True, default='HIGH:!MEDIUM:!LOW:!aNULL:!eNULL:!EXP:SHA1:!MD5:SSLv3:!SSLv2', help_text=_('Autorized SSL ciphers'))
    honorcipherorder = BooleanField(required=False, default=True, help_text=_('Use server\'s ciphers preferences instead of client preferences'))
    ocsp_responder_enable = BooleanField(required=False, default=False, help_text=_('Enable OCSP validation of client certificates'))
    ocsp_responder_default = StringField(required=False, default='http://responder.example.com:8888/responder', help_text=_('URI of the default OCSP responder to use'))
    ocsp_responder_override = BooleanField(required=False, default=False, help_text=_('Ignore OCSP responder in client certificate and use the default OCSP responder instead'))
    ocsp_responder_timeout = IntField(required=False, default=10, help_text=_('Timeout for OCSP requests, in seconds'))
    ssl_options_vhost = StringField(required=False, default='SSLVerifyDepth 3', help_text=_('Custom mod_ssl \'SSLOptions\', in virtualhost context'))
    ssl_options_app = StringField(required=False, help_text=_('Custom mod_ssl \'SSLOptions\', in application context'))
    verifyclient = StringField(required=True, default='none', help_text=_('Do clients have to present a certificate ?'))
    # SSLCARevocationCheck
    verify_crl = StringField(required=True, default='none', help_text=_('Enables certificate revocation list (CRL) checking.'))
    # SSLCACertificateFile
    accepted_ca = StringField(required=False, help_text=_('List of valid PEM certificates for client authentication'))
    redirect_no_cert = StringField(required=False, help_text=_('Redirect to this URL if no certificate is presented by the client'))
    hpkp_enable = BooleanField(required=False, default=False, help_text=_('Add HTTP Public Key Pinning Extensions'))
    hpkp_other = StringField(required=False, default="max-age=2592000; includeSubDomains", help_text=_('Additional DATA for Public-Key-Pins header'))
    # OSCP
    enable_ocsp_stapling = BooleanField(required=False, default=True, help_text=_("Enable OCSP Stapling for better performances (see https://www.digicert.com/enabling-ocsp-stapling.htm)"))

    """Write configuration on disk
    """
    def writeConf(self):

        if self.accepted_ca:
            try:
                with open("%s/SSLCACertificateFile-%s.txt" % (settings.CONF_DIR, self.id), 'w') as f:
                    f.write(self.accepted_ca)
            except Exception as e:
                logger.error("Unable to build configuration. Reason is: " + str(e))
                return None

        if self.certificate.cert:
            try:
                with open("%s/SSLCertificateFile-%s.txt" % (settings.CONF_DIR, self.id), 'w') as f:
                    f.write(self.certificate.cert)
                    if self.certificate.chain:
                        f.write("\n" + self.certificate.chain)
            except Exception as e:
                logger.error("Unable to build configuration. Reason is: " + str(e))
                return None

        if self.certificate.key:
            try:
                with open("%s/SSLCertificateKeyFile-%s.txt" % (settings.CONF_DIR, self.id), 'w') as f:
                    f.write(self.certificate.key)
            except Exception as e:
                logger.error("Unable to build configuration. Reason is: " + str(e))
                return None

        # Update the CRL on disk
        crl = self.certificate.getCRL()
        if not crl:
            rev_date = "{:%Y%m%d%H%M%SZ}".format(datetime.now())
            crl = self.certificate.genCRL(rev_date)
        try:
            with open("%s/SSLCARevocationFile-%s.crl" % (settings.CONF_DIR, self.id), 'w') as f:
                f.write(crl)
        except Exception as e:
            logger.error("Unable to build configuration. Reason is: " + str(e))
            return None

        try:
            os.system("chmod 640 %sSSL*" % settings.CONF_DIR)
            os.system("chown vlt-gui:daemon %sSSL*" % settings.CONF_DIR)
        except Exception as e:
            logger.error("Unable to build configuration. Reason is: " + str(e))
            return None

        return True


    """ Write certificates on disk for HAProxy uses """
    def write_HAProxy_conf(self):

        if self.accepted_ca:
            try:
                with open("%shaproxy/CACertificate-%s.pem" % (settings.CONF_DIR, self.id), 'w') as f:
                    f.write(self.accepted_ca.encode('utf8', 'ignore'))
            except Exception as e:
                logger.error("Unable to build configuration. Reason is: " + str(e))
                return None


        # Update the CRL on disk
        crl = self.certificate.getCRL()
        if not crl:
            rev_date = "{:%Y%m%d%H%M%SZ}".format(datetime.now())
            crl = self.certificate.genCRL(rev_date)

        try:
            with open("%shaproxy/CACRL-%s.crl" % (settings.CONF_DIR, self.id), 'w') as f:
                f.write(crl)
        except Exception as e:
            logger.error("Unable to build configuration. Reason is: " + str(e))
            return None

        try:
            os.system("/usr/sbin/chown vlt-gui:daemon %shaproxy" % settings.CONF_DIR)
            os.system("/bin/chmod 770 %shaproxy" % settings.CONF_DIR)
            os.system("/bin/chmod 640 %shaproxy/*" % settings.CONF_DIR)
        except Exception as e:
            logger.error("Unable to build configuration. Reason is: " + str(e))
            return None

        return True



    def get_tags(self):
        ret = ""
        for s in self.format.split(','):
            ret = ret + '"' + s + '",'
        return ret[:-1]

    def __str__(self):
        return self.name
