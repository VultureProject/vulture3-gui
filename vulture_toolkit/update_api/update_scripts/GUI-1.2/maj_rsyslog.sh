#!/bin/sh
#
# This script create a path required by rsyslog
#
#
DIR="/usr/local/etc/rsyslog.d"

/bin/echo "[+] Creating '$DIR' directory ..."

if [ $(/usr/bin/whoami) = "root" ]
then
    /bin/mkdir $DIR
    /bin/echo "[*] Installation ended successfully."
else
    /bin/echo "[/] You are not authorized to execute that file : only root can."
fi
