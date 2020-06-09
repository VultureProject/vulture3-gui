#!/bin/sh

/bin/echo "Updating MongoDB from 2.6 to 3.2"

set -ex

. /etc/rc.conf

if [ "$http_proxy" != "" ]
then
    export https_proxy="http://$http_proxy"
    export http_proxy="http://$http_proxy"
fi

cd /tmp
/usr/bin/env ASSUME_ALWAYS_YES=YES /usr/sbin/pkg fetch -d -o . mongodb32
/usr/sbin/service mongod stop
/usr/bin/env ASSUME_ALWAYS_YES=YES /usr/sbin/pkg remove mongodb
/usr/bin/env ASSUME_ALWAYS_YES=YES /usr/sbin/pkg add ./All/*.txz
/usr/sbin/service mongod start

rm -rf ./All
/bin/echo "MongoDB successfully updated"