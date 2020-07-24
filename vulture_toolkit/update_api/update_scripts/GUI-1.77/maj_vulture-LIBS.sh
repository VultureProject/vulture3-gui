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

/bin/echo "[+] Updating Vulture-LIBS from branch \"$1\"..."
/bin/rm -f /tmp/Vulture-LIBS.tar.gz

bsd_version=$(/usr/bin/uname -r | /usr/bin/cut -d '-' -f 1)
url="https://dl.vultureproject.org/$bsd_version$1/Vulture-LIBS.tar.gz"

/bin/echo -n "[+] Downloading from '$url' ..."
/usr/local/bin/wget --no-check-certificate $url >>/tmp/installation.log 2>&1
/bin/echo "DONE"

cd /home/vlt-gui
/bin/rm -rf ./env
/usr/bin/tar xf /tmp/Vulture-LIBS.tar.gz
/usr/sbin/chown -R vlt-gui:vlt-gui /home/vlt-gui/

/bin/echo -n "[+] Installing Vulture libraries ..."
/bin/sh "/home/vlt-gui/lib-$bsd_version/install.sh"
/bin/echo "OK"

/bin/echo "[+] Installing required libraries for Images ..."
/usr/sbin/pkg install -y libxcb && echo "OK" || (echo "KO" && echo "[!] Please install following packages manually : libxcb")

/bin/echo "[*] Update of Vulture-LIBS ended"

