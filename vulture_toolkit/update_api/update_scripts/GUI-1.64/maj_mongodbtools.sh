#!/bin/sh
#
# This migration script install mongodb32-tools package
#
#
/bin/echo "[*] Installing MongoDB tools package"

. /etc/rc.conf

if [ "$http_proxy" != "" ]
then
    export https_proxy="http://$http_proxy"
    export http_proxy="http://$http_proxy"
fi

/usr/bin/env ASSUME_ALWAYS_YES=YES /usr/sbin/pkg install mongodb32-tools

/bin/echo "[*] MongoDB tools successfully installed"
