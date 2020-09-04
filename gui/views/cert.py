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
__doc__ = 'Django views dedicated to certificate management'

import logging
import logging.config
from itertools import zip_longest

from M2Crypto import X509, RSA, BIO, EVP, EC
from bson.objectid import ObjectId
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, HttpResponse
from django.template import RequestContext

from gui.decorators import group_required
from gui.forms.cert_settings import CertForm
from gui.models.system_settings import Cluster
from gui.models.ssl_certificate import SSLCertificate
from gui.signals.gui_signals import config_modified
from vulture_toolkit.system.ssl_utils import get_ca_cert_path, get_ca_key_path, mk_cert, mk_signed_cert

import subprocess
import os

from django.conf import settings
logging.config.dictConfig(settings.LOG_SETTINGS)
logger = logging.getLogger('debug')


@group_required('administrator', 'system_manager')
def cert_list(request):
    """ Page dedicated to show certificate list
    """
    try:
        certs = SSLCertificate.objects(is_trusted_ca__ne=True)
    except DoesNotExist:
        certs = None

    try:
        trusted_ca_list = SSLCertificate.objects(is_trusted_ca=True)
    except DoesNotExist:
        trusted_ca_list = None

    return render_to_response('cert.html', {'certs': certs, 'trusted_ca_list': trusted_ca_list}, context_instance=RequestContext(request))


@group_required('administrator', 'system_manager')
def download(request, object_id=None):
    """ method dedicated to certificate download
    :param request: Django request object
    """
    cert = SSLCertificate.objects.with_id(ObjectId(object_id))
    response = HttpResponse(cert.cert, content_type='application/force-download')
    response['Content-Disposition'] = 'attachment; filename=' + cert.cn + '.crt'
    return response


@group_required('administrator', 'system_manager')
def edit(request, object_id=None):
    """ method dedicated to certificate modification
    :param request: Django request object
    Obviously, only properties not related to the certificate can be modified
    It is possible to change:
        - The friendly name of the certificate
        - The chain list
    """

    # Retrieving access configuration
    if object_id:
        cert = SSLCertificate.objects.with_id(ObjectId(object_id))
    else:
        return HttpResponseRedirect('/system/cert/')

    if request.method == 'POST':
        dataPosted = request.POST

        error = dict()
        err = None
        name = None
        chain = None
        crl = None

        try:
            chain = str(dataPosted['chain'])
        except:
            err = 1
            error['chain'] = 'Chain is missing'
            pass

        try:
            name = str(dataPosted['name'])
        except:
            err = 1
            error['cert'] = 'Name is missing'
            pass

        if chain:
            cert.chain = chain

        try:
            crl = str(dataPosted['crl'])
        except:
            pass

        cert.crl = crl

        if name:
            cert.name = name
        else:
            err = 1
            error['cert'] = 'Name is required'

        if err:
            return render_to_response('cert_edit.html', {'cert': cert, 'object_id': object_id, 'error': error}, context_instance=RequestContext(request))

        # Update certificate details
        cert.save()
        config_modified.send(sender=SSLCertificate, id=cert.id)

        return HttpResponseRedirect('/system/cert/')

    return render_to_response('cert_edit.html', {'cert': cert, 'object_id': object_id, }, context_instance=RequestContext(request))


"""Callback function used by RSA.load_key_bio
Simply return the content of POST['keypass']
"""
keypass = None


def read_pass_from_POST(*args):
    """ This function needs to return bytes """
    global keypass
    if isinstance(keypass, str):
        return keypass.encode('utf8')
    return keypass


@group_required('administrator', 'system_manager')
def load(request):
    """ method dedicated to certificate importation
    :param request: Django POST request object
    :param POST['cert']: The PEM X509 certificate
    :param POST['key']: The PEM X509 key
    :param POST['chain']: The PEM X509 certificate chain
    """
    cert = SSLCertificate()
    cert.cert = ""
    cert.key = ""
    cert.chain = ""
    if request.method == 'POST':
        dataPosted = request.POST

        error = dict()
        err = None
        try:
            cert_cert = dataPosted['cert']
        except:
            err = True
            error['cert'] = "X509 PEM Certificate required"
            pass

        try:
            cert_key = dataPosted['key']
        except:
            err = True
            error['key'] = "X509 PEM Key required"
            pass

        try:
            cert.chain = str(dataPosted['chain'])
        except:
            pass

        if err:
            return render_to_response('cert_import.html', {'cert': cert, 'error': error}, context_instance=RequestContext(request))

        # Check the certificate
        try:
            x509Cert = X509.load_cert_string(bytes(cert_cert, 'utf8'))
            cert.cert = str(cert_cert)
        except:
            error['cert'] = "Invalid X509 PEM Certificate"
            return render_to_response('cert_import.html', {'cert': cert, 'error': error}, context_instance=RequestContext(request))

        global keypass
        try:
            keypass = str(dataPosted['keypass'])
        except:
            pass

        # Check the private key
        try:
            bio = BIO.MemoryBuffer(bytes(cert_key, 'utf8'))
            RSA.load_key_bio(bio, callback=read_pass_from_POST)
            cert.key = str(cert_key)
        except RSA.RSAError:
            try:
                bio = BIO.MemoryBuffer(bytes(cert_key, 'utf8'))
                EC.load_key_bio(bio, callback=read_pass_from_POST)
                cert.key = str(cert_key)
            except RSA.RSAError:
                error['keypass'] = "Invalid KEY"
            except Exception as e:
                logger.exception(e)
                error['key'] = "Invalid PEM KEY"
        except Exception as e:
            logger.exception(e)
            error['key'] = "Invalid PEM KEY"

        if error:
            return render_to_response('cert_import.html', {'cert': cert, 'error': error}, context_instance=RequestContext(request))

        # Store certificate details
        cert.name = str(x509Cert.get_subject())
        cert.status = 'V'
        cert.issuer = str(x509Cert.get_issuer())
        try:
            cert.validfrom = str(x509Cert.get_not_before().get_datetime())
        except Exception as e:
            logger.error("Exception while retrieving validation date 'before' of certificates : ")
            logger.exception(e)

        try:
            cert.validtill = str(x509Cert.get_not_after().get_datetime())
        except Exception as e:
            logger.error("Exception while retrieving validation date 'after' of certificates : ")
            logger.exception(e)

        if x509Cert.check_ca():
            cert.is_ca = True
        else:
            cert.is_ca = False

        # Find certificate fields
        fields = cert.name.split('/')
        for field in fields:
            tmp = field.split('=')
            if str(tmp[0]) == "CN":
                cert.cn = tmp[1]
            elif str(tmp[0]) == "C":
                cert.c = tmp[1]
            elif str(tmp[0]) == "ST":
                cert.st = tmp[1]
            elif str(tmp[0]) == "L":
                cert.l = tmp[1]
            elif str(tmp[0]) == "O":
                cert.o = tmp[1]
            elif str(tmp[0]) == "OU":
                cert.ou = tmp[1]

        # if cert.cn is empty check if subjectAltName is set en use it
        if(not cert.cn):
            alt_name=x509Cert.get_ext('subjectAltName').get_value()
        if(alt_name):
            cert.cn=alt_name

        cert.save()

        return HttpResponseRedirect('/system/cert/')

    return render_to_response('cert_import.html', {'cert': cert, }, context_instance=RequestContext(request))


@group_required('administrator', 'system_manager')
def load_ca(request):
    """ method dedicated to certificate importation
    :param request: Django POST request object
    :param POST['cert']: The PEM X509 trusted CA
    """
    # Used to api_request the write of the new certificates
    cluster = Cluster.objects.get()

    cert = SSLCertificate()
    str_cert_list = ""

    if request.method == 'POST':
        dataPosted = request.POST

        users_cn = ""
        error = dict()
        err = None
        try:
            str_cert_list = str(dataPosted['cert'])
        except:
            err = True
            error['cert'] = "X509 PEM trusted CA required"
            pass

        try:
            users_cn = str(dataPosted['cn'])
        except:
            pass

        if err:
            return render_to_response('cert_import_ca.html', {'cert': cert, 'error': error}, context_instance=RequestContext(request))

        # If the user provide CN, split them
        users_cn = users_cn.replace(' ', '')
        users_cn_list = filter(lambda x: x, users_cn.split(";"))

        # Create a list with the certificates the user imported
        cert_list = filter(lambda x: x, str_cert_list.split("-----BEGIN CERTIFICATE-----"))

        # Create the CAs in Mongo
        ca_count = 0
        for cer_pem, users_cn in zip_longest(cert_list, users_cn_list):
            if not cer_pem:
                break
            if "-----BEGIN CERTIFICATE-----" not in cer_pem:
                cer_pem = "-----BEGIN CERTIFICATE-----" + cer_pem

            cert = SSLCertificate()
            cert.cert = cer_pem
            cert.key = ""
            cert.chain = ""
            cert.is_trusted_ca = True

            # Check the certificate
            try:
                x509Cert = X509.load_cert_string(cert.cert)
            except:
                error['cert'] = "Invalid X509 PEM trusted CA: " + str(ca_count) + " CA saved"
                return render_to_response('cert_import_ca.html', {'cert': cert, 'error': error}, context_instance=RequestContext(request))

            # Store certificate details
            cert.name = str(x509Cert.get_subject())
            cert.status = 'V'
            cert.issuer = str(x509Cert.get_issuer())
            try:
                cert.validfrom = str(x509Cert.get_not_before().get_datetime())
            except Exception as e:
                logger.error("Exception while retrieving validation date 'before' of certificates : ")
                logger.exception(e)
            try:
                cert.validtill = str(x509Cert.get_not_after().get_datetime())
            except Exception as e:
                logger.error("Exception while retrieving validation date 'after' dates of certificates : ")
                logger.exception(e)

            # Find certificate fields
            fields = cert.name.split('/')
            for field in fields:
                tmp = field.split('=')
                if str(tmp[0]) == "CN":
                    cert.cn = tmp[1]
                elif str(tmp[0]) == "C":
                    cert.c = tmp[1]
                elif str(tmp[0]) == "ST":
                    cert.st = tmp[1]
                elif str(tmp[0]) == "L":
                    cert.l = tmp[1]
                elif str(tmp[0]) == "O":
                    cert.o = tmp[1]
                elif str(tmp[0]) == "OU":
                    cert.ou = tmp[1]

            # If the CA doesn't provide a CN, use the user's one
            if not cert.cn and not users_cn:
                error['cn'] = "No CN provided by the user or the CA: " + str(ca_count) + " CA saved"
                return render_to_response('cert_import_ca.html', {'cert': cert, 'error': error}, context_instance=RequestContext(request))
            elif not cert.cn:
                cert.cn = users_cn

            # Save the CA in Mongo
            cert.save()

            # Write the certificate on disk on all nodes
            response = cluster.api_request("/api/certs/write_ca/{}".format(str(cert.id)), {'certificate': cert.cert})
            for node_name in response.keys():
                if response[node_name].get('status') != 1:
                    logger.error(response[node_name].get('error'))

            # Add the saved CA to the count
            ca_count += 1

        os.system("/usr/local/bin/c_rehash /home/vlt-sys/Engine/conf/certs")

        return HttpResponseRedirect('/system/cert/')

    return render_to_response('cert_import_ca.html', {'cert': cert, }, context_instance=RequestContext(request))


@group_required('administrator', 'system_manager')
def sign(request):
    """ method dedicated to sign an external certificate request
    :param request: Django POST request object
    :param POST['csr']: The PEM certificate request
    """
    cert = SSLCertificate()
    cert.cert = ""
    cert.key = ""
    cert.chain = ""
    cert.csr = ""

    if request.method == 'POST':
        dataPosted = request.POST

        error = dict()
        err = None
        try:
            cert.csr = str(dataPosted['csr'])
        except:
            err = True
            error['csr'] = "PEM Certificate request required"
            pass

        if err:
            return render_to_response('cert_sign.html', {'cert': cert, 'error': error}, context_instance=RequestContext(request))

        # Check the request
        try:
            x509Request = X509.load_request_string(cert.csr)
        except:
            error['csr'] = "Invalid PEM Certificate Request"
            return render_to_response('cert_sign.html', {'cert': cert, 'error': error}, context_instance=RequestContext(request))

        # Get cluster
        cluster = Cluster.objects.get()

        # Find the internal CA's certificate and private key
        internal = cluster.ca_certificate
        ca_key = RSA.load_key_string(str(internal.key))
        ca_cert = X509.load_cert_string(str(internal.cert))

        # Get PKI next serial number
        serial = cluster.ca_serial
        serial += 1

        # Create a certificate from the request
        crt = mk_cert(serial)
        crt.set_pubkey(x509Request.get_pubkey())

        pk = EVP.PKey()
        pk.assign_rsa(ca_key)

        issuer = X509.X509_Name()
        subject = X509.X509_Name()

        fields = str(x509Request.get_subject()).split('/')
        for field in fields:
            tmp = field.split('=')
            if str(tmp[0]) == "CN":
                subject.CN = tmp[1]
                cert.cn = tmp[1]
            elif str(tmp[0]) == "C":
                subject.C = tmp[1]
                cert.c = tmp[1]
            elif str(tmp[0]) == "ST":
                subject.ST = tmp[1]
                cert.st = tmp[1]
            elif str(tmp[0]) == "L":
                subject.L = tmp[1]
                cert.l = tmp[1]
            elif str(tmp[0]) == "O":
                subject.O = tmp[1]
                cert.o = tmp[1]
            elif str(tmp[0]) == "OU":
                subject.OU = tmp[1]
                cert.ou = tmp[1]

        fields = str(ca_cert.get_subject()).split('/')
        for field in fields:
            tmp = field.split('=')
            if str(tmp[0]) == "CN":
                issuer.CN = tmp[1]
            elif str(tmp[0]) == "C":
                issuer.C = tmp[1]
            elif str(tmp[0]) == "ST":
                issuer.ST = tmp[1]
            elif str(tmp[0]) == "L":
                issuer.L = tmp[1]
            elif str(tmp[0]) == "O":
                issuer.O = tmp[1]
            elif str(tmp[0]) == "OU":
                issuer.OU = tmp[1]

        crt.set_subject(subject)
        crt.set_issuer(issuer)

        crt.add_ext(X509.new_extension('basicConstraints', 'CA:FALSE'))
        crt.add_ext(X509.new_extension('subjectKeyIdentifier', str(crt.get_fingerprint())))

        try:
            crt.sign(pk, 'sha256')
        except Exception as e:
            print(e)

        # Save serial number
        cluster.ca_serial = serial
        cluster.save()

        # Store the certificate
        cert.cert = crt.as_pem()
        cert.name = str(crt.get_subject())
        cert.status = 'V'
        cert.issuer = str(internal.issuer)
        cert.validfrom = str(crt.get_not_before().get_datetime())
        cert.validtill = str(crt.get_not_after().get_datetime())
        cert.is_ca = False
        cert.chain = str(internal.cert)
        cert.serial = str(serial)
        cert.save()

        return HttpResponseRedirect('/system/cert/')

    return render_to_response('cert_sign.html', {'cert': cert, }, context_instance=RequestContext(request))


@group_required('administrator', 'system_manager')
def create(request):
    """ View dedicated to certificate creation
    :param request: Django request object
    """

    form = CertForm(request.POST or None)

    # Saving information into database and redirect to certificate list
    if request.method == 'POST' and form.is_valid():
        cert = form.save(commit=False)

        # We want to create a Let's Encrypt certificate...
        if request.POST.get("cert-type") == "acme-client":

            # Call acme-client to generate the Let's Encrypt challenge
            proc = subprocess.Popen(['/usr/local/bin/sudo', '-u', 'vlt-sys', '/usr/local/bin/sudo', '/usr/local/bin/sudo',
                                     '/usr/local/sbin/acme.sh', '--issue', '-d', cert.cn, '--webroot', '/home/vlt-sys/Engine/conf',
                                     '--cert-home', '/usr/local/etc/ssl/acme'],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, env={'PATH': "/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin"})
            success, error = proc.communicate()

            if error:
                logger.error("Let's encrypt Error: {}".format(error))
                return render_to_response('cert_create.html', {'form': form, 'error': error}, context_instance=RequestContext(request))
            else:
                logger.info("Let's encrypt certificate was issued for '{}".format(cert.cn))

                """ At this point, the certificate is ondisk: We need to store it into MongoDB """
                proc = subprocess.Popen(['/usr/local/bin/sudo', '-u', 'vlt-sys', '/usr/local/bin/sudo', '/usr/local/bin/sudo',
                                         '/bin/cat', '/usr/local/etc/ssl/acme/{}/{}.key'.format(cert.cn, cert.cn)],
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                private_key, error = proc.communicate()
                if error:
                    logger.error("Let's encrypt Error: Unable to read private key")
                    return render_to_response('cert_create.html', {'form': form, 'error': 'Unable to read private key'}, context_instance=RequestContext(request))

                proc = subprocess.Popen(['/usr/local/bin/sudo', '-u', 'vlt-sys', '/usr/local/bin/sudo', '/usr/local/bin/sudo',
                                         '/bin/cat', '/usr/local/etc/ssl/acme/{}/ca.cer'.format(cert.cn)],
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                ca, error = proc.communicate()
                if error:
                    logger.error("Let's encrypt Error: Unable to read CA")
                    return render_to_response('cert_create.html', {'form': form, 'error': 'Unable to read CA'}, context_instance=RequestContext(request))

                proc = subprocess.Popen(['/usr/local/bin/sudo', '-u', 'vlt-sys', '/usr/local/bin/sudo', '/usr/local/bin/sudo',
                                         '/bin/cat', '/usr/local/etc/ssl/acme/{}/{}.cer'.format(cert.cn, cert.cn)],
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                certificate, error = proc.communicate()
                if error:
                    logger.error("Let's encrypt Error: Unable to read certificate")
                    return render_to_response('cert_create.html', {'form': form, 'error': 'Unable to read certificate'}, context_instance=RequestContext(request))

                # Store the certificate
                x509Cert = X509.load_cert_string(certificate)

                cert.cert = str(certificate.decode('utf8'))
                cert.key = str(private_key.decode('utf8'))
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
                cert.chain = str(ca.decode('utf8'))
                cert.save()

                return HttpResponseRedirect('/system/cert/')

        # Get PKI next serial number
        cluster = Cluster.objects.get()
        serial = cluster.ca_serial
        serial = serial + 1

        # Create a certificate
        ca_cert_file = get_ca_cert_path()
        ca_key_file = get_ca_key_path()

        crt, pk2 = mk_signed_cert(ca_cert_file, ca_key_file, cert.cn, cert.c, cert.st, cert.l, cert.o, cert.ou, serial)

        # Save serial number
        cluster.ca_serial = serial
        cluster.save()

        internal = cluster.ca_certificate

        # Store the certificate
        cert.cert = crt.as_pem().decode('utf8')
        cert.key = pk2.as_pem(cipher=None).decode('utf8')
        cert.name = str(crt.get_subject())
        cert.status = 'V'
        cert.issuer = str(internal.issuer)
        cert.validfrom = str(crt.get_not_before().get_datetime())
        cert.validtill = str(crt.get_not_after().get_datetime())
        cert.is_ca = False
        cert.serial = str(serial)
        cert.chain = str(internal.cert)
        cert.save()

        return HttpResponseRedirect('/system/cert/')

    return render_to_response('cert_create.html', {'form': form, }, context_instance=RequestContext(request))
