---
title: "Reputation"
currentMenu: reputation
parentMenu: management
---

## Overview

From this view you can configure the IP reputation databases you want to use with Vulture. By default Vulture will download 55 databases from Internet and ingest them into Redis. This process runs every night in background (crontab).

If you want to add custom database, just add the URL of the list and associate a "tag" to it.
![Reputation](/doc/img/reputation.png)

## How does reputation work ?

A Vulture system process, `loganalyzer`, check in Vulture logs if any source IP address is known to have a bad reputation. This process will query redis for that. If a match is found, Vulture will modify the log entries to add the corresponding tags:<br/>
![Logs Reputation](/doc/img/logs-reputation.png)


## Can I block traffic based on IP source reputation ?

Yes you can! Just go in the security panel of an application [Application security](/doc/app/security.html) and select tags you want to block:
![](/doc/img/waf_reputation.png)

The blocking process is done via mod_vulture inside httpd. Vulture looks for the source IP address in Redis and, if found and the tag needs to be blocked, Vulture will return a "403 FORBIDDEN" HTTP response.
