#!/bin/sh
#
# This migration script install newest Vulture-LIBS package
#
#

. /etc/rc.conf

if [ "$http_proxy" != "" ]
then
    export https_proxy="http://$http_proxy"
    export http_proxy="http://$http_proxy"
fi

service rsyslogd stop
/usr/bin/env ASSUME_ALWAYS_YES=YES pkg remove rsyslog 2> /dev/null
/usr/bin/env ASSUME_ALWAYS_YES=YES pkg remove ruby 2> /dev/null
/usr/bin/env ASSUME_ALWAYS_YES=YES pkg install mongo-c-driver 2> /dev/null

cd /tmp

/bin/echo "[+] Updating Vulture-LIBS..."
/bin/rm -f /tmp/Vulture-LIBS.tar.gz

/usr/local/bin/wget --no-check-certificate https://dl.vultureproject.org/11.0/Vulture-LIBS.tar.gz >>/tmp/installation.log 2>&1

cd /home/vlt-gui
/usr/bin/tar xf /tmp/Vulture-LIBS.tar.gz
/usr/sbin/chown -R vlt-gui:vlt-gui /home/vlt-gui/
/bin/sh /home/vlt-gui/lib-11.0/install.sh

/bin/echo "[*] Update of Vulture-LIBS ended successfully"

/bin/echo "[+] Updating rsyslog..."

/bin/echo '#!/bin/sh
#
# $FreeBSD: branches/2017Q2/sysutils/rsyslog8/files/rsyslogd.in 340872 2014-01-24 00:14:07Z mat $
#


# PROVIDE: rsyslogd
# REQUIRE: mountcritremote cleanvar newsyslog ldconfig
# BEFORE:  SERVERS

. /etc/rc.subr

name=rsyslogd
rcvar=rsyslogd_enable
command="/usr/local/sbin/${name}"
load_rc_config $name
: ${rsyslogd_enable:="NO"}
: ${rsyslogd_pidfile:="/var/run/rsyslogd.pid"}
: ${rsyslogd_config:="/usr/local/etc/rsyslog.conf"}
pidfile="${rsyslogd_pidfile}"
command_args="-i ${pidfile} -f ${rsyslogd_config}"
required_files="${rsyslogd_config}"
extra_commands="reload"

run_rc_command "$1"' > /usr/local/etc/rc.d/rsyslogd
chmod 555 /usr/local/etc/rc.d/rsyslogd

/bin/echo "[*] Rsyslogd update ended successfully"