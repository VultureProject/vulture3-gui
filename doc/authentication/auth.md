---
title: "Authentication concepts"
currentMenu: authentication
parentMenu: getting-started
---

## Overview

Vulture is a reverse proxy and can authenticate users **before** they access to protected web applications <br/>
The simplified authentication workflow works the following way:

![Authentication workflow](/doc/img/auth-flow.png)

During the redirection between mod_vulture and Vulture's portal, there is a temporary token created so that the portal can retrieve the session created by mod_vulture. <br/><br/>
The "anonymous tracking mode" allows to track the number of active sessions on Vulture: each session is registered in Redis cache. <br/>
<br/>
Here is the simplified flow-chart associated to the Vulture authentication portal :<br/>
![Authentication workflow](/doc/img/auth-portal-flow.png)
<br/><br/>
At any stage, when either a portal cookie or an application cookie is sent to Vulture, a check is done against Redis. <br/>
If the session corresponding to the cookie does not exists in Redis, Vulture will deny access.<br/>
<br/>
Depending of the authentication process stage, Vulture may:
 - Silently redirect to the authentication portal.
 - Deny access with a 403 - Forbidden.
<br/>
<br/>

Check against redis are done by mod_vulture: It's pretty fast. <br/>
`Redis is a critical component for Vulture`: In case of a failure in Redis, Vulture will send a HttpResponseServerError() django response (HTTP Error 500).
