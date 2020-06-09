
# Vulture3 GUI

Welcome on the [Vulture 3](https://www.vultureproject.org) project !

![](/doc/img/screenshot.png)

## Overview

Vulture3 is an Open Source HTTP `reverse-proxy`. It ensures the security of web applications facing the internet. <br/>
Vulture3 is ready for HTTP/2 and IPv6.

Basic features are:
 - Network firewall based on FreeBSD `pf`
 - Network TCP balancing based on `ha-proxy`
 - HTTP Proxy balancer based on `Apache`
 - User Authentication against LDAP/AD, Kerberos, SQL, Radius, ...
 - Web application firewall based on `ModSecurity` and `custom algorithms`
 - TLS endpoint, Content rewriting, and many other cool things...

Vulture3 is build on top of FreeBSD, Apache, Redis and MongoDB. <br/>
It is horizontaly scalable by-design (Vulture Cluster) and is manageable though a unique Web GUI.

