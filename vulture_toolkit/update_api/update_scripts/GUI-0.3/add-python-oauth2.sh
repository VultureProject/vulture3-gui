#!/bin/sh
#
# This migration script install python-oauth2
#
#
. /etc/rc.conf

if [ "$http_proxy" != "" ]
then
    export https_proxy="http://$http_proxy"
    export http_proxy="http://$http_proxy"
fi

/home/vlt-gui/env/bin/pip2.7 install python-oauth2
