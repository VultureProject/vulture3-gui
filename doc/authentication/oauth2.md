---
title: "OAuth2 responder"
currentMenu: oauth2
parentMenu: getting-started
---

## Overview

Vulture provides an internal OAuth2 responder that can be used with any authentication backend of type MongoDB, SQL, and LDAP.<br/>
To enable OAuth2 responder, simply activate the checkbox in the backend's configuration. <br/>
<br/>

Here are the available options:

 -  `Get Oauth2 scopes from these columns` : Additional backend's fields to return as a scope in the oauth2 token.
 -  `Form of returned values` : How to return the scope attributes: As a list (value,value,...) or as a dictionary (key=value).
 -  `Place of returned token` : How to return the scope: As JSON response, HTTP header or both.
 -  `Token time to live` : The oauth2 token lifetime.


*Note*: If you don't enable OAuth2 scope, it is still possible to obtain an oauth2 token, but no custom attribute will be returned.


## Obtain a token

You can obtain an authentication token from Vulture using the following HTTP *POST* request :
 - URI: `http(s)://<vultureIP:Port>/<Public_token_name>/portal/oauth2/login`
 - POST DATA: username=xxx&password=xxx&app_id=xxx

Public_token_name is configurable from ["Services / Vulture setting"](/doc/management/services.html)
app_id is the application's id of your app. You can find it in the GUI.

If authentication succeeds, you will get an HTTP response with an authentication token. <br/>
Depending of the Oauth2 repository configuration (.See below), the token may be returned: <br/>
 - In a 'Authorization' HTTP header
 - In a JSON response.
 - In a JSON response + 'Authorization HTTP header'.

The JSON token is with the following format: "485285e1-a4d2-4a5c-a012-12ca6d5fec1b"

There are two causes of failure:
 - OAuth2 responder is not enabled in the repository configuration ('OAuth2 tab'). You will receive a 403-FORBIDDEN.
 - Login / password are invalid: You will receive a 403-FORBIDDEN.

## Check the validity of a token and retrieve user' scope

Once you have a valid token, you can check if it's valid with the following HTTP *POST* request:
 - URI: `http(s)://<vultureIP:Port>/<Public_token_name>/portal/oauth2/token`
 - POST DATA: token=xxx

If the token is not valid, you will receive the following JSON response: ```{"active": "false"}```. <br/>
If the token is valid, you will receive the following JSON response:
```
{
    "active": "true",
    "scope": {
        'dn': 'uid=john_doe,ou=jdoe,ou=Users,dc=mycompany,dc=com',
        'cn': [' john.doe'],
        'memberOf': ['cn=group1', 'cn=group2'],
        'user_phone': 0122334455,
        'user_groups': ['cn=group1,ou=Policy,dc=mycompany,dc=com', 'cn=group2,ou=Policy,dc=mycompany,dc=com'],
        'password_expired': False,
        'account_locked': False,
        'user_email': john.doe@company.com
    }
}
```

If the token is invalid (expired or unknown), you will receive the following JSON response:
```
{
    "active": "false"
}
```
