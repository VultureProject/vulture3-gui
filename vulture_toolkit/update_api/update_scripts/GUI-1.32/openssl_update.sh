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

/bin/echo "[+] Updating openssl..."

if [ $(/usr/bin/whoami) = "root" ]
then
    /usr/bin/env ASSUME_ALWAYS_YES=YES /usr/sbin/pkg update
    /usr/bin/env ASSUME_ALWAYS_YES=YES /usr/sbin/pkg upgrade openssl
    /bin/echo "[*] Update of openssl ended successfully"
else
    /bin/echo "[/] You are not authorized to execute that file : only root can."
fi
