#!/bin/sh
#
# This script set the correct execution rights to crontab script's
#

if [ $(/usr/bin/whoami) = "root" ]
then
    chmod -R 750 /home/vlt-sys/crontab/
    chmod -R 750 /home/vlt-gui/crontab/

    /bin/echo "--- old	2016-09-26 15:50:57.380021000 +0200
+++ new	2016-09-26 16:28:53.770015000 +0200
@@ -1,6 +1,7 @@
 #!/bin/sh
 
+touch /var/log/Vulture/gui/redis_events.log
+chown vlt-gui:vlt-web /var/log/Vulture/gui/*
 /usr/local/bin/sudo /home/vlt-sys/scripts/check_updates.hour
+sudo /usr/local/sbin/logrotate /usr/local/etc/logrotate.d/vulture.conf
 for each in /home/vlt-sys/crontab/*.hour ; do sh $each ; done
-/home/vlt-sys/scripts/log_rotate.hour
-/usr/local/sbin/logrotate /usr/local/etc/logrotate.d/vulture.conf" | patch /home/vlt-sys/scripts/hour.sh
fi