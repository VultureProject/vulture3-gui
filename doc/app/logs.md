---
title: "Logs settings"
currentMenu: logs
parentMenu: app
---

## Overview

From this menu you can manage the logs settings of your application.

By default logs are always stored in `/var/log/Vulture/`, and are sent to a [data repository](/doc/repositories/repo.html) if configured to.
On disk logs are:
 - /var/log/vulture/gui/    : Logs related to GUI (also stored in the internal mongoengine).
 - /var/log/vulture/portal/ : Logs related to PORTAL (also stored in the internal mongoengine).
 - /var/log/vulture/worker/ : Logs related to Apache workers.


## Logs settings

 - `Log Profile`: The [LOG profile](/doc/configuration/logs.html) to use to store applications's worker's logs.
 - `Log Level`: Apache LogLevel directive: info, warning or error. In production, choose error.
 - `Log POST data`: If enable, Vulture will log POST content. ** WARNING ** This may reveal sensitive information, use with caution.
