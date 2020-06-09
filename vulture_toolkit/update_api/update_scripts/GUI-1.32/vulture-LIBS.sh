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

/bin/echo "[+] Updating Vulture-LIBS..."

rm -f /tmp/Vulture-LIBS.tar.gz
rm -f /tmp/Vulture-LIBS-11.tar.gz

version=$(freebsd-version | grep -c 11)

if [ $version -eq 1 ]; then
    /usr/local/bin/wget --no-check-certificate https://dl.vultureproject.org/11.0/Vulture-LIBS.tar.gz >>/tmp/installation.log 2>&1
    cd /home/vlt-gui
    tar xf /tmp/Vulture-LIBS.tar.gz
    chown -R vlt-gui:vlt-gui /home/vlt-gui/
    /bin/echo "[*] Update of Vulture-LIBS ended successfully"

else
    /usr/local/bin/wget --no-check-certificate https://dl.vultureproject.org/10.3/Vulture-LIBS.tar.gz >>/tmp/installation.log 2>&1
    cd /home/vlt-gui
    tar xf /tmp/Vulture-LIBS.tar.gz
    chown -R vlt-gui:vlt-gui /home/vlt-gui/
    /bin/echo "[*] Update of Vulture-LIBS ended successfully"

fi

