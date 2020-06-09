#!/bin/sh
#
# This migration script changes /etc/hosts with new addresses
#
#

/bin/cat /etc/hosts | /usr/bin/sed -e 's/.*vultureproject.org/163.172.108.9 2001:bc8:236b:101::100 dl.vultureproject.org/' > /tmp/hosts && /bin/mv /tmp/hosts /etc/hosts
