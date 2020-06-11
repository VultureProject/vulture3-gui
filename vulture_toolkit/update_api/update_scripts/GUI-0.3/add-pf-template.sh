#!/bin/sh
#
# This migration script add support for pf.conf template in /home/vlt-sys/scripts/write_configuration_file
#
#
echo "--- old	2016-02-02 22:49:22.347068000 +0100
+++ new	2016-02-02 22:50:00.272294000 +0100
@@ -35,6 +35,7 @@
                      '/usr/local/etc/ssmtp/ssmtp.conf',
                      '/usr/local/etc/fluentd/fluent.conf',
                      '/usr/local/etc/redis.conf',
+                     '/usr/local/etc/pf.conf',
                      '/usr/local/etc/sentinel.conf',
                      '/etc/rc.conf.local',
                      '/home/vlt-sys/Engine/conf/gui-httpd.conf'," | patch /home/vlt-sys/scripts/write_configuration_file
