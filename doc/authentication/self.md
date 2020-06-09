---
title: "Self-service portal"
currentMenu: self
parentMenu: getting-started
---

## Overview

Any authenticated user may access a "self-service portal" from which it will be able to perform several operations:
 - See what are the applications available for him.
 - Change its password.

The self-service is also available for anonymous users, if they previously have received an email when they lost their password.<br/>
The appearance and the content of the self-service portal is defined from the [Portal template](/doc/app/template.html) configuration.

## How to access the self-service

The self-service may be accessed through the following URI:

```
http(s)://<public_uri>/<public_token_name>/self
```
 - public_uri is your application's public URI.
 - public_token_name is configurable from ["Services / Vulture setting"](/doc/management/services.html).

**Note: https should always be used when accessing the self-service portal.**

Here is an example of a valid self-service URI: **http://www.example.com/99fa9c9f9dcb141a/self**.


## Self-service content

### Password change

If the self-service template contains the ``{{changePassword}}`` tag , the password change link will be displayed:
```
http(s)://<public_uri>/<public_token_name>/self/change
```
If the user clicks on this link, Vulture will show the change password HTML form. <br/>
If something goes wrong during password change, Vulture will display an error message. It will display a success message otherwise. Message can be customized from the [Portal template](/doc/app/template.html) configuration

**Note: If the old password is not good, Vulture won't display any error message.**

### Password lost

Self-service portal is also available for anonymous users who wants to reset their password. <br/>
The tag `{{lostPassword}}` may for example be added on the login form so the user may ask for its password reset.<br/><br/>
The lost password link is:
```
http(s)://<public_uri>/<public_token_name>/self/lost
```
If the user click on this link, Vulture will show the "lost password" HTML form. In this form he will have to provide its email address. Note that this email address should be associated to the user's account inside the authentication repository. Of course, **"User email address column name"** MUST be correctly defined in the [repository configuration](/doc/repositories/repo.html)

<br/>
Thanks to the public_uri, Vulture will know on which application the user wants to reset his password and thus will be able to found the correct authentication repository.<br/>
<br/>
If the user submits a valid email address, he will receive a email containing the link to reset his password.
If the user submits a invalid email address, no email will be send, but Vulture will still display the 'an email has been sent' message, for security reasons. The email received by the user contains a link that is only valid during a short period of time: **10 minutes**. During 10 minutes, the temporary key will be hold in Redis session, and will be counted into ["password reset statistics"](/doc/monitoring/general.html).
