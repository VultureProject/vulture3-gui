#!/bin/sh
#
# This script migrates crontab from vulture-ova to vulture-gui project
#
#


echo "#!/bin/sh
for each in /home/vlt-gui/vulture/crontab/vlt-gui/*.day ; do \$each ; done
" > /home/vlt-gui/day_gui.sh

echo "#!/bin/sh
for each in /home/vlt-gui/vulture/crontab/vlt-gui/*.hour ; do \$each ; done
" > /home/vlt-gui/hour_gui.sh

echo "#!/bin/sh
for each in /home/vlt-gui/vulture/crontab/vlt-gui/*.minute ; do \$each ; done
/home/vlt-gui/env/bin/python /home/vlt-gui/vulture/testing/testing_client.py
" > /home/vlt-gui/minute_gui.sh

/bin/chmod 750 /home/vlt-gui/*_gui.sh
chown vlt-gui /home/vlt-gui/*_gui.sh



echo "#!/bin/sh

touch /var/log/Vulture/gui/redis_events.log
chown vlt-gui:vlt-web /var/log/Vulture/gui/*
/usr/local/bin/sudo /home/vlt-sys/scripts/check_updates.hour
sudo /usr/local/sbin/logrotate /usr/local/etc/logrotate.d/vulture.conf
" > /home/vlt-sys/hour.sh

echo "#!/bin/sh

/usr/local/bin/sudo /home/vlt-gui/vulture/crontab/vlt-sys/pflog.sh >/dev/null 2>&1
" > /home/vlt-sys/minute.sh

/bin/chmod 750 /home/vlt-sys/*.sh
chown vlt-sys /home/vlt-sys/*.sh

rm -rf /home/vlt-gui/crontab/

sudo -u vlt-gui crontab -l > /tmp/ctgui
echo "*       0       *       *       *	       /home/vlt-gui/day_gui.sh >/dev/null 2>&1" >> /tmp/ctgui
sudo -u vlt-gui crontab /tmp/ctgui
rm -f /tmp/ctgui