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
__doc__ = 'Django models dedicated to workers'

import re

from django.utils.translation import ugettext_lazy as _
from mongoengine import BooleanField, DynamicDocument, IntField, StringField


class Worker(DynamicDocument):
    """ Vulture Apache Worker model representation
    name: A friendly name for the application
    ratelimit: The maximum rate for this application, in kb/s
    req_timeout_header: Timeout for receiving request headers, in seconds
    req_timeout_body: Timeout for receiving request body, in seconds
    req_timeout_header_rate: Minimum rate for request headers, in bytes. This increases the timeout by 1 second for every x bytes received.
    req_timeout_body_rate: Minimum rate for request body, in bytes. This increases the timeout by 1 second for every x bytes received.
    timeout: Number of seconds Apache will wait before considering a request is failed
    keepalive: Transmit multiple HTTP requests through the same TCP connection
    maxkeepaliverequests: Number of authorized HTTP requests per TCP connexion
    keepalivetimeout: Number of seconds Apache will wait before closing the keepalive connection

    """

    ON_OFF = (
        ('on', 'On'),
        ('off', 'Off'),
    )

    name = StringField(required=True,help_text=_('Friendly name to reference the worker'))

    gracefulshutdowntimeout = IntField(required=True,default=0,help_text=_('Number of seconds to wait before killing the worker after a graceful-stop. Set to "0" to stop worker when all current requests have been processed.'))
    maxconnectionsperchild = IntField(required=True,default=1024,help_text=_('Maximum number of connections for a child process. Set to "0" for unlimited.'))

    minsparethreads = IntField(required=True,default=75,help_text=_('Minimum number of inactive threads'))
    maxsparethreads = IntField(required=True,default=250,help_text=_('Maximum number of inactive threads'))

    serverlimit = IntField(required=True,default=16,help_text=_('Maximum number of server process'))
    threadsperchild = IntField(required=True,default=25,help_text=_('Number of threads for a child'))
    rate_limit = StringField(required=True, default="0", help_text=_('Limit the client bandwith to this value in KiB/s. Zero means "unlimited".'))
    req_timeout_header = StringField(required=True, default="20-40", help_text=_('Timeout for receiving request headers, in seconds'))
    req_timeout_body = StringField(required=True, default="20", help_text=_('Timeout for receiving request body, in seconds'))
    req_timeout_header_rate = StringField(required=True, default="500", help_text=_('Minimum rate for request headers, in bytes. This increases the timeout by 1 second for every x bytes received.'))
    req_timeout_body_rate = StringField(required=True, default="500", help_text=_('Minimum rate for request body, in bytes. This increases the timeout by 1 second for every x bytes received.'))

    timeout = StringField(required=True, default="60", help_text=_('Number of seconds Apache will wait before considering a request is failed'))
    keepalive = StringField(required=True, default='on', choices=ON_OFF,help_text=_('Transmit multiple HTTP requests through the same TCP connection'))
    maxkeepaliverequests = StringField(required=True, default="500", help_text=_('Number of authorized HTTP requests per TCP connexion'))
    keepalivetimeout = StringField(required=True, default="5", help_text=_('Number of seconds Apache will wait before closing the keepalive connection'))


    h2direct = BooleanField(required=False, default=False, help_text=_('H2 Direct Protocol Switch'))
    h2maxsessionstreams = StringField(required=False, default="100", help_text=_('Maximum number of open streams per session'))
    h2maxworkeridleseconds = StringField(required=False, default="600", help_text=_('Maximum number of seconds h2 workers remain idle until shut down'))
    h2minworkers = StringField(required=False, default="16", help_text=_('Minimum number of worker threads per child'))
    h2maxworkers = StringField(required=False, default="32", help_text=_('Maximum number of worker threads per child'))
    h2moderntlsonly = BooleanField(required=False, default=True, help_text=_('Require HTTP/2 connections to be "modern TLS" only'))
    h2push = BooleanField(required=False, default=True, help_text=_('H2 Server Push Switch'))
    h2pushpriority = StringField(required=False, default="#mime-type [after|before|interleaved] [weight]\n* after\ntext/css before\nimage/jpeg after 32\nimage/png after 32\napplication/javascript interleaved", help_text=_('H2 Server Push Priority'))
    h2serializeheaders = BooleanField(required=False, default=False, help_text=_('Serialize Request/Response Processing Switch'))
    h2streammaxmemsize = StringField(required=False, default="65536", help_text=_('Maximum number of bytes buffered in memory for a stream'))
    h2tlscooldownsecs = StringField(required=False, default="1", help_text=_('Sets the number of seconds of idle time on a TLS connection'))
    h2tlswarmupsize = StringField(required=False, default="1048576", help_text=_('Sets the number of bytes to be sent in small TLS records'))
    h2upgrade = BooleanField(required=False, default=True, help_text=_('H2 Upgrade Protocol Switch'))
    h2windowsize = StringField(required=False, default="65536", help_text=_('Size of Stream Window for upstream data'))


    # Maximum number of concurrent requests
    # Must be = serverlimit x threadlimit
    def getMaxRequestWorkers(self):
        return  int(self.serverlimit) * int(self.threadsperchild)

    def getThreadLimit(self):
        return self.threadsperchild #FIXME ???

    """Returns rate configuration or None, if there is a valid rate-limit defined """
    def get_rate_limit (self):
        if self.rate_limit and self.rate_limit != 0:
            return self.rate_limit
        return None

    """Returns timeout configuration or None, if there is a valid req_timeout configuration """
    def get_req_timeout (self):
        ret=""
        if self.req_timeout_header:
            ret = ret + "header=" + str(self.req_timeout_header)
            if self.req_timeout_header_rate and self.req_timeout_header_rate != 0 and self.req_timeout_header_rate != "":
                ret = ret + ",MinRate="+str(self.req_timeout_header_rate)
        if self.req_timeout_body:
            ret = ret + " body=" + str(self.req_timeout_body)
            if self.req_timeout_body_rate and self.req_timeout_body_rate != 0 and self.req_timeout_body_rate != "":
                ret = ret + str(",MinRate=") + str(self.req_timeout_body_rate)

        if ret == "":
            return None
        return ret

    """Returns HTTP/2 configuration"""
    def get_h2_config (self):

        str = ""
        if (self.h2direct):
            str = str + 'H2Direct ' +'on' + '\n'
        else :
            str = str + 'H2Direct ' +'off' + '\n'
        str = str + 'H2MaxSessionStreams ' + self.h2maxsessionstreams + '\n'
        str = str + 'H2MaxWorkerIdleSeconds ' + self.h2maxworkeridleseconds + '\n'
        str = str + 'H2MinWorkers ' + self.h2minworkers + '\n'
        str = str + 'H2MaxWorkers ' + self.h2maxworkers + '\n'
        if (self.h2moderntlsonly):
            str = str + 'H2ModernTLSOnly ' +'on' + '\n'
        else :
            str = str + 'H2ModernTLSOnly ' +'off' + '\n'
        if (self.h2push):
            str = str + 'H2Push ' +'on' + '\n'
        else :
            str = str + 'H2Push ' +'off' + '\n'
        if (self.h2push):
            strpp = []
            lines=self.h2pushpriority.split("\n")
            for line in lines:
                if not line.strip().startswith('#'):
                    p=re.compile('([a-zA-Z\/\*-]+)\s*([a-zA-Z]+)?\s*([0-9]+)?')
                    m=p.match(line)
                    if m is not None:
                        dir = m.group(1)
                        if m.group(2):
                            dir = dir + ' ' + m.group(2)
                        if m.group(3):
                            dir = dir + ' ' + m.group(3)
                        strpp.append(dir)
            for element in strpp :
                str = str + 'H2PushPriority ' +element + '\n'
        if (self.h2serializeheaders):
            str = str + 'H2SerializeHeaders ' +'on' + '\n'
        else :
            str = str + 'H2SerializeHeaders ' +'off' + '\n'
        str = str + 'H2StreamMaxMemSize ' + self.h2streammaxmemsize + '\n'
        str = str + 'H2TLSCoolDownSecs ' + self.h2tlscooldownsecs + '\n'
        str = str + 'H2TLSWarmUpSize ' + self.h2tlswarmupsize + '\n'
        if (self.h2upgrade):
            str = str + 'H2Upgrade ' +'on' + '\n'
        else :
            str = str + 'H2Upgrade ' +'off' + '\n'
        str = str + 'H2WindowSize ' + self.h2windowsize + '\n'
        return str





    def __str__(self):
        return self.name



