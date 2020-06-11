---
title: "Backend settings"
currentMenu: backend
parentMenu: app
---

## Overview

From this menu you can manage settings relative to the "Internal side" of your Vulture's application.

## Backend settings

### Application backend settings
 - `Portal template`: The [Portal template](/doc/app/template.html) used for this application. Vulture will use it as soon as it has to dialog with end users (authentication portal, email, error messages, ...).
 - `Application type`: Choose here the URL scheme of your application, typically "http" or "https". <br/>
 Supported scheme are: http, https, balancer, ftp, fcgi, scgi, websocket and ajp.
 If you select "Balanced application" you will have to select a [Proxy Balancer](/doc/network/proxybalancer.html) backend.
 If you select "TLS Web application" additional TLS settings will be displayed (See below).
 Note:
 Vulture gives you the ability to use ws:// and wss:// protocol on regular HTTP applications.<br/>
 It handles Connection: Upgrade / Upgrade: websocket and redirects it so that the application responds 101 Switching Protocols, meaning websocket connection were successfully established.

 - `Private URI`: The private URI of your Web application. Vulture will contact your application through this URL. It is better to use IP Address here instead of hostname, to avoid useless DNS requests. If your web backend needs a Host header associated to this IP address, you can add a custom 'Host' [HTTP Request header](/doc/app/request_header.html) in Vulture.
 - `Preserve incoming Host Header`: By default Vulture will forward to the backend the hostname of the private URI defined above. If you want Vulture to forward the public Host header requested by the client, toggle this option.
 - `Timeout`: This timeout will be passed to an Apache "ProxySet" directive. This is the global timeout for communication with the backend, in seconds. Once this timeout is over, Vulture will raise a HTTP 504 Gateway Timeout.
 - `Disable connection reuse`: This parameter should be used when you want to force mod_proxy to immediately close a connection to the backend after being used, and thus, disable its persistent connection and pool for that backend. This helps in various situations where a firewall between Apache httpd and the backend server (regardless of protocol) tends to silently drop connections or when backends themselves may be under round-robin DNS. To disable connection pooling reuse, set this property value to On.
 - `Send KEEP_ALIVE messages to backend`: This parameter should be used when you have a firewall between your Apache httpd and the backend server, which tends to drop inactive connections. This flag will tell the Operating System to send KEEP_ALIVE messages on inactive connections and thus prevent the firewall from dropping the connection. To enable keepalive, set this property value to On.
 - `TTL of inactive connection`: Time to live for inactive connections and associated connection pool entries, in seconds. Once reaching this limit, a connection will not be used again; it will be closed at some later time.


### Advanced settings
 - `Send Proxy HTTP headers to backend`: This is the [ProxyAddHeaders](https://httpd.apache.org/docs/2.4/en/mod/mod_proxy.html#proxyaddheaders) directive of Apache. This directive determines whether or not proxy related information should be passed to the backend server through X-Forwarded-For, X-Forwarded-Host and X-Forwarded-Server HTTP headers.
 - `Override backend's HTTP errors`: This is the [ProxyErrorOverride](https://httpd.apache.org/docs/2.4/en/mod/mod_proxy.html#proxyerroroverride) directive of Apache. This directive is useful for reverse-proxy setups where you want to have a common look and feel on the error pages seen by the end user. This also allows for included files (via mod_include's SSI) to get the error code and act accordingly. (Default behavior would display the error page of the proxied server. Turning this on shows the SSI Error message.)
  If enable, Vulture will replace application's error page by the one specified in the [Portal template](/doc/app/template.html).
 - `Rewrite Cookie Path`: If enabled (default), Vulture will rewrite the 'path' argument of backend's Cookies. For example if the Vulture's public dir is '/public' and your private URI is '/', Vulture will rewrite the Cookie **"path=/"** to **"path=/public/"**.
