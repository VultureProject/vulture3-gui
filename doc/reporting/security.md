---
title: "Reporting Security"
currentMenu: security
parentMenu: reporting
---

![Vulture GUI](/doc/img/report_security.png)

This page displays several charts which allows you to see security informations about your applications.<br/>
It searches and aggregates data from the data logs repository of your applications within the `access` database.<br/>
To get data on this page, you need to setup a [data repository](/doc/repositories/repo.html) for at least one of your [applications](/doc/app/logs).<br/>

- `Application`: Filter results by application (empty will use all applications).
- `Date` : Filter by a date range (precision of line charts depends on date range length).

Charts available on this page:
- Number of hits by status code (line chart)
- Average score by status code (pie chart)
- Distribution of blocked requests  (radar chart)
- Number of blocked requests (bar chart)
- OWASP Top 10 requests (bar chart)
- Reputation tags (pie chart)
- IP list reputation (bar chart)
