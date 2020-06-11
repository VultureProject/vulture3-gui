---
title: "Reporting Map"
currentMenu: map
parentMenu: reporting
---

![Vulture GUI](/doc/img/report_map.png)

This page shows the number of hits by country for the last 10 minutes.<br/>
This page searches from the data logs repository of applications and search inside the `access` database.<br/>
To enable GEOIP, you need to active it inside the [application configuration](/doc/app/security.html).<br/>

- `Application`: Filter results by application (empty will use all applications).
- `Status code`: Filter by request status code.
- `Reputation` : Filter by reputation tags.

With this page, you can see where the traffic is coming from and block or allow targeted countries.
