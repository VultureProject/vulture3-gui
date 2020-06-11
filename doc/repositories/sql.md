---
title: "SQL repository"
currentMenu: sql
parentMenu: repositories
---

## Overview

SQL Databases can be used to authenticate users. <br/>
Vulture is using [SQL Alchemy](http://www.sqlalchemy.org/) for SQL support and currently supports MySQL and PostgreSQL databases <br/>.
<br/>

Note that we do not encourage using SQL database to authenticate users.<br/>
You will have a better experience with Vulture with LDAP repositories.<br/>

### Connection settings

- `Repository Name`: Friendly name that will be display in the GUI.
- `Database type`: MySQL or PostgreSQL.
- `Database host`: The IP address of your SQL database.
- `Database port`: The corresponding TCP port.
- `Database name`: The name of you database containing your users.
- `Username`: The SQL username allowed to query your database.
- `Password`: The corresponding SQL password.

You cannot save your LDAP configuration without clicking on "TEST LDAP connection". <br/>
This ensures that Vulture can login onto your SQL server using the provided login and password.

### User settings

Here you must define where are stored your user accounts:

- `User table name`: Name os the SQL table containign users.
- `Username column name`: Name of the login column inside the SQL table.
- `Password column name`: Name of the password column inside the SQL table.
- `Password hash algorythm` : Algorithm used for password hashing.
- `Password salt` : Optional salt field that is concatenated with the password before hashing.
- `Password salt position` : optional salt position.
- `Change pass column` : Name of the document field, inside the collection, that Vulture will check to know if the user MUST change his password.
- `Change pass expected value` : If the `Change pass field` contains this specific value, Vulture will inform the user that his password MUST be changed
- `Account locked column` : Name of the column, that Vulture will check to know if the user account is locked
- `Account locked expected value` : If the `Account locked column` contains this specific value, Vulture will deny the user
- `User mobile column name` : Name of the document field that contains the user's phone number. This is used by the [One Time Password](/doc/repositories/otp.html) authentication feature.
- `User email address column name` : Name of the document field that contains the user's email address. This is used by the [One Time Password](/doc/repositories/otp.html) authentication feature.


## OAuth2 settings

Please see [OAuth2 Authentication](/doc/authentication/oauth2.html) for details.
