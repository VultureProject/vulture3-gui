#!/bin/sh
#
# This migration script install yajl - Used by Vulture-Engine-2.4.39-66 min
#

# If this script is not ran as root
if [ $(/usr/bin/whoami) != "root" ]; then
    # Echo error message in stderr
    /bin/echo "[/] This script must be run as root" >&2
fi

# Get global variables in rc conf
. /etc/rc.conf

# If there is a proxy
if [ "$http_proxy" != "" ]
then
    # Modify format of http(s)_proxy variables, for pkg and wget
    export https_proxy="http://$http_proxy"
    export http_proxy="http://$http_proxy"
fi

/bin/echo -n "[+] Installing YAJL package ..."

if ! /usr/sbin/pkg install -y yajl && echo "OK" ; then
    echo "[!] Something went wrong when trying to install yajl. You can do it by yourself with : "
    echo "/usr/sbin/pkg install -y yajl"
fi

echo "[+] Install of yajl ended."
