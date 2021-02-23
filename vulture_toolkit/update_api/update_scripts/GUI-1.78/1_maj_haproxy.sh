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

/usr/sbin/pkg upgrade -y haproxy || echo "[!] Failed to upgrade HAProxy - Please do this manually using 'pkg upgrade -y haproxy'"
