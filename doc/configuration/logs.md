---
title: "Logs profiles"
currentMenu: logs
parentMenu: configuration
---

## Overview

Logs profiles are used to define custom logging policy: Where to store logs, log format ... <br/>
Logs can be stored:
 - On disk (Repository type = file).
 - On a mongoDB or Elasticsearch repository (Repository type = data).

Note that when you store logs inside elasticsearch or mongodb, you cannot change the logs format. <br/>
This is useless because Vulture stores all that can be stored.
Also if you want to use Vuture's [reporting pages](/doc/reporting/access.md) you need to have at least one data repository.

We recommend storing logs into a remote elasticsearch or mongoDB cluster.


## Create an "on-disk" log profile

 - `Friendly name`: Friendly name of your log profile.
 - `Repository type`: file.
 - `Optional syslog repository` : You can choose to forward log to an external SYSLOG server. See [SYSLOG repository](/doc/repositories/syslog.html) documentation.
 - `Bufferize before writing on disk`: This boosts the logging performance at the cost of loosing logs in case of a failure.
 - `Log separator`: Log field separator, <whitespace> is the Apache httpd's default.
 - `Log format`: You can choose the format of a log entry here. Auto-completion let you known default Apache httpd's available fields.
 - `Log preview`: You will see here a sample log line with you custom log format.

## Create a "data repository" log profile


 - `Friendly name`: Friendly name of your log profile.
 - `Repository type`: data.
 - `Optional syslog repository` : You can choose to forward log to an external SYSLOG server. See [SYSLOG repository](/doc/repositories/syslog.html) documentation.
 - `Data repository` : Select a [mongodb](/doc/repositories/mongodb.html) or [elasticsearch](/doc/repositories/elastic.html) data repository.

When you choose a data repository, the log format is the following:
```
"%{app_name}e %a %l %u %t %r %>s %b %{Referer}i %{User-agent}i %I %O %D %{COUNTRY_CODE}e %{REPUTATION}e"
```

For ```%{COUNTRY_CODE}e``` to be replaced by the country of the source IP address, you need to [enable GeoIP in application](/doc/app/security.html).
For ```%{REPUTATION}e``` to be replaced by the country of the source IP address, you need to [enable Reputation in application](/doc/app/security.html).
