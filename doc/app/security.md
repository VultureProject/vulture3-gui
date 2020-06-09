---
title: "Security settings"
currentMenu: security
parentMenu: app
---

## Overview

From this menu you can manage the security settings of your application.

## Security settings

### Global settings
 - `Use ACLs`: Choose here one or more [ACLs profiles](/doc/configuration/acl.html)
 - `Redirect http to https`: If enabled, Vulture will automatically redirect incoming HTTP request to HTTPS request. For that it will send an **HTTP 301 Permanent Redirect** response. Not that it can't work if you don't have at least one TLS profile associated to one of your listeners.
 - `Allowed HTTP Method`: By default Vulture only allows HEAD, GET and POST requests. If you need support for other HTTP METHOD, simply add them here. There is an auto-completion feature that helps you to add valid HTTP METHOD. For [Microsoft RPC-Over-HTTP](/doc/app/internet.html) you will typically need to add the HTTP METHOD "RPC_IN_DATA" and "RPC_OUT_DATA" here.
 - `Enable backend's cookies encryption`: If enabled, will encrypt ALL the cookies sent by the backend using a randomly generated key and iv with the selected cipher. (Note: Changing the cipher will invalidate all the current cookies)
 - `Cipher to use for backend's cookies`: Choose here the cipher to use for backend's cookies encryption.
 - `Protect <FORM> with CSRF token`: If enabled, Vulture will alter application's response body to insert an hidden CSRF field with a random value inside FORM. When the user will submit the form, Vulture will check if the CSRF field is present and if it match the expected value.
 - `Block Session Fixation`: If enabled, Vulture will block requests with a Cookie that has not been created before with a Set-Cookie
 - `Block Session / IP mismatch`: If enabled, Vulture will block requests if there is a change in the client's IP Address inside a given Session
 - `Block Session / User-Agent mismatch`: If enabled, Vulture will block requests if there is a change in the client's browser's User-Agent inside a given Session

### Source IP Reputation analysis
The source ip of clients will be checked against the reputation database which is a MaxmindDB file generated daily.
If the IP is found, a 403 forbidden will occur.<br/>
Reputation's database is loaded by mod_maxminddb at Apache startup

The download of new IP databases and the generation of the maxmindDB is done by a crontab, which occurs every day (Internet Access required). <br/>
When an IP is found in the database, you will be able to see its tags in the log viewer.

- `Block IP with the following tags`: Gives you the ability to block some [tags](/doc/management/reputation.html) associated to source IP addresses.<br/>
If reputation blocking is enable, mod_maxminddb will check if the client ip is found, it will retrieve the corresponding tags. <br/>
If one of the tags match a forbidden tag, Vulture will send a 403-FORBIDDEN HTTP response.

 - `Enable GeoIP`: Toggle this settings if you want Vulture to lookup the country of the source IP Address. This is based on GeoLite2 data created by MaxMind, available from
<a href="http://www.maxmind.com">http://www.maxmind.com</a>.
 - `Block following countries`: Enter the 2-letters code of countries you want to deny access from (blacklist).
 - `Only allow following countries`: Enter the 2-letters code of country you want to accept. Other countries will be denied (whitelist).

 - `High-precision GeoIP`: Toggle this setting if you want to lookup the city of the source IP Address. This is also bring by MaxMind.

### WAF policy settings
 - `Protect application with WAF profile`: Select here a [WAF profile](/doc/waf/policy.html) that will be used to protect your application against Web attacks.


### Machine Learning Protection (SVM: Support Vector Machines)
 - `Choose dataset and show graph`:

![SVM](/doc/img/data_received_by_server.png)
![SVM](/doc/img/ratio_data_received_sent.png)
![SVM](/doc/img/request_content_analysis.png)
![SVM](/doc/img/trafic_evolution_over_day_per_ip.png)
![SVM](/doc/img/trafic_evolution_over_day_per_user.png)
