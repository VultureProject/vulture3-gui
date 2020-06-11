#!/bin/sh
#
# This migration script add the /sbin/pfctl to sudoers for vlt-sys
#
#

echo "vlt-sys ALL=NOPASSWD:/sbin/pfctl" >> /usr/local/etc/sudoers.d/vulture_sudoers


