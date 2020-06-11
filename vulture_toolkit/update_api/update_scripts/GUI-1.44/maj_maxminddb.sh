#!/bin/sh
#
# This migration script install maxminddb
#
#

. /etc/rc.conf

/bin/echo "[+] Installing maxminddb python module ..."

if [ $(/usr/bin/whoami) = "root" ]
then
    if [ "$http_proxy" != "" ]
    then
        export https_proxy="http://$http_proxy"
        export http_proxy="http://$http_proxy"
    fi
    /home/vlt-gui/env/bin/pip install maxminddb

    /bin/echo "[*] Installation ended successfully."
else
    /bin/echo "[/] You are not authorized to execute that file : only root can."
fi
