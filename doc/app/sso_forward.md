---
title: "SSO Forward"
currentMenu: sso_forward
parentMenu: app
---

## Overview

Once a user is logged on Vulture, it is not yet authenticated on the web application.<br/>
The user will have to manually login on the application by supplying login / password or whatever... <br/>
<br/>
If you configure what we call **SSO Forward** here, Vulture will be able to:<br/>
 1. Propagate the credentials provided by the user to the protected application. We call that **"Autologon"**.
 2. Propagate other credentials, previously stored in Vulture. We call that **"SSO Learning"**.


![SSO](/doc/img/sso.png)

## SSO Forward settings

### Main settings

 - `Enable SSO Forward`: Click to enable SSO Forward
 - `Follow the 30[1|2] redirection after SSO request`: **AFTER** the SSO Forward request, the web application may perform a 30X HTTP redirection. This setting lets you choose if you want Vulture to follow this redirection or to ignore it.
 - `Immediately return the SSO response`: By default, **AFTER** the SSO Forward request, Vulture will redirect the user to the URI it initially asked for. Thus, HTTP response of the application is ignored from the user point of view. You can break this workflow and immediately return the application's response to the user by toggling this setting.
 - `Use Vulture User-Agent`: If enabled, HTTP request between Vulture and the application, **DURING SSO Forward**, will be done with a special 'Vulture-3.0' User-Agent HTTP Header. This allow you to distinguish Vulture authentication requests in your application's logfiles.
 - `URL to disconnect from your private application`: When a user will request this **relative URI**, Vulture will destroy the session in Redis, thus disconnect the user from Vulture.
 - `Display the logout message from template`: If a user click on a disconnect URI, he will be redirected to the root directory of the application. If you want to display an "HTML logout form" from Vulture's [Portal template](/doc/app/template.html), toggle this option.
 - `Destroy portal session on disconnect`: When a user click on a disconnect URI, his session is destroyed on the application, but not on the [Vulture portal](/doc/authentication/self.md). If you also want to destroy the portal session on disconnect, toggle this option.

##### For all of the authentication methods bellow, the `SSO URL` field behavior has changed since version **1.62**. <br>
If the pattern **[ ]** is found in the field value, it will be **replaced by the url of the backend (private uri)**. <br>
We have implemented that behavior to fully support SSO with ProxyBalancer.
Ideed, the pattern will be replaced by the first member private url, and if the connection fail the next member will be contacted. <br>
For example :
> if I enter **"[ ]/logon.html"** in `SSO URL` and I have 2 members in my **ProxyBalancer** configuration having the urls :
> - http://192.168.1.50/post/,
> - http://192.168.1.51/post/,
>
> The SSO will be performed on http://192.168.1.50/post/logon.html and if it fail it will be performed on http://192.168.1.51/post/logon.html. <br>

##### Furthermore, if you have the 2 caracters **\[** and **\]** but you don't want them to be interpreted, simply escape them by respectively **\\\[** and **\\\]**.

### SSO Forward using Basic authentication

 - `Forward credentials`: If set to "using Autologon", Vulture will authenticate on the Application using credentials provided by the user. If set to "using SSO Learning", Vulture will authenticate on the Application using previously learned credentials.
 - `Send Authorization header only to the login page`: By default, Vulture will send the "Authorization" header in every request to the Web application. If you only want to send the header to the login page, toggle this option.
 - `URL to login to your private application`: You have to define the FULL URI of the login page, if you have enable the previous option.

### SSO Forward using HTML Form

- `URL to login to your private application`: You have to define the FULL URI of the login page. Vulture will POST credentials to this page in an automated manner:
 1. Vulture will first do a HTTP GET on the page.
 2. Then it will detect the authentication FORM.
 3. Then it will fill in the FORM with credentials and DATA given by the user (autologon) or previously saved (learning).
 4. Then it will submit the FORM.

 - `Content-Type of POST Request`: You can specify here the format of the POST content that vulture will send to the application.
 - `SSO Forward Status`: This indicates if you successfully performed the SSO Wizard.

** HTML Form WIZARD**

First, fill in the `URL to login to your private application` field. Then click on 'Wizard'. <br/>
When clicking on Wizard, Vulture will:
 1. Send a GET request to the "URL to login".
 2. Display the list of all HTML FORM it has detected inside the page.

Inside the HTML FORM corresponding to the Login form of your application, you will have to tell to Vulture what it should POST to the application for login. <br/>
Here are the field type available:
 - `OAuth2 Token`: Vulture will fill in the field with the OAuth2 token associated with the user session.
 - `Dynamic Value`: Vulture will fill in the field with the value set by the application itself.
 - `Autologon User`: Vulture will fill in the field with the login provided by the user during authentication.
 - `Autologon Password`: Vulture will fill in the field with the password provided by the user during authentication.
 - `Custom Text Value`: Vulture will fill in the field with this static value.
 - `Learning`: Vulture will first prompt the user for the value, after authentication. Then, when the user logs in later on, Vulture will automatically send this stored value.
 - `Learning Secret`: Same as above, but the field is prompted using a PASSWORD box, not a TEXT box

Learned values are stored inside Vulture in the MongoEngine database. <br/>
Values are encrypted using AES256, with a KEY derived from the following attributes :
 - Vulture's internal Django SECRET_KEY.
 - Vulture's internal Application ID.
 - Vulture's internal Authentication Backend ID.
 - Login of the user.
 - Name of the learning field.

Using the Wizard, you can also send custom fields to the protected application. <br/>
These fields may be sent as **POST content**, or as **HTTP Cookie**. <br/>
Just click on 'Add Custom Field'.


### SSO Forward using Kerberos authentication

 - `Kerberos service of the app`: This is the service name used by the Kerberos-protected application to verify TGTs on the KDC
 - `Forward credentials`:

    - If set to "using Autologon", Vulture will authenticate on the Application using:
        1. kinit on the KDC, with credentials provided by the user to obtain a TGT.
        2. Send WWW-Authorization: Negotiate <TGT> in each following requests.

   - If set to "using SSO Learning", Vulture will authenticate on the Application using:
        1. kinit on the KDC, with credentials previously learned to obtain a TGT.
        2. Send WWW-Authorization: Negotiate <TGT> in each following requests.

 - `Send Authorization header only to the login page`: By default, Vulture will send the "Authorization" header in every request to the Web application. If you only want to send the header to the login page, toggle this option. **This is probably not what you want with Kerberos authentication, so you should probably not enable this**.
 - `URL to login to your private application`: You have to define the FULL URI of the login page, if you have enabled the previous option.
