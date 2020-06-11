#!/bin/sh
#
# This migration script install kerberos
#
#
. /etc/rc.conf

proxy=""
if [ "$http_proxy" != "" ]
then
    env ASSUME_ALWAYS_YES=YES http_proxy="http://$http_proxy" /usr/sbin/pkg install krb5
    /home/vlt-gui/env/bin/pip2.7 --proxy="http://$http_proxy" install --global-option=build_ext --global-option="-I/usr/local/include" kerberos
else
    env ASSUME_ALWAYS_YES=YES /usr/sbin/pkg install krb5
    /home/vlt-gui/env/bin/pip2.7 install --global-option=build_ext --global-option="-I/usr/local/include" kerberos
fi
