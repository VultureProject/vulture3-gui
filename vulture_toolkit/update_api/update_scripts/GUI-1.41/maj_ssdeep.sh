#!/bin/sh
#
# This migration script install ssdeep
#
#

. /etc/rc.conf

if [ "$http_proxy" != "" ]
then
    export https_proxy="http://$http_proxy"
    export http_proxy="http://$http_proxy"
fi

#Remove compilators from vulture
/usr/bin/env ASSUME_ALWAYS_YES=YES pkg install ssdeep 2> /dev/null