---
title: "Repositories"
currentMenu: repositories
parentMenu: repositories
---

## Overview

From this menu you can manage repositories used by Vulture. We make a distinction between `data repository` and `user repository`.

* A **Data Repository** is used to store logs and alerts
> Supported data repositories are: The internal MongoDB Engine, MongoDB, Elasticsearch, SYSLOG (read-only).

* An **Authentication Repository** is used to authenticate users
> Supported authentication repositories are: The internal MongoDB Engine, MongoDB, MySQL, PostgreSQL, LDAP, Active Directory, Kerberos.


The internal MongoDB Engine (**"Vulture Internal Database"**) is a special repository. It cannot be modified nor deleted and can be used as a data repository and authentication repository. This is the repository which contains Vulture GUI users and Vulture logs by default.

`On architecture with high traffic, it is not recommended to store logs inside the Vulture cluster, except if you are in a cluster with enough nodes`.

## Repositories


### LDAP / Active directory

Please see [LDAP repositories](/doc/repositories/ldap.html) for details.

### Kerberos

Kerberos repositories are used to authenticate user in a transparent manner as well as to propagate identities to web backends.
Indeed, Vulture is able to authenticate users:
  - Against Kerberos via a login and password.
  - Against Kerberos via a TGT ticket provided by the web browser or client application.

Unlike httpd for example, Vulture is also capable to propagate the Kerberos TGT ticket to the Web application backend. <br/>
Thus allowing Vulture to do fully transparent Web SSO from web browser to web backends.

Please see [Kerberos repositories](/doc/repositories/kerberos.html) for details.

### Radius

Vulture can authenticate users against a Radius backend. This feature is built on top of the pyrad implementation (https://pypi.python.org/pypi/pyrad).<br/>
Please see [Radius repositories](/doc/repositories/radius.html) for details.

### SQL

You can use a MySQL or PostgreSQL Database to authenticate your users with Vulture. <br/>
Please see [SQL repositories](/doc/repositories/sql.html) for details.


### Syslog

Vulture can forward its logs to external syslog servers. Vulture uses rsyslog (http://www.rsyslog.com/) for that purpose, so syslog capacities are very large.<br/>
The GUI only provide some basic features, but you can easily customize rsyslog configuration to meet your specific needs.<br/>
Please see [Syslog repositories](/doc/repositories/syslog.html) for details.

### Internal MongoEngine and external MongoDB

These repositories can be used to authenticate users and / or to store Vulture's logs.
Please see [MongoDB repositories](/doc/repositories/mongodb.html) for details.

### Elasticsearch

Elasticsearch can be used as a data repository, to store Vulture's logs.
Please see [Elastic repositories](/doc/repositories/elastic.html) for details.


## More authentication features...

### OTP / Two-factor authentication

You can create One Time Password (OTP) repositories so that your users, after been successfully authenticated on any **LDAP backend**, will receive a challenge by SMS or email. <br/>
They will need to provide this challenge back to Vulture to be fully authenticated. <br/>
<br/>
Vulture supports [Authy OTP](https://www.authy.com/), Time-base OTP (TOTP) and a custom OTP (simple email sent by Vulture).

Please see [OTP Configuration](/doc/authentication/otp.html) for details.

### Oauth2 responder
Please see [OAuth2 Authentication](/doc/authentication/oauth2.html) for details.
