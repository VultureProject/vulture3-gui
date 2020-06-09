---
title: "Configuration profiles"
currentMenu: configuration
parentMenu: configuration
---

## Overview

Configuration profiles are use to simplify Vulture management. <br/>
Here you can create configuration profiles and reuse them later in your application's configurations:

 - [Logs profiles](/doc/configuration/logs.html)
 - [TLS profiles](/doc/configuration/tls.html)
 - [Worker profiles](/doc/configuration/worker.html)
 - [ACLs profiles](/doc/configuration/acls.html)

## Vulture's configuration files and associated Apache httpd processes

``
Vulture will create a configuration file and an associated apache process for every IP address / port used in its configuration:
 - A configuration file + process for 192.168.1.1 on port 80
 - A configuration file + process for 192.168.1.2 on port 80
 - A configuration file + process for 192.168.1.1 on port 443
 - ...

Be careful when you configure profiles, because 2 applications may be sharing the same server context or virtualhost context inside a unique configuration file:
 - Application level's directives will be good.
 - VirtualHost level's directives may enter in conflict.
 - Server level's directives may enter in conflict.

If you use inconsistent parameters between applications, Vulture will warn you telling that there is conflict between parameters. <br/>

``
