---
title: "Internet settings"
currentMenu: internet
parentMenu: app
---

## Overview

From this menu you can manage global application settings as well as settings relative to the "Internet side" of your Vulture's applications.

## Internet settings

### Global settings

 - `Friendly name`: A friendly name for your application.
 - `GUI tags`: A list of 'tags' related to your application. You may use these tags to find your application in the application list of the main page.

### Public URL mapping

 - `Public FQDN`: This is the fully qualified domain name of your web application, as users will type in their web browser. For example: www.example.com. This is used by the Apache 'ServerName' directive.
 - `Public Alias`: Another fully qualified name for your application. Use ',' if you want to add Multiple alias. This is used by the Apache 'ServerAlias' directive.
 - `Public directory`: The public path of your application. Default is '/'.

<br/>
If you want to have www.example.com/private protected by an LDAP authentication and www.example.com/public left unprotected, you can create 2 web applications in Vulture:
 1. The first one will have the '/private/' public dir and will be protected by LDAP authentication.
 2. The second one will have the '/public/' public dir and won't be protected.

Vulture will treat these 2 applications as two completely different applications.


### HTTP features and performance

 - `Worker profile`: The [worker profile](/doc/configuration/worker.html) you want to use for your application.
 - `Enable HTTP/2 protocol`: If enabled this will activate HTTP/2 support for this application. Note that it implies you have at least a [TLS profile](/doc/configuration/tls.html) for one of your [listener](/doc/app/network.html) and a correct HTTP/2 configuration in you [worker profile](/doc/configuration/worker.html).
 - `Enable support of Microsoft RPC-Over-HTTP`: If enabled this will load the mod_msrpc Apache module that supports Microsoft RPC Over HTTP protocol. <br/>
    ** Note that you will need to accept additional HTTP methods for this to works: "RPC_IN_DATA" and "RPC_OUT_DATA". You can do that in [Security settings](/doc/app/security.html)/ **
 - `Enable support of PROXY protocol`: If enabled, the directive *RemoteIPProxyProtocol* of the Apache module *mod_remoteip* will be set to On, Which can be very usefull with HAProxy balancer to keep the original client IP. See [documentation](https://httpd.apache.org/docs/2.4/mod/mod_remoteip.html#remoteipproxyprotocol) for more details.