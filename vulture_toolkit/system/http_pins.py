#!/usr/bin/python
# -*- coding: utf-8 -*-

"""Calculate or view HTTP Public Key Pins.

Requires OpenSSL binary.
RFC draft: https://tools.ietf.org/html/draft-ietf-websec-key-pinning-11

Example with CAcert Root CA (Class 1) certificate:
$ wget https://www.cacert.org/certs/root.crt
$ python http_pins.py root.crt
root.crt:
* SPKI fingerprint (sha256): 6f:28:51:40:9d:71:05:04:a3:51:15:ab:cb:9a:6d:d3:f2:57:7e:c9:37:c9:ef:19:38:92:6f:a8:2f:d6:ff:5d
Public-Key-Pins: max-age=600; pin-sha256="byhRQJ1xBQSjURWry5pt0/JXfsk3ye8ZOJJvqC/W/10="
Warning! Per RFC you need at minimum two pins

$ python http_pins.py byhRQJ1xBQSjURWry5pt0/JXfsk3ye8ZOJJvqC/W/10=
SPKI fingerprint (sha256): 6f:28:51:40:9d:71:05:04:a3:51:15:ab:cb:9a:6d:d3:f2:57:7e:c9:37:c9:ef:19:38:92:6f:a8:2f:d6:ff:5d
"""

__author__ = "https://github.com/StalkR"
__credits__ = []
__license__ = "Apache 2.0"
__email__ = "github@stalkr.net"
__doc__ = "https://github.com/StalkR/misc/blob/master/crypto/http_pins.py"
__maintainer__ = "Vulture Project (Kevin Guillemot for Python3 compatibility)"

import binascii
import base64
import hashlib
import logging
import subprocess

logger = logging.getLogger('debug')


def extract_spki(cert):
    args = ['openssl', 'x509', '-pubkey', '-noout']
    proc = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    out = proc.communicate(input=cert.encode('utf8'))[0].decode('utf8').strip().split('\n')
    # remove 1st (BEGIN PUBLIC KEY) and last line (END PUBLIC KEY)
    return base64.b64decode(''.join(map(str.strip, out[1:-1])))


def pin_to_fingerprint(pin):
    return ':'.join(c.encode('hex') for c in pin.decode('base64'))


def fingerprint_to_pin(fingerprint):
    return base64.b64encode(bytes.fromhex(fingerprint.replace(':', '').rstrip())).decode('utf8')


def fingerprint(spki, hash):
    '''Calculate fingerprint of a SubjectPublicKeyInfo given a hash function.'''
    h=hash(spki).hexdigest()
    return ':'.join(i+j for i,j in zip(h[0::2], h[1::2]))


def explain_pin(pin):
    '''Explain a pin by showing its fingerprint with hash algorithm.'''
    try:
        fp = pin_to_fingerprint(pin)
    except binascii.Error:
        print("Error: invalid pin (base64 decode failed)")
        return False

    # +1 to have even ':', /3 for hex representation with ':'
    fp_length = (len(fp) + 1) / 3
    if fp_length == 32:
        algo = 'sha256'
    else:
        algo = ''

    if not algo:
        logger.error("Error: unrecognized algorithm ength %i" % fp_length)
        logger.error("SPKI fingerprint: %s" % fp)
        return False

    logger.debug("SPKI fingerprint (%s): %s" % (algo, fp))
    return True


def getSPKIFingerpring(cert):
    spki = extract_spki(cert)
    fp_sha256 = fingerprint(spki, hashlib.sha256)
    logger.debug("* SPKI fingerprint (sha256): %s" % fp_sha256)
    return fingerprint_to_pin(fp_sha256)
