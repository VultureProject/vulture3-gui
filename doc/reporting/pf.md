---
title: "Reporting Packet Filter"
currentMenu: pf
parentMenu: reporting
---

![Vulture GUI](/doc/img/report_pf.png)

This page displays several charts which allows you to see incoming and outgoing traffic captured by Packet Filter.<br/>
It searches and aggregates data from the data logs repository of your applications within the `vulture pf` database.<br/>
To get data on this page, you need to setup a [data repository](/doc/repositories/repo.html) for [packet filter](/doc/waf/pf.html).<br/>

- `Node` : Filter by vulture node.
- `Date` : Filter by a date range (precision of line charts depends on date range length).

Charts splitted in two sections (incoming and outgoing) available on this page:
- Number of hits (line chart)
- Source IP (pie chart)
- Destination IP (radar chart)
- Firewall actions (pie chart)
- Requests per destination port (bar chart)
