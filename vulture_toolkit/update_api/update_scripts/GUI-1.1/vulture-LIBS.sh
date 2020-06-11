#!/bin/sh
#
# This migration script install newest Vulture-LIBS package
#
#

. /etc/rc.conf

cd /tmp

if [ "$http_proxy" != "" ]
then
    export https_proxy="http://$http_proxy"
    export http_proxy="http://$http_proxy"
fi

ASSUME_ALWAYS_YES=YES /usr/sbin/pkg install lapack >>/tmp/installation.log 2>&1
ASSUME_ALWAYS_YES=YES /usr/sbin/pkg install libpqtypes >>/tmp/installation.log 2>&1

rm -f /tmp/Vulture-LIBS.tar.gz
/usr/local/bin/wget --no-check-certificate https://dl.vultureproject.org/Vulture-LIBS.tar.gz >>/tmp/installation.log 2>&1
cd /home/vlt-gui
tar xf /tmp/Vulture-LIBS.tar.gz
chown -R vlt-gui:vlt-gui /home/vlt-gui/
