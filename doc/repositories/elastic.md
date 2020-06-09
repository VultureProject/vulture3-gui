---
title: "Elastic repository"
currentMenu: elastic
parentMenu: repositories
---

## Overview

Elasticsearch can be used as a data repository, to store Vulture's logs.<br/>
Warning: The minimal version of ElasticSearch is 2.3.x.

### Connection settings

You will need to provide the following information to create en elastic repo: <br/>
 <br/>


*   Repository name: "Friendly name" for the repository
*   Hosts list: List of Elastic HTTP hosts IP addresses. Use a comma to separate entries. _Ex : \(http://192.168.0.100:9200, http://192.168.0.101:9200 )_
*   Username: Username to use if Elastic requires HTTP basic authentication
*   Password: Password use if Elastic requires HTTP basic authentication

Please note that Vulture does not support, yet, sending logs to Elasticsearch over TLS. <br/>

You cannot save your configuration without clicking on "TEST Elasticsearch connection". <br/>
This ensures that Vulture can connect to elastic cluster.


### Data settings

Logs are sent to Elastic through rsyslog. <br/>
Here you can configure the indexes name and type to use with elastic.

* `Date format`: Format to use for the full index name (ex: `vulture_access-<DATE FORMAT>`).
* `Index name (Access logs)`: Name of the index used to store Apaches's access.log.
* `Type name (Access logs)`: Name of the document type used to store Apaches's access.log.

Please note that when using Elastic to store logs, Vulture uses some hardcoded index and type names for its internal logs.
These names cannot be changed:
 - `vulture_pf-<DATE_OF_DAY>`: is the index used to hold the pf firewall logs.
 - `vulture_fail2ban-<DATE_OF_DAY>`: is the index used to hold the fail2ban logs.
 - `vulture_logs-<DATE_OF_DAY>`: is the index used to hold the Vulture's internal logs (GUI, PORTAL, ...).
 - `vulture_diagnostic-<DATE_OF_DAY>`: is the index used to hold the Vulture's diagnostic logs.
