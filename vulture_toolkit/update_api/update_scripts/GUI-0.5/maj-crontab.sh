#!/bin/sh
#
# This script redirect crontab to /dev/null
#
#
echo "SHELL=/bin/sh
PATH=/usr/local/sbin:/usr/sbin:/sbin:/usr/local/bin:/usr/bin:/bin
*       *       *       *       *       /home/vlt-sys/minute.sh >/dev/null 2>&1
0       *       *       *       *       /home/vlt-sys/hour.sh >/dev/null 2>&1
59       23       *       *       2   /home/vlt-sys/scripts/geoipupdate.sh >/dev/null 2>&1" > /tmp/cron-vlt-sys

echo "SHELL=/bin/sh
PATH=/usr/local/sbin:/usr/sbin:/sbin:/usr/local/bin:/usr/bin:/bin
*       *       *       *       *       /home/vlt-gui/minute_gui.sh >/dev/null 2>&1" > /tmp/cron-vlt-gui

crontab -u vlt-sys /tmp/cron-vlt-sys
crontab -u vlt-gui /tmp/cron-vlt-gui

rm /tmp/cron-vlt-gui
rm /tmp/cron-vlt-sys