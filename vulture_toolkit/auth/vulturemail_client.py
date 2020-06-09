#!/usr/bin/python
#-*- coding: utf-8 -*-
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
__doc__ = ''

# Logger configuration
import logging
#logging.config.dictConfig(settings.LOG_SETTINGS)
logger = logging.getLogger('portal_authentication')

import smtplib
from email.mime.text import MIMEText
from django.utils.crypto import get_random_string

from .base_auth import BaseAuth
from gui.models.system_settings import Cluster



class VultureMailClient(BaseAuth):
    def __init__(self, settings):
        """ Instantiation method

        :param settings:
        :return:
        """
        # Connection settings
        self.type = settings.otp_type
        self.mail_service = settings.otp_mail_service
        self.key_length = settings.key_length


    def authenticate(self, user_id, key):
        raise NotImplemented('Simple compareason does not require a function')


    def register_authentication(self, sender, recipient):
        chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        secret_key = get_random_string(self.key_length, chars)

        msg            = MIMEText("Vulture authentication\r\nThis is your secret key: {}".format(secret_key))
        msg['Subject'] = 'Vulture OTP Authentication'
        msg['From']    = sender
        msg['To']      = recipient

        cluster = Cluster.objects.get()
        node = cluster.get_current_node()
        smtp_settings = getattr(node.system_settings, 'smtp_settings')
        if not smtp_settings:
            """ Not found, use cluster settings for configuration """
            smtp_settings = getattr(cluster.system_settings, 'smtp_settings')

        if not smtp_settings:
            logger.error("VultureMailClient::register_authentication: Cluster and Node SMTP settings not configured")
            raise smtplib.SMTPException("Vulture mail service not configured")

        server = smtplib.SMTP(smtp_settings.smtp_server)
        message = "Subject: " + unicode (msg['Subject']) + "\n\n" + unicode (msg)
        server.sendmail(msg['from'], recipient, message)
        server.quit()

        return secret_key