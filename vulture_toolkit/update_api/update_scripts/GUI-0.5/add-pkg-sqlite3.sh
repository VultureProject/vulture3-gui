#!/bin/sh
#
# This migration script add the py-sqlite3 package to Vulture (needed for vulture 2 => 3 migration)
#
#

. /etc/rc.conf

proxy=""
if [ "$http_proxy" != "" ]
then
    env ASSUME_ALWAYS_YES=YES http_proxy="http://$http_proxy" pkg install databases/py-sqlite3
else
    env ASSUME_ALWAYS_YES=YES pkg install databases/py-sqlite3
fi
