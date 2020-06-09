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

cd /tmp

/bin/echo "[+] Removing Python2 packages ..."
/usr/sbin/pkg remove -y py27-setuptools py27-sqlite3 py27-kerberos

/bin/echo -n "[+] Installing Python3 packages ..."
/usr/sbin/pkg install -y python37 py37-setuptools py37-sqlite3 py37-kerberos openmp && echo "OK" || (echo "KO" && echo "[!] Please install following packages manually : python37 py37-setuptools py37-sqlite3 py37-kerberos openmp")

/bin/echo "[*] Upgrade of Python3 packages done."
