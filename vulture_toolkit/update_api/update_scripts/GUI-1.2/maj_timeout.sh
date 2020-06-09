#!/bin/sh
#
# This migration script increase default timeout
#


val=`/bin/cat /home/vlt-sys/Engine/conf/gui-httpd.conf | /usr/bin/grep "Timeout 60"`
if [ "$val" == "" ]
then

	/bin/echo "--- gui-httpd.conf  2016-08-10 16:22:11.685024703 +0200
+++ gui-httpd.conf  2016-08-10 16:22:18.569024653 +0200
@@ -62,7 +62,7 @@
 MaxRequestWorkers      400
 MaxConnectionsPerChild   0
 
-Timeout 20
+Timeout 60
 KeepAlive On
 KeepAliveTimeout 20
 MaxKeepAliveRequests 100
@@ -115,4 +115,4 @@
         </Files>
     </Directory>
 
-</VirtualHost>
\ Pas de fin de ligne à la fin du fichier
+</VirtualHost>" | patch /home/vlt-sys/Engine/conf/gui-httpd.conf

fi

