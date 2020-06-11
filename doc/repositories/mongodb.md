---
title: "MongoDB Repository"
currentMenu: mongodb
parentMenu: repositories
---

## MongoDB repositories

MongoDB can be used as an authentication backend or as a data repository for logs.


### Vulture Internal Database (MongoDBRepository)

This is the internal mongodb database for the Vulture cluster. You cannot configure anything about it, but you can use this database to authenticate users or to store logs into it.
We do not recommend using this database for storing huge volume of logs, except if you are running a Vulture cluster with good performances (use an external elastic repo whenever you can).

Under normal conditions there is no need to connect to the Vulture's database.<br/>
> Just in case, here is the command to obtain a shell on the mongodb database:
> ```
> mongo --ssl --sslPEMKeyFile /var/db/mongodb/mongod.pem 127.0.0.1:9091/vulture
> ```
> Use it with caution, you have been warned :-)

Remember you can't write to a mongoDB SECONDARY slave. You will have to connect to the PRIMARY for any write operation.


### MongoDB repository


#### Connection settings


The following information will be required to create a MongoDB repository:


* `Repository name` : A friendly name for your repo.
* `Repository type` : You have to choose the purpose of the repo: 'Data' or 'Authentication' repository.
* `Database host` : The IP address of your mongoDB server.
* `Database port` : The mongoDB TCP port to use.
* `Replicaset` : If your mongoDB server is part of a cluster, choose the Replica Set of the cluster.
* `Client certificate` : If the mongoDB requires a client certificate, you can use the one selected here. See [PKI Management](/doc/management/pki.html) to know how to add certificates inside Vulture.
* `Database name` : Name of the mongoDB database to use for the repo.
* `Username` : MongoDB username.
* `Password` : Corresponding MongoDB password.


Please note that:
 - Vulture does not support user groups inside MongoDB. [Use LDAP for that](/doc/repositories/ldap.html).
 - Vulture requires you to choose a client certificate to connect to TLS mongoDB Server. If no certificate is selected, Vulture will use plaintext unencrypted connection.


When clicking on "Test User authentication settings", you can test if your settings are good. Vulture will prompt for a login and a password and will try to fetch user's email and phone number.
If authentication is unsuccessful, the error message should indicates the reason. Usually this is because of an authentication failure or wrong LDAP filters / attributes.


#### Users settings (Authentication repository)

You must fill in this field in case you are creating an authentication repository.

* `User collection name` : Name of the MongoDB collection that contain users.
* `Username field name` : Name of the document field, inside the collection, that contains the user's login.
* `Username's password field name` : Name of the document field, inside the collection, that contains the user's password.
* `Password hash algorythm` : Algorithm used for password hashing.
* `Password salt` : Optional salt field that is concatenated with the password before hashing.
* `Password salt position` : optional salt position.
* `Change pass field` : Name of the document field, inside the collection, that Vulture will check to know if the user MUST change his password.
* `Change pass expected value` : If the `Change pass field` contains this specific value, Vulture will inform the user that its password MUST be changed
* `User mobile field name` : Name of the document field that contains the user's phone number. This is used by the [One Time Password](/doc/repositories/otp.html) authentication feature.
* `User email address field name` : Name of the document field that contains the user's email address. This is used by the [One Time Password](/doc/repositories/otp.html) authentication feature.


Once these field are filled, this is recommended to test authentication by clicking on "Test user authentication settings". Vulture will prompt for a login and a password and will try to authenticate against the mongoDB repository.
If it succeed, email and phone number of the user will be displayed on screen. In case of a failure, Vulture will display the error message.

#### Data settings (Data repository)

Logs are sent to MongoDB through rsyslog. <br/>
You must fill in this field in case you are creating a data repository, to store Vulture logs.

* `Access collection name` : Name of the MongoDB collection that will contain Vulture's Apache worker access logs


Please note that when using MongoDB to store logs, Vulture uses some hardcoded collection name for its internal logs.
These names cannot be changed:
 - `vulture_pf`: is used to hold the pf firewall logs
 - `vulture_logs`: is used to hold the Vulture's internal logs (GUI, PORTAL, ...)
 - `vulture_fail2ban`: is used to hold the fail2ban logs
 - `vulture_diagnostic`: is used to hold the Vulture's diagnostic logs


#### OAuth2 settings (Authentication repository)

Please see [OAuth2 Authentication](/doc/authentication/oauth2.html) for details.
