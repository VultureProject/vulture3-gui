---
title: "Log Viewer"
currentMenu: logs
parentMenu: management
---

## Overview

Depending on its configuration, Vulture will send logs into its internal MongoDB Repository (default) or external Elastic or MongoDB.
There are different type of logs inside Vulture:
 - Internal Vulture logs (GUI, Portal, process...).
 - Internal Vulture diagnostic logs (updated every minute), [see diagnostic](/doc/monitoring/diagnostic.html).
 - Packet filter logs, [see pf](/doc/waf/pf.html).
 - Apache Worker logs, [see application](/doc/app/logs.html).

Several actions and options are available from the search toolbar :

*   `Search` : Shows the query builder form.
*   `Real Time` : Log display is updated continuously (every second).
*   `Configuration` : Shows the configuration form to customize your display.
*   `Date` : Date and time filter.
*   `Query` : The active query filter.
*   `Export to csv file` : You can export the query result into a CSV file.
*   `Reset` : Delete the query filter.
*   `Execute` : Execute the search query.
*   `Save as dataset` : After a query has been executed, you can save the resulting logs into a "Dataset". This dataset can be used later to build a mathematical model and find abnomalies based on SVM algorithms (Support Vector Machine). [See Machine Learning](/doc/waf/svm.md) for details.




<i class="fa fa-warning"></i>&nbsp;&nbsp;If you use ElasticSearch to store your logs, be careful of the version of the ElasticSearch python library.<br/>
You'll need to adapt it with your ElasticSearch version. See [ElasticSearch-PY version](https://elasticsearch-py.readthedocs.io/en/master/#compatibility)<br/>
To update the lib:
`/home/vlt-gui/env/bin/pip install elasticsearch==<version>`


## Query builder

The query builder let you build a query with AND / OR logic and save it for further reuse.
![Log builder](/doc/img/log-builder.png)

## Detail

When you click on a log line, you've got all the details on the log entry:
![Log detail](/doc/img/log-detail.png)

## Available actions when you "right click" on a line of log

### Add IP to blacklist"
 > This will automatically add the source IP address to `pf network Firewall` blacklist. See [PF Blacklist](/doc/waf/pf.md)

### Add whitelist/blacklist
 > A menu will appear with a modSecurity Rule Wizard. You will be able to review the rule automatically created for you and decide wether you want to accept or block the corresponding HTTP request. Once done, the rule will be automatically added to the blacklist / whitelist associated with the Web application. The corresponding rules are available in [WAF Ruleset](/doc/waf/ruleset.md).

 ![WLBL Builder](/doc/img/wl_bl.png)

 With this, you can build some ModSecurity Rules with data all the data of the selected log line.<br/>
 In this example: `SecRule REQUEST_URI "@contains id=1" "id:{id},deny,nolog,auditlog,msg:'BLACKLIST'"`<br/>
 With this rule, if the string "id=1" is found anywhere in the requested uri, ModSecurity will block it.


### Find related rules
 > This menu allows you to find all rules related to the log entry. This way you can edit / delete it.

  ![Find Rule](/doc/img/find_rule.png)


You will need to reload your application listener after that.
