#!/bin/sh

/bin/echo '#!/usr/bin/env /home/vlt-gui/env/bin/python2.7
# -*- coding: utf-8 -*-
from __future__ import print_function

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
__doc__ = ""
import sys

nb_args = len(sys.argv)
if nb_args == 3:
    filename = sys.argv[1]
    content = sys.argv[2]
    allowed_files = ("/etc/resolv.conf",
                     "/etc/ntp.conf",
                     "/etc/mail/mailer.conf",
                     "/usr/local/etc/ssmtp/ssmtp.conf",
                     "/usr/local/etc/fluentd/fluent.conf",
                     "/usr/local/etc/redis.conf",
                     "/usr/local/etc/pf.conf",
                     "/usr/local/etc/sentinel.conf",
                     "/usr/local/etc/logrotate.d/vulture.conf",
                     "/usr/local/etc/vlthaproxy.conf",
                     "/etc/rc.conf.local",
                     "/etc/krb5.conf",
                     "/usr/local/etc/rsyslog.d/rsyslog.conf",
                     "/usr/local/etc/loganalyzer.json",
                     "/home/vlt-sys/Engine/conf/gui-httpd.conf",
                     "/home/vlt-sys/Engine/conf/portal-httpd.conf",
                     "/usr/local/etc/ipsec.conf",
                     "/usr/local/etc/ipsec.secrets",
                     "/usr/local/etc/strongswan.conf"
    )
    # Testing IP Address validity
    if filename in allowed_files:
        f = open(filename, "w")
        f.write(content)
        f.close()
    else:
        print("NOT ALLOWED", file=sys.stderr)
        sys.exit(2)
else:
    print("ARGS ERROR", file=sys.stderr)
    sys.exit(2)' > /home/vlt-sys/scripts/write_configuration_file

/bin/echo "Installing Strongswan package"

. /etc/rc.conf

if [ "$http_proxy" != "" ]
then
    export https_proxy="http://$http_proxy"
    export http_proxy="http://$http_proxy"
fi

/usr/bin/env ASSUME_ALWAYS_YES=YES /usr/sbin/pkg install strongswan


    

