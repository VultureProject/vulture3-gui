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
__author__ = "Kevin Guillemot"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = 'Django views dedicated to Vulture log management'


# System imports
from os                         import chmod as os_chmod, system as os_system, remove as os_remove

# Django system imports
from django.conf                import settings
from django.http                import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# Django project imports
from gui.models.ssl_certificate import SSLCertificate

# Extern modules imports
from bson.objectid              import ObjectId
from json                       import loads as json_loads

# Required exceptions imports


# Logger configuration imports
import logging
import logging.config
logger = logging.getLogger('cluster')


# Global variables
certs_dir = "/home/vlt-sys/Engine/conf/certs"


@csrf_exempt
def write_ca(request, cert_id):
    """ Function called when a new Trusted CA certificate is imported.
     It will write-it on disk.

    :param request: Django request object
    :param cert_id: String id of certificate to write on disk
    :return:
    """

    try:
        certificate = SSLCertificate(ObjectId(cert_id))
    except Exception as e:
        logger.error("API::write_ca: CA Certificate '{}' not found : {}".format(cert_id, e))
        return JsonResponse({'status': 0, 'error': "CA Certificate '{}' not found : {}".format(cert_id, str(e))})

    try:
        cert_content = json_loads(request.body)['certificate']
    except Exception as e:
        logger.error("API::write_ca: CA certificate content not found in api request : {}".format(str(e)))
        return JsonResponse({'status': 0, 'error': "CA certificate content null : {}".format(str(e))})

    # Write the certificate on disk
    certificate_path = "{}/{}.crt".format(certs_dir, str(cert_id))
    try:
        with open(certificate_path, "w") as certificate_fd:
            certificate_fd.write(str(cert_content))
    except Exception as e:
        logger.error("API::write_ca: Cannot write CA certificate '{}' on disk : {}".format(certificate_path, e))
        return JsonResponse({'status': 0, 'error': "Cannot write CA certificate '{}' on disk : {}".format(certificate_path, str(e))})

    # Set permissions
    try:
        os_chmod(certificate_path, 664)
        os_system("/usr/bin/chgrp vlt-web {}".format(certificate_path))
    except Exception as e:
        logger.error("API::write_ca: Failed to set permissions on '{}' file : {}".format(certificate_path, str(e)))

    os_system("/usr/local/bin/c_rehash /home/vlt-sys/Engine/conf/certs")
    logger.info("API::write_ca: Ca certificate successfully written on disk")

    return JsonResponse({'status': 1})


def remove_ca(request, cert_id):
    """ Function called when a Trusted CA certificate is deleted.
     It will erase-it on disk.

    :param request: Django request object
    :param cert_id: String id of certificate to erase
    :return:
    """

    try:
        certificate = SSLCertificate(ObjectId(cert_id))
    except Exception as e:
        logger.error("API::remove_ca: CA Certificate '{}' not found : {}".format(cert_id, e))
        return JsonResponse({'status': 0, 'error': "CA Certificate '{}' not found : {}".format(cert_id, str(e))})

    # Delete the certificate on disk
    certificate_path = "{}/{}.crt".format(certs_dir, str(cert_id))
    try:
        os_remove(certificate_path)
    except Exception as e:
        logger.error("API::remove_ca: Failed to delete certificate '{}' on disk : {}".format(certificate_path, str(e)))

    os_system("/usr/local/bin/c_rehash /home/vlt-sys/Engine/conf/certs")
    logger.info("API::remove_ca: Ca certificate successfully deleted on disk")

    return JsonResponse({'status': 1})


def remove_cert(request, cert_id):
    """ Function called when a certificate is deleted.
     It will erase-it on disk.

    :param request: Django request object
    :param cert_id: String id of certificate to erase
    :return:
    """

    try:
        certificate = SSLCertificate(ObjectId(cert_id))
    except Exception as e:
        logger.error("API::delete_cert: SSL Certificate '{}' not found : {}".format(cert_id, e))
        return JsonResponse({'status': 0, 'error': "SSL Certificate '{}' not found : {}".format(cert_id, str(e))})

    # Delete all the declinaisons of files of that certificate on disk
    if certificate.cert and certificate.key:
        certificate_path = "{}SSLProxyCertificateFile-{}.txt".format(settings.CONF_DIR, cert_id)
        try:
            os_remove(certificate_path)
        except Exception as e:
            logger.error("API::remove_cert: Failed to delete file '{}' on disk : {}".format(certificate_path, str(e)))

    if certificate.cert:
        certificate_path = "{}SSLCertificateFile-{}.txt".format(settings.CONF_DIR, cert_id)
        try:
            os_remove(certificate_path)
        except Exception as e:
            logger.error("API::remove_cert: Failed to delete file '{}' on disk : {}".format(certificate_path, str(e)))

    if certificate.key:
        certificate_path = "{}SSLCertificateKeyFile-{}.txt".format(settings.CONF_DIR, cert_id)
        try:
            os_remove(certificate_path)
        except Exception as e:
            logger.error("API::remove_cert: Failed to delete file '{}' on disk : {}".format(certificate_path, str(e)))

    logger.info("API::remove_cert: SSL certificate successfully deleted on disk")

    return JsonResponse({'status': 1})

