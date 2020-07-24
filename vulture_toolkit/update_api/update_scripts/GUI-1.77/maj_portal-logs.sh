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

dir="/var/log/Vulture/portal"

for file in "debug.log" \
"portal_authentication.log" \
"redis_events.log" ; do
    /usr/bin/touch "$dir/$file"
    /bin/chmod 644 "$dir/$file"
    /usr/sbin/chown vlt-portal:vlt-web "$dir/$file"
done
