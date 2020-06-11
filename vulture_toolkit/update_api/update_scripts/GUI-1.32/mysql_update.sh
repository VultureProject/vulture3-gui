#!/bin/sh
#
# This migration script update msql-client from v56 to v57
#
#

. /etc/rc.conf

if [ "$http_proxy" != "" ]
then
    export https_proxy="http://$http_proxy"
    export http_proxy="http://$http_proxy"
fi

/bin/echo "[+] Updating mysql-client..."

if [ $(/usr/bin/whoami) = "root" ]
then
    /usr/bin/env ASSUME_ALWAYS_YES=YES /usr/sbin/pkg update
    /usr/bin/env ASSUME_ALWAYS_YES=YES /usr/sbin/pkg remove mysql56-client
    /usr/bin/env ASSUME_ALWAYS_YES=YES /usr/sbin/pkg install mysql57-client
    /bin/echo "[*] Update of mysql-client ended successfully"
else
    /bin/echo "[/] You are not authorized to execute that file : only root can."
fi
