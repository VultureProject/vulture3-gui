#!/bin/sh
#
# This script add vlt-gui to group daemon
#
#

# Add vlt-gui in "vlt-conf" group
if [ "$(/bin/cat /etc/group | /usr/bin/grep 'vlt-gui' | /usr/bin/grep 'daemon')" == "" ]
then
    /usr/sbin/pw usermod vlt-gui -G daemon
else
    /bin/echo "It seems that this script has already been executed"
fi

# Add vlt-gui in "vlt-conf" group
if [ "$(/bin/cat /etc/group | /usr/bin/grep 'vlt-gui' | /usr/bin/grep 'vlt-conf')" == "" ]
then
    /usr/sbin/pw usermod vlt-gui -G vlt-conf
else
    /bin/echo "It seems that this script has already been executed"
fi
