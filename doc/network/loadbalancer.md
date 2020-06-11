---
title: "Load Balancer"
currentMenu: loadbalancer
parentMenu: network
---

## Overview

Vulture uses [ha-proxy](http://www.haproxy.org) to provide high-performance load-balancing features on **incoming request**. <br/>
You can use this feature to accept incoming connexion on any TCP port and load-balance it to another server:
  - Another Vulture node inside the cluster for incoming web traffic.
  - Another server for another protocol.

![HA-Proxy Load Balancer](/doc/img/load-balancing.png)


## Create a load-balancer

To create an incoming load-balancer configuration, here are the required informations:


 - `Name`: A friendly name for the load-balancer.
 - `HTTP Mode`: Needed if the backend is a HTTP Application.
 - `Enable TLS`: Enable listening in HTTPS mode
 - `SSL Profile`: [SSL Profile](/doc/configuration/tls.html) to use for HTTPS listening.
 - `Keep Alive`: Enable connection reuse on client/server side to provide lowest latency. See [documentation](http://cbonte.github.io/haproxy-dconv/1.9/configuration.html#4-option%20http-keep-alive)
 - `Sticky session`: In HTTP mode, ensure that a user will always be directed to the same server. This option set the directive *cookie SRVNAME insert* in Listen section, and *cookie \[server-name\]* in each server section.
 - `Incoming listener`: The network interface on which ha-proxy should listen.
 - `Incoming port`: The TCP port on which ha-proxy will listen (80 or 443 for example).
 - `Balancing mode`: All balancing mode of HAProxy are supported :
    - `RoundRobin`: Use the servers weight to balance connections
    - `Least Conn`: The server with the lowest number of connections receives the connection
    - `First server`: The first server with available connection slots receives the connection
    - `Source IP based`: Ensures that the same client IP address will always reach the same server
    - `URI based`: Ensures that the same URI will always be directed to the same server
    - `URL param based`: This is used to track user identifiers in requests and ensure that a same user ID will always be sent to the same server))
    - `Header based`: Ensures that the same header value will always be directed to the same server
    - `RDP-Cookie based`: Makes it possible to always send the same user (or the same session ID) to the same server
- `Balancing parameter` (optional): Parameter of balancing mode chosen, if needed.
> See [HAProxy balance documentation](http://cbonte.github.io/haproxy-dconv/1.9/configuration.html#4-balance) for more details on balancing modes.

<i class="fa fa-warning">&nbsp;&nbsp;</i>The HTTP Mode is needed if you need the original client's IP logged by Vulture. This mode adds a `X-Forwarded-For' header with the Client's IP address.

You can fine-tune some settings to improve performance / to adapt timeout to backends:


 - `Timeout connect` : Maximum timeout for client to connect to Vulture, defaults to 500ms. [HAProxy documentation](http://cbonte.github.io/haproxy-dconv/1.9/configuration.html#4.2-timeout%20connect)
 - `Timeout server` : Maximum timeout for Vulture to connect to the backend, defaults to 2s. [HAProxy documentation](http://cbonte.github.io/haproxy-dconv/1.9/configuration.html#4.2-timeout%20server)
 - `Timeout client` : Maximum timeout for a client to acknowledge or send data, defaults to 5s. [HAProxy documentation](http://cbonte.github.io/haproxy-dconv/1.9/configuration.html#4.2-timeout%20client)
 - `Timeout tunnel` : Maximum timeout on client and server side for tunnels (e.g: for WebSocket tunnels). Defaults to 600s. [HAProxy documentation](http://cbonte.github.io/haproxy-dconv/1.9/configuration.html#4.2-timeout%20tunnel)
 - `Timeout server-fin` : Maximum timeout on server side for half-closed connections (usefull for example for WebSocket tunnels). Defaults to 10s. [HAProxy documentation](http://cbonte.github.io/haproxy-dconv/1.9/configuration.html#4.2-timeout%20server-fin)
 - `Max connections` : Maximum simultaneous connections, defaults to 10,000. [HAProxy documentation](http://cbonte.github.io/haproxy-dconv/1.9/configuration.html#maxconn)


You will then need to add one or more backend to which you want to forward incoming request. <br/>
In a cluster configuration you will want to declare here all your Vulture nodes, but you can choose any IP / port you want.<br/>
** Please not that you CANNOT select any carp IP address here **
<br/><br/>

 - `Host` : A Friendly name for the backend
 - `IP` : IP address of the backend
 - `Port` : TCP port of the backend
 - `Weight` : An integer to ponderate load-balancing trafic. If you have 2 backends, one with a weight of "1" and the second with a weight of "2", the second will receive twice more traffic that the first. [HAProxy documentation](http://cbonte.github.io/haproxy-dconv/1.9/configuration.html#5.2-weight)
 - `Tls`: Connect to server with HTTPS protocol
 - `Send-proxy`: Enforce the use of PROXY protocol over TCP connections to informs server about source IP addresses. [HAProxy documentation](http://cbonte.github.io/haproxy-dconv/1.9/configuration.html#5.2-send-proxy)

For example, consider the following network diagram:<br/>
![Load-Balancing-2](/doc/img/load-balancing-2.png) <br/>
<br/>
We want to load-balance incoming HTTP traffic (TCP port 80) from our CARP listener to each member of the Vulture cluster.<br/>
Here are the parameters to create the HA-PROXY configuration:
 - `Incoming listener`: Your CARP Listener (192.168.1.1)
 - `Incoming port`: 80
 - `Backend servers (Host / IP / PORT / Weight) `:
    - Vulture-1 / 172.16.1.1 / 80 / 1
    - Vulture-2 / 172.16.1.2 / 80 / 1
    - Vulture-3 / 172.16.1.3 / 80 / 1

In this example, all weights are set to 1. So Vulture will send the first request to vulture-1, then on vulture-2, then on vulture-3, then on vulture-1, ...
If one of the node fails, the CARP IP address will switch to another node and load-balancing will continue on the remaining 2 nodes.

## Advanced configuration

In this section you can write ha-proxy directives. These directives will be placed in the "Listen" section of ha-proxy configuration.
See ha-proxy documentation for details.
