---
title: "Reporting Access"
currentMenu: Access
parentMenu: reporting
---

![Vulture GUI](/doc/img/report_access.png)

This page displays several charts which allows you to see general informations about your applications.<br/>
It searches and aggregates data from the data logs repository of your applications within the `access` database.<br/>
To get data on this page, you need to setup a [data repository](/doc/repositories/repo.html) for at least one of your [applications](/doc/app/logs.html).<br/>

- `Application`: Filter results by application (empty will use all applications).
- `Date` : Filter by a date range (precision of line charts depends on date range length).

Charts available on this page:
- Number of hits by status code (line chart)
- HTTP code (pie chart)
- HTTP methods (pie chart)
- Browsers (pie chart)
- Operating systems (pie chart)
- Traffic per URL (data table)
- Average bytes received per request (line chart)
- Average bytes sent per request (line chart)
- Average time elasped per request (line chart)
