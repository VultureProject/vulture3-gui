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
__credits__ = ["eskil@yelp.com"]
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = 'System Utils SSL Toolkit'

import re
import subprocess
import time

from M2Crypto import X509, EVP, RSA, ASN1


def mk_ca_issuer(CN, C, ST, L, O, OU):
    """Our default CA issuer name.

    :param CN: Common Name field
    :param C: Country Name
    :param ST: State or province name
    :param L: Locality
    :param O: Organization
    :param OU: Organization Unit
    :return:
    """
    issuer = X509.X509_Name()
    issuer.C = C
    issuer.CN = CN
    issuer.ST = ST
    issuer.L = L
    issuer.O = O
    issuer.OU = OU
    return issuer


def mk_cert_valid(cert, days=3652):
    """Make a cert valid from now and til 'days' from now.

    :param cert: cert to make valid
    :param days: number of days cert is valid for from now.
    """
    t = int(time.time())
    now = ASN1.ASN1_UTCTIME()
    now.set_time(t)
    expire = ASN1.ASN1_UTCTIME()
    expire.set_time(t + days * 24 * 60 * 60)
    cert.set_not_before(now)
    cert.set_not_after(expire)


def mk_request(bits, CN, C, ST, L, O, OU):
    """Create a X509 request with the given number of bits in they key.

    :param bits: number of RSA key bits
    :param CN: Common Name field
    :param C: Country Name
    :param ST: State or province name
    :param L: Locality
    :param O: Organization
    :param OU: Organization Unit
    :returns: a X509 request and the private key (EVP)
    """
    pk = EVP.PKey()
    x = X509.Request()
    rsa = RSA.gen_key(bits, 65537, lambda: None)
    pk.assign_rsa(rsa)
    x.set_pubkey(pk)
    name = x.get_subject()

    if CN is None:
        CN = ""
    if C is None:
        C = ""
    if ST is None:
        ST = ""
    if L is None:
        L = ""
    if O is None:
        O = ""
    if OU is None:
        OU = ""
        
    name.CN = CN
    name.C = C
    name.ST = ST
    name.L = L
    name.O = O
    name.OU = OU
    x.sign(pk, 'sha256')
    return x, pk


def mk_ca_cert(CN, C, ST, L, O, OU):
    """Make a CA certificate.

    :param CN: Common Name field
    :param C: Country Name
    :param ST: State or province name
    :param L: Locality
    :param O: Organization
    :param OU: Organization Unit
    :returns: the certificate, private key and public key.
    """
    req, pk = mk_request(2048, CN, C, ST, L, O, OU)
    pkey = req.get_pubkey()
    cert = X509.X509()
    cert.set_serial_number(1)
    cert.set_version(2)
    mk_cert_valid(cert, 7200)
    cert.set_issuer(mk_ca_issuer(CN, C, ST, L, O, OU))
    cert.set_subject(cert.get_issuer())
    cert.set_pubkey(pkey)
    cert.add_ext(X509.new_extension('basicConstraints', 'CA:TRUE'))
    cert.add_ext(X509.new_extension('subjectKeyIdentifier', str(cert.get_fingerprint())))
    cert.add_ext(X509.new_extension('subjectAltName', 'DNS:{}'.format(CN)))
    cert.sign(pk, 'sha256')
    return cert, pk, pkey



def mk_cert(serial):
    """Make a certificate.

    :return: a new cert.
    """
    cert = X509.X509()
    cert.set_serial_number(serial)
    cert.set_version(2)
    mk_cert_valid(cert, 1825)
    cert.add_ext(X509.new_extension('keyUsage', 'digitalSignature, keyEncipherment'))
    cert.add_ext(X509.new_extension('nsComment', 'Issued by VulturePKI'))
    cert.add_ext(X509.new_extension('extendedKeyUsage', 'serverAuth, clientAuth'))

    return cert


def mk_ca_cert_files(CN, C, ST, L, O, OU):
    """Create CA cacert files (cert + key).

    :param CN: Common Name field
    :param C: Country Name
    :param ST: State or province name
    :param L: Locality
    :param O: Organization
    :param OU: Organization Unit
    """
    ca_cert, pk1, pkey = mk_ca_cert(CN, C, ST, L, O, OU)

    # Save files
    ca_cert.save_pem(get_ca_cert_path())
    pk1.save_key(get_ca_key_path(), cipher=None)
    return ca_cert, pk1


def mk_signed_cert(ca_cert_file, ca_key_file, CN, C, ST, L, O, OU, serial):
    """Create certificate (cert+key) signed by the given CA, and with the
    given parameters.

    :param ca_cert_file: Path to the CA cert file
    :param ca_key_file: Path to the CA key file
    :param CN: Common Name field
    :param C: Country Name
    :param ST: State or province name
    :param L: Locality
    :param O: Organization
    :param OU: Organization Unit
    :param serial: Certificate serial number
    :return: Certificate and certificate key
    """
    cert_req, pk2 = mk_request(2048, CN, C, ST, L, O, OU)
    ca_cert = X509.load_cert(ca_cert_file)
    pk1 = EVP.load_key(ca_key_file)

    # Sign certificate
    cert = mk_cert(serial)
    cert.set_subject(cert_req.get_subject())
    cert.set_pubkey(cert_req.get_pubkey())
    cert.set_issuer(ca_cert.get_issuer())
    cert.add_ext(X509.new_extension('subjectAltName', 'DNS:{}'.format(CN)))
    cert.sign(pk1, 'sha256')

    return cert, pk2


def mk_signed_cert_files(ca_cert_file, ca_key_file, CN, C='fr', ST='', L='',
                         O='', OU='', serial=1):#FIXME default parameters
    """Create certificate files (cert+key) signed by the given CA, and with the
    given parameters.

    :param ca_cert_file: Path to the CA cert file
    :param ca_key_file: Path to the CA key file
    :param CN: Common Name field
    :param C: Country Name
    :param ST: State or province name
    :param L: Locality
    :param O: Organization
    :param OU: Organization Unit
    """
    cert, pk2 = mk_signed_cert(ca_cert_file, ca_key_file, CN, C, ST, L, O, OU,
                               serial)

    cert.save_pem(get_cert_path())
    pk2.save_key(get_key_path(), cipher=None)

    # Writing PEM File for MongoDB
    f = open(get_cert_dir()+"mongod.pem", 'wb')
    cert_and_key = cert.as_pem() + pk2.as_pem(None)
    f.write(cert_and_key)
    f.close()
    # Writing Cert and Key
    f_cert = open(get_cert_dir()+"mongod.cert", 'wb')
    f_cert.write(cert.as_pem())
    f_cert.close()
    f_key = open(get_cert_dir()+"mongod.key", 'wb')
    f_key.write(pk2.as_pem(None))
    f_key.close()
    return cert, pk2


def get_cert_dir():
    return "/var/db/mongodb/"#TODO PATH IN SETTINGS


def get_cert_path():
    """ Retrieve node cert

    :return: Path to the cert file
    """
    path = get_cert_dir()
    return path+"mongod.cert"


def get_pem_path():
    """ Retrieve node pem file (cert+key)

    :return: Path to the pem file
    """
    path = get_cert_dir()
    return path+"mongod.pem"


def get_key_path():
    """ Retrieve node cert key file

    :return: Path to the key file
    """
    path = get_cert_dir()
    return path+"mongod.key"


def get_ca_cert_path():
    """ Retrieve CA cert

    :return: Path to the CA cert file
    """
    path = get_cert_dir()
    return path+"ca.pem"


def get_ca_key_path():
    """ Retrieve CA cert

    :return: Path to the CA key file
    """
    path = get_cert_dir()
    return path+"ca.key"


def get_openssl_engines():
    output = "(builtin) Software engine\n" + subprocess.check_output(['openssl','engine']).decode('utf8')
    engines = re.findall("\((.*)\) (.*)", output, re.M)
    return engines
