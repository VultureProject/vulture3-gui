---
title: "Network"
currentMenu: network
parentMenu: network
---

## Overview

Vulture is a reverse-proxy. It should be placed between users and the web-application you want to protect: <br/>
<br/>
![Network](/doc/img/network.png)
<br/>
<br/>
Vulture has a built-in **firewall**, based on [OpenBSD pf](https://www.openbsd.org/faq/pf/). You do not need to protect Vulture with an additional firewall.


## Listeners

Vulture accepts incoming traffic on defined IP addresses and ports. IP addresses on which Vulture is listening are called `listeners`. <br/>
You can add / remove listeners and configure as many IP addresses as you need on any network device available on the system. <br/>
<br/>
In cluster configuration, Vulture uses [CARP](https://www.freebsd.org/doc/handbook/carp.html) and allows multiple hosts to share the same IP address and Virtual Host ID (VHID) in order to provide high availability. This means that one or more hosts can fail, and the other hosts will transparently take over so that users do not see a service failure.
<br/><br/>Create a load-balancer (see below) on top of a CARP listener to have a highly available cluster with incoming traffic load balanced among all the Vulture nodes available in your cluster.

See [how to configure Listeners here](/doc/network/listener.html).

## Load balancer

Vulture has a built-in **layer 4** [load-balancer](/doc/network/loadbalancer.html), based on [ha-proxy](http://www.haproxy.org). You do not need to add a load-balancer "before" Vulture. <br/>
ha-proxy is configured in `tcp mode`: Vulture can load-balance any TCP traffic, not only HTTP.<br/>

## Proxy balancer

Vulture has a built-in **layer 7** [HTTP Proxy balancer](/doc/network/procybalancer.html) so that it can load-balance trafic to multiple web backends.


## Incoming URL rewriting

Incoming HTTP requests can be rewritten by Vulture.  <br/>
See details [here](/doc/network/rewriting.html).
