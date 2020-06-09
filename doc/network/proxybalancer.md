---
title: "Proxy Balancer"
currentMenu: proxybalancer
parentMenu: network
---

## Overview

Sometimes a web application runs on multiple web servers, to improve performance and availability. <br/>
Vulture can load-balance incoming HTTP requests to multiple web backends: <br/>
<br/>
![Proxy load-balancer](/doc/img/proxy-balancing.png)
<br/>
Unlike [load-balancer](/doc/network/loadbalancer.html), Proxy balancer works in layer 7 on HTTP protocol. <br/>
You can combine both incoming TCP load-balancer and Proxy balancer to have powerful multi-layered load-balancing.


## Create a proxy balancer

 - `Friendly name` : A friendly name for the proxy balancer.
 - `Load-balancing method` : HTTP Load-balancing algorithm.
    - By backend busyness : A new request is sent to the backend with the smallest number of requests.
    - By heartbeat : A new request is sent to the backend with the best average response time.
    - By backend requests : Requests are distributed on each backend, by request count.
    - By traffic : Requests are distributed on each backend, by request size.
 - `Sticky session` : Once a first request, for a given user, has been sent to a backend, you may want to serve other requests to the same backend. Specify here the **name of the cookie** used to track the user backend. This cookie must been set by the backend itself and must contain the route (usually appended to session id).
 - `Sticky session separator` : If the backend route is not inside an dedicated cookie, but part as a session cookie for example (sessionid=aff4213.route_1), specify here the character used as a separator ("." in our example). Set to 'Off' if no separator is used.
 - `Expert config` : You can pass custom directive for Proxy Balancer. They will be passed to the apache `Proxyset` directive, inside a ""<Proxy balancer://XXXXX>" section.

For details, see https://httpd.apache.org/docs/2.4/fr/mod/mod_proxy_balancer.html.

Then, we need to add HTTP backend to balance traffic to:

 - `Backend Type` : Choose the URL scheme of the backend
 - `IP Address` : IP address of the backend
 - `Disable reuse` : This parameter should be used when you want to force mod_proxy to immediately close a connection to the backend after being used, and thus, disable its persistent connection and pool for that backend. This helps in various situations where a firewall between Apache httpd and the backend server (regardless of protocol) tends to silently drop connections or when backends themselves may be under round- robin DNS. To disable connection pooling reuse, set this property value to On.
 - `KeepAlive` : This parameter should be used when you have a firewall between your Apache httpd and the backend server, which tends to drop inactive connections. This flag will tell the Operating System to send KEEP_ALIVE messages on inactive connections and thus prevent the firewall from dropping the connection. To enable keepalive, set this property value to On.
 - `Group ID` : Integer that represent the group ID of your backend. Vulture will first try all members of the group with the smallest group ID, then will try another group ID.
 - `Retry` : Connection pool worker retry timeout in seconds. If the connection pool worker to the backend server is in the error state, Apache httpd will not forward any requests to that server until the timeout expires. This enables to shut down the backend server for maintenance and bring it back online later. A value of 0 means always retry workers in an error state with no timeout.
 - `Route` : Value of the sticky session associated to the backend, as found in the sticky session cookie.
 - `Timeout` : Connection timeout in seconds. The number of seconds Apache httpd waits for data sent by / to the backend.
 - `TTL` : Time to live for inactive connections and associated connection pool entries, in seconds. Once reaching this limit, a connection will not be used again; it will be closed at some later time.
 - `Expert Config` : Custom directives, directtly appended in the httpd's **BalancerMember** directive

For details, see https://httpd.apache.org/docs/2.4/fr/mod/mod_proxy_balancer.html


Once your proxy balancer is created, you can choose it as backend in the [Private URI](/doc/app/backend.html) settings of your application.


## I want sticky session but my backend do not have a "routing cookie"

If you want stickysession, but your backend servers do not set COOKIE for routing, you can create it from Vulture. <br/>
Here is the howto:

1. **Create the following Cookie in vulture application's configuration** (See [how to add a response Cookie](/doc/app/response_headers.html))
    - Action: Add the header
    - Header name: ROUTEID
    - Matching pattern: .%{BALANCER_WORKER_ROUTE}e (do not forget the '.')
    - Condition: "If env. variable exists" => BALANCER_ROUTE_CHANGED
2. **Use "ROUTEID" as Sticky session name**
2. **Use "." as Sticky session separator**
3. **Create balancer members (see below) with "1", "2", "3"... as route value**

This will result in the following configuration in Vulture's worker configuration files:
```
Header add Set-Cookie "ROUTEID=.%{BALANCER_WORKER_ROUTE}e; path=/" env=BALANCER_ROUTE_CHANGED
<Proxy "balancer://mycluster">
    BalancerMember "http://192.168.1.50:80" route=1
    BalancerMember "http://192.168.1.51:80" route=2
    ProxySet stickysession=ROUTEID
</Proxy>
```
