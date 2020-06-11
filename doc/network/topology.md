---
title: "Topology"
currentMenu: topology
parentMenu: network
---

## Overview

- `Trusted IP for which X-Forwarded-For is acceptable`: IP/Block IP/FQDN

These directives list the IP address from which Vulture will trust the `X-FORWARDED-FOR` header.<br/>
It is used for example when Haproxy is configured and load balance web traffic to the Vulture cluster.<br/>
Haproxy creates an `X-FORWARDED-FOR` header in the HTTP request, with the `REMOTE_ADDR` value.<br/><br/>

By default, if Vulture sees a `X-FORWARDED-FOR` header coming from itself or an other member of the cluster, it will replace the `REMOTE_ADDR` header with it.<br/>
So if you have a proxy ahead, you'll need to specify its IP address to accept the `X-FORWARDED-FOR` header.
