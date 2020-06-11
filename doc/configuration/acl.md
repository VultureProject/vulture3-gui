---
title: "ACLS"
currentMenu: acl
parentMenu: configuration
---

## Overview

Vulture can perform access control before accepting to serve a request. <br/>
Here you can create ACLs to allow or deny requests based on several criteria:
 - HTTP method,
 - Client IP address,
 - Apache Expression,
 - Apache environment variable, ...

You can also check that, after a successful authentication, a users satisfies with the ACL. Indeed, Vulture can check that the login is the expected one or that the user belongs to specific groups.

## ACL policy

Here you can define ACLs that are based on Apache `mod_auth* modules`. Here are the modules that are enabled by default for authorization control inside Vulture:
 - authz_core_module.
 - authz_user_module.
 - authz_host_module.

Inside the Vulture's configuration files, directives are placed like that :
```
<RequireAll>
  <RequireAny>
     #Your ACL_1
  </RequireAny>
  <RequireAny>
     #Your ACL_2
  </RequireAny>
</RequireAll>
```

Please refer to the Apache documentation to create ACLs based on theses modules: https://httpd.apache.org/docs/2.4/mod/mod_authz_core.html.


## Users & Groups ACL

**User and groups ACL requires an LDAP authentication backend.** <br/>
To create a user and / or group based ACL, you need to configure the following things:

 - `LDAP backend`: Your authentication LDAP repository.
 - `Base DN:`: It will be automatically filled, based on your LDAP repository;
 - `User DN:`: It will be automatically filled, based on your LDAP repository.
 - `Group DN:`: It will be automatically filled, based on your LDAP repository.
 - `Authorized users`: Type the list of allowed users. **There is auto completion with LDAP users found in your repository**.
 - `Authorized groups`: Type the list of allowed groups. **There is auto completion with LDAP groups found in your repository**.

 **Note**: If you specify both users and groups, Vulture will do a "LOGICAL AND". The ACL will be satisfied only if both the user is explicitely allowed **AND** the user belongs to one of the group.
