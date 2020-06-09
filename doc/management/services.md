---
title: "Services management"
currentMenu: services
parentMenu: management
---

## Overview

From the "Management / Services" view you can manage Vulture's global settings:
 - ModSecurity URL settings
 - Vulture global settings
 - Log global settings
 - Location settings

You can also manage the configuration of the following system services:
  - DNS
  - NTP
  - SMTP
  - SSH
  - FAIL2BAN

## ModSecurity URL settings
- `OWASP CRS URL`: The ModSecurity URL from which Vulture should download OWASP CRS ruleset.
- `Trustwave rules URL`: The URL from which Vulture should download rules from Spiderlabs Research (SLR).
- `Trustwave authentication header`: The authentication header needed to download SLR rules.

## Vulture settings
- `Source branch`: The name of the branch from where to download vulture.
- `Portal Cookie Name`: The name of the Cookie used to maintain session on the Vulture portal (randomized by default).
- `Application Cookie Name`: The name of the Cookie used to maintain session on Web Applications (randomized by default).
- `Public Token Name`: The name of the token used during redirection from application to the portal login form (randomized by default).
- `OAuth2 Token Name`: The name of the HTTP Header used by Vulture to get the user's OAuth2 Token ("X-Vlt-Token" by default).
- `GUI Timeout`: The amount of time, in seconds, before disconnecting the user from the Vulture GUI. Everytime the user clicks on the GUI, the timeout is resetted.

## Log settings

Vulture stores internal logs (GUI logs, Portal logs, pf logs, diagnostic logs, ...) into a "Log repository". <br>
By default logs are stored :
 - Inside the Vulture internal mongoDBEngine.
 - On disk, in /var/log/Vulture/*

From this menu you can:
 - Choose any data repository created from the [Repository menu](/doc/repository/repo.md).
 - Choose when the rotation should occur (daily by default).
 - How many archives you want to keep (30 by default).

 `Rotation and archives to keep apply to on-disk file and internal mongoDBEngine`. This is to prevent any saturation of the internal database. If you choose a remote repository, like ElasticSearch - which is recommended in case of heavy traffic, Vulture won't rotate the logs inside this remote repository.


## Services settings

### Overview

For many of these services, you can choose to apply configuration on a given node or on the whole cluster.

### DNS Resolver

These settings are used to build the /etc/resolv.conf of Vulture. By default no DNS configuration exists, you will need to define your DNS configuration if you want Vulture to access the Internet (for system updates). If you access Internet through an HTTP Proxy, it is not required to define any DNS.

### NTP Settings

Define here the addresses of your NTP server. If NTP server are on the Internet don't forget to configure DNS resolution if needed to resolv NTP hostname

### SMTP Settings

Vulture needs to send emails when [email OTP](/doc/repository/otp) is enable. Vulture won't send email directly and requires an SMTP server to relay emails. If no relay server is available within your organisation you can still configure a local postfix on Vulture and user 127.0.0.1 as SMTP relay here here.

### SSH Settings

From this menu you can enable / disable SSH service on vulture nodes.
