#!/bin/sh
#
# This migration script upgrades Vulture's package
#
#

. /etc/rc.conf

if [ "$http_proxy" != "" ]
then
    env ASSUME_ALWAYS_YES=YES http_proxy="http://$http_proxy" pkg install lua53
else
    env ASSUME_ALWAYS_YES=YES pkg install lua53
fi
