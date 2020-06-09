#!/bin/sh
#
# This migration script update openssl
#
#

. /etc/rc.conf

if [ "$http_proxy" != "" ]
then
    export https_proxy="http://$http_proxy"
    export http_proxy="http://$http_proxy"
fi

/bin/echo "[+] Updating redis..."

if [ $(/usr/bin/whoami) = "root" ]
then

    service sentinel stop
    service redis stop

    /usr/bin/env ASSUME_ALWAYS_YES=YES /usr/sbin/pkg update
    /usr/bin/env ASSUME_ALWAYS_YES=YES /usr/sbin/pkg upgrade redis

    /bin/echo "
# Disable the protected mode to permit connection from the non-loopback interfaces
protected-mode no" >> /usr/local/etc/redis.conf

    /bin/echo "--- /usr/local/etc/sentinel.conf	2016-11-17 14:08:30.264485792 +0100
+++ /usr/local/etc/sentinel.conf	2016-11-17 14:04:58.548489224 +0100
@@ -21,6 +21,9 @@
 # General options #
 ###################

+# Disable the protected mode to permit connection from the non-loopback interfaces
+protected-mode no
+
 # Run as daemon
 daemonize yes
 pidfile /var/run/redis/sentinel.pid
" | patch /usr/local/etc/sentinel.conf

    /usr/sbin/chown redis:redis /usr/local/etc/redis.conf
    /usr/sbin/chown redis:redis /usr/local/etc/sentinel.conf

    service redis start
    service sentinel start

    /bin/echo "[*] Update of redis ended successfully"
else
    /bin/echo "[/] You are not authorized to execute that file : only root can."
fi