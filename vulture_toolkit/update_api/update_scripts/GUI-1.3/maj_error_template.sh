#!/bin/sh


/bin/echo "[+] Updating error_templates"

if [ $(/usr/bin/whoami) = "root" ]
then
    /bin/echo "[*] Patching portal-httpd.conf..."
    /bin/echo "--- /home/vlt-adm/portal-httpd.conf	2016-09-07 13:13:37.466990000 +0000
+++ portal-httpd.conf	2016-09-07 12:55:38.497318000 +0000
@@ -113,6 +113,7 @@
     RewriteCond %{REQUEST_URI} !^/portal/2fa/otp$ [NC]
     RewriteCond %{REQUEST_URI} !^/templates/portal_.*_css\.conf$ [NC]
     RewriteCond %{REQUEST_URI} !^/templates/portal_.*\.png$ [NC]
+    RewriteCond %{REQUEST_URI} !^/templates/portal_.*_html_error_[0-9]{3}\.html$ [NC]
     RewriteRule .* - [F,NC]

 </VirtualHost>
" | patch /home/vlt-sys/Engine/conf/portal-httpd.conf
else
    /bin/echo "[/] You are not authorized to execute that file : only root can."
fi