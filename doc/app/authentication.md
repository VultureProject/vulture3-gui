---
title: "Authentication"
currentMenu: app_auth
parentMenu: app
---

## Overview

From this menu you can manage the authentication settings of your application. <br/>
Please consult the doc about [authentication concepts](/doc/authentication/auth.html) before.

![Authentification](/doc/img/authentification.png)

Here you can define if you want Vulture to :
 - Let user access to protected applications without authentication
 - Let user access to protected applications without authentication, but with an anonymous cookie so you can track connexion into Vulture's statistics
 - Let user access to protected applications with authentication

Authentication credentials are check against one of your [Authentication repositories](/doc/repositories/repo.html). <br/>
The ways Vulture will ask for credentials are :
 - Basic authentication: Vulture will prompt a login and a password with a "HTTP 401 Authorization Required"
 - HTLM Form: Vulture will display an HTML Form to prompt a login and a password
 - Kerberos Authentication: Vulture will try to get an existing Kerberos Ticket from the user's client, or will display a popup to prompt for a login and password to get one on your KDC


## Authentication settings

### Main settings

 - `Enable authentication`: Click to active authentication
 - `Track anonymous connexion`: If enable, mod_vulture will give an anonymous cookie to the user and create a corresponding session in Redis. This allows to keep trace of this connexion in Vulture's statistics (number of active anonymous connexions)
 - `Disconnect user from app after timeout`: Vulture will destroy the redis session of the user after this timeout, in seconds
 - `Restart timeout after a request`: If enable, the session timeout is restarted each time the user send a request to Vulture
 - `Select authentication type`: Sets how Vulture shoud ask for credentials, see below
 - `Primary authentication backend`: Set which [authentication repository](/doc/repositories/repo.html) to use for user authentication. Vulture will first try to authenticate user against this repository.
 - `Fallback authentication backend`: If set, and if authentication failed on the primary authentication repository, Vulture will try with this one.


### Basic authentication

Just select "Basic Authentication" for Vulture to ask login / password with a basic popup ("HTTP 401 Authorization Required", with "WWW-Authenticate: Basic"). <br/>
Never use this kind of authentication without a secure TLS connexion.


### HTML Form authentication

Select "HTML Form" to have Vulture display a login / password HTML form. <br/>
Never use this kind of authentication without a secure TLS connexion.    <br/>

Additional options are available for this kind of authentication:

- `Require Captcha`: If enable, the user will have to fill in the captcha in the authentication form
- `OTP Repository`: Choose an [OTP repository](/doc/repositories/otp.html) here if you want two-factor authentication. After successful verification of login/password, the user will receive a SMS or an email and will have to type in the code he receives for the authentication process to complete.

### Kerberos authentication

Just select "Kerberos Authentication" for Vulture to authenticate user with Kerberos. <br/>
Vulture will try to authenticate user by getting its Kerberos TGT ticket. If such a ticket is present, Vulture will query the KDC to verify the ticket validity. If the ticket is not valid, Vulture will deny the connexion. If no ticket is sent by the user, Vulture will prompt a login / password via a "HTTP 401 Authorization Required", with "WWW-Authenticate: Negotiate". Vulture will then try to obtain a ticket on the KDC with the provided credentials.<br/>
<br/>

### OAuth2 authentication

Just click on `Accept stateless OAuth2 tokens` for Vulture to let pass users which have a valid oauth2 token given in wanted header. <br/>
That header is by default `X-Vlt-Token` but can be modified in "Vulture management -> Services -> OAuth2 HTTP header".
See how OAuth2 runs at : ["Authentication / OAuth2"](/doc/authentication/oauth2.html).


### Advanced settings

 - `Force portal URI`: When you have several listeners associated to an application, Vulture will use the first available TLS listener and fallback to the first non-TLS if none is found. If you want to force the URI of the Vulture portal during redirection, define a URI here. For example: 'https://my-portal.com'. Note that the URI must resolve to Vulture for this to work.
 - `Force redirection to this URI after authentication`: After a successful authentication, you may want to redirect the user to a fixed URI. You can define this URI here.
