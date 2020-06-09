#!/bin/sh
#
# This migration script create the trusted CA directory and copy the needed certs
#
#

. /etc/rc.conf

/bin/echo "[+] Creating the trusted CA certificates directory ..."

if [ $(/usr/bin/whoami) = "root" ]
then
    /bin/mkdir /home/vlt-sys/Engine/conf/certs
    /usr/bin/chgrp vlt-web /home/vlt-sys/Engine/conf/certs
    /bin/chmod 775 /home/vlt-sys/Engine/conf/certs
    /bin/echo "[+] Copying Mozilla's trusted CA certificates ..."
    /bin/cp /usr/local/share/certs/ca-root-nss.crt /home/vlt-sys/Engine/conf/certs
    /bin/echo "[+] Copying Vulture certificate ..."
    /bin/cp /var/db/mongodb/ca.pem /home/vlt-sys/Engine/conf/certs/vulture_ca.crt
    /bin/echo "[+] c_rehash certificates ..."
    /usr/local/bin/c_rehash /home/vlt-sys/Engine/conf/certs
    /bin/echo "[+] Patching portal-httpd.conf ..."
    if [ `grep -c "WSGIPassAuthorization On" /home/vlt-sys/Engine/conf/portal-httpd.conf` == 0 ]
    then
        /bin/echo "--- /home/vlt-sys/Engine/conf/portal-httpd.conf	2016-08-18 17:31:58.983198000 +0200
+++ /home/vlt-sys/Engine/conf/portal-httpd.conf	2016-08-18 17:54:53.994523000 +0200
@@ -2,6 +2,7 @@
 PidFile /home/vlt-sys/run/portal.pid
 ScoreBoardFile /home/vlt-sys/run/portal.scoreboard
 WSGISocketPrefix /home/vlt-sys/run/
+WSGIPassAuthorization On
 Mutex sem

 Listen 127.0.0.1:9000 https" | patch /home/vlt-sys/Engine/conf/portal-httpd.conf
    fi
    /bin/echo "--- /home/vlt-sys/Engine/conf/portal-httpd.conf	2016-08-17 13:28:12.770975000 +0200
+++ /home/vlt-sys/Engine/conf/portal-httpd.conf	2016-08-17 15:31:39.654587000 +0200
@@ -5,7 +5,7 @@
 WSGIPassAuthorization On
 Mutex sem

-Listen 127.0.0.1:9000 https
+Listen 127.0.0.1:9000 http

 #Autorisation helper (require valid-use / hostr)
 LoadModule authz_core_module modules/mod_authz_core.so
@@ -51,7 +51,7 @@
 ErrorDocument 500 /templates/static/html/error-500.html

 AcceptFilter http httpready
-AcceptFilter https dataready
+AcceptFilter http dataready

 EnableMMAP on
 EnableSendfile on
@@ -85,15 +85,6 @@
     WSGIDaemonProcess portal python-path=/home/vlt-gui/vulture:/home/vlt-gui/env/lib/python2.7/site-packages
     WSGIProcessGroup portal

-    #SSL Configuration parts
-    SSLEngine                    on
-    SSLCACertificateFile         /var/db/mongodb/ca.pem
-    SSLCertificateKeyFile        /var/db/mongodb/mongod.key
-    SSLCertificateFile           /var/db/mongodb/mongod.cert
-    SSLOptions +StdEnvVars
-    SSLProtocol -ALL +TLSv1.1 +TLSv1.2
-    SSLCipherSuite ALL:!ADH:RC4+RSA:+HIGH:+MEDIUM:!LOW:!SSLv2:!EXPORT
-
     #No cache at all for portal
     Header always set Cache-Control \"no-cache, no-store, must-revalidate\"
     Header always set Pragma \"no-cache\"" | patch /home/vlt-sys/Engine/conf/portal-httpd.conf
    /bin/echo "[*] Script ended successfully."
else
    /bin/echo "[/] You are not authorized to create that file : only root can."
fi
