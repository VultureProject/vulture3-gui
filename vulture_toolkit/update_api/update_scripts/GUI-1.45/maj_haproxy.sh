#!/bin/sh

/bin/echo "Stopping haproxy"
service haproxy stop

/bin/rm /var/run/haproxy.pid

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
                     "/home/vlt-sys/Engine/conf/portal-httpd.conf"
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
    

/bin/echo '#!/bin/sh
#
#

# PROVIDE: vlthaproxy
# REQUIRE: NETWORK
# KEYWORD: shutdown

. /etc/rc.subr

name="vlthaproxy"
rcvar=vlthaproxy_enable
rc_startmsgs="YES"

pidfile="/var/run/${name}.pid"
conf="/usr/local/etc/${name}.conf"

# read configuration and set defaults
load_rc_config "$name"
: ${vlthaproxy_enable="YES"}

start_cmd="vlthaproxy_start"
stop_cmd="vlthaproxy_stop"
status_cmd="vlthaproxy_status"


vlthaproxy_start()
{
    if ! [ -s ${pidfile} ]; then
        /usr/local/sbin/haproxy -p ${pidfile} -f ${conf} -D
        return 0
    fi

    echo "vlthaproxy is already running"
}

vlthaproxy_stop()
{
    if ! [ -s ${pidfile} ]; then
        echo "vlthaproxy is not running"
        return 0
    fi

    kill -SIGTERM `cat ${pidfile}`
    /bin/rm ${pidfile}
}

vlthaproxy_status()
{
    if ! [ -s ${pidfile} ]; then
        echo "vlthaproxy is not running"
        return 0
    fi

    pid=`cat ${pidfile} 2>/dev/null || echo 0` 

    if [ "$pid" -le 0 ]; then
        echo "vlthaproxy is not running."
        return 0
    fi

    ps aux | grep ${pid} | grep haproxy 2>/dev/null >/dev/null
    if [ "$?" -ne 0 ]; then
        echo "vlthaproxy is not running."
        return 0
    fi

    echo "vlthaproxy is running."
    return 1
}   

run_rc_command "$*"' > /usr/local/etc/rc.d/vlthaproxy

/bin/chmod +x /usr/local/etc/rc.d/vlthaproxy
/bin/mv /usr/local/etc/haproxy.conf /usr/local/etc/vlthaproxy.conf

/usr/bin/sed -i '' 's/haproxy_enable="YES"/vlthaproxy_enable="YES"/g' /etc/rc.conf.local

/bin/echo "Starting vlthaproxy"
service vlthaproxy start