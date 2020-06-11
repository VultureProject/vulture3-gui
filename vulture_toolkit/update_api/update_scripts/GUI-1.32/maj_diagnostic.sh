#!/bin/sh
#
# Script to set the correct rights to the diagnostic logfile
#

/usr/bin/touch /var/log/Vulture/gui/diagnostic.log
/usr/sbin/chown vlt-gui:vlt-web /var/log/Vulture/gui/diagnostic.log
