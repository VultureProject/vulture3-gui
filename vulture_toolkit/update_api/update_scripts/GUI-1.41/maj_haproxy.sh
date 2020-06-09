#!/bin/sh
#
# This script install haproxy and uninstall fail2ban
#
#

. /etc/rc.conf

if [ "$http_proxy" != "" ]
then
    export https_proxy="http://$http_proxy"
    export http_proxy="http://$http_proxy"
fi


/bin/echo "[+] Installing haproxy..."

if [ $(/usr/bin/whoami) = "root" ]; then
    /usr/bin/env ASSUME_ALWAYS_YES=YES /usr/sbin/pkg install haproxy
    /usr/bin/env ASSUME_ALWAYS_YES=YES /usr/sbin/pkg remove py27-fail2ban
fi

/usr/sbin/pw useradd haproxy
/usr/bin/touch /usr/local/etc/haproxy.conf
/bin/chmod 644 /usr/local/etc/haproxy.conf


/bin/echo '#!/bin/sh
#
#

# PROVIDE: haproxy
# REQUIRE: NETWORK
# KEYWORD: shutdown

. /etc/rc.subr

name="haproxy"
rcvar=haproxy_enable
rc_startmsgs="YES"

command="/usr/sbin/daemon"
pidfile="/var/run/${name}.pid"
conf="/usr/local/etc/${name}.conf"
binary="/usr/local/sbin/haproxy -sf -q -f ${conf}"
command_args="-p ${pidfile} -c ${binary}"

# read configuration and set defaults
load_rc_config "$name"
: ${haproxy_enable="YES"}

start_cmd="haproxy_start"
stop_cmd="haproxy_stop"
status_cmd="haproxy_status"


haproxy_start()
{
	cmd="${command} ${command_args}"
	eval ${cmd}
}

haproxy_stop()
{
	if ! [ -s ${pidfile} ]; then
		echo "haproxy is not running"
		return 0
	fi

	kill -SIGTERM `cat ${pidfile}`
}

haproxy_status()
{
	if ! [ -s ${pidfile} ]; then
		echo "haproxy is not running"
		return 0
	fi

	pid=`cat ${pidfile} 2>/dev/null || echo 0` 

	if [ "$pid" -le 0 ]; then
		echo "haproxy is not running."
		return 0
	fi

	ps aux | grep ${pid} | grep haproxy 2>/dev/null >/dev/null
	if [ "$?" -ne 0 ]; then
		echo "haproxy is not running."
		return 0
	fi

	echo "haproxy is running."
	return 1
}	

run_rc_command "$*"' > /usr/local/etc/rc.d/haproxy