#!/bin/sh
#
# This migration script install the dictionaries for radius auth
#
#

. /etc/rc.conf

cd /tmp
rm -f /tmp/dictionaries.zip

if [ "$http_proxy" != "" ]
then
    export https_proxy="http://$http_proxy"
    export http_proxy="http://$http_proxy"
fi

/usr/local/bin/wget --no-check-certificate https://dl.vultureproject.org/dictionaries.zip
cd /usr/local/share
unzip /tmp/dictionaries.zip
