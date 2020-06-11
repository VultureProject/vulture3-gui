---
title: "Two-factor authentication repository"
currentMenu: otp
parentMenu: repositories
---

## Overview

Two-factor authentication is based on sending a one-time-password (OTP) to the user after a first successful authentication. <br/>
The user is going to receive his otp code by email or SMS and will have to provide it to Vulture. <br/>
Vulture will then check the received code and, if valid, it will let the user access his application. <br/>
Vulture also now support TOTP (Time-based OTP).<br/>
<br/>
This achieves strong authentication: The user first needs a valid login / password on a Vulture Repository **then** needs to confirm an OTP received by email / phone.


## OTP Repository

The following elements are required to create an OTP repository:

- `Repository Name`: A friendly name for your repo.
- `Otp Type:`: Select how to send the OTP to the user: by email or by phone.
- `Key length`: You can choose the length of the random OTP that will be send to the user.

For now vulture supports the following OTP system:
- [Authy](https://www.authy.com) for SMS OTP.
- Vulture email for Email OTP.

*Note that it is easy to add new OTP backend*, so feel free to [contact us](mailto: support@vultureproject.org) if you want support for other OTP systems

Once your repository is created, you can use it in any of your application that requires authentication. See [application authentication](/doc/application/auth.html) for details<br/>
`Note that OTP requires an LDAP, SQL or MongoDB authentication repository to work` <br/>
<br/>


### OTP by Email

You need to setup the SMTP relay that Vulture will use to send its email. <br/>
Check [SMTP settings](/doc/management/services.html) for details. <br/>
<br/>



### OTP by SMS
#### Authy

Vulture uses Authy API to send OTP. So you will need to provide you service `API KEY` for this to work. To obtain your key, go to the [Authy](https://www.authy.com/) portal and click on "Try It Now". <br/>
Fill in the required form, follow the tutorial to create your first app, then copy and paste your authy key:

![Authy-key](/doc/img/otp.png)
<br/>


### OTP by OneTouch
#### Authy

Vulture uses Authy API to verify authentication. It needs the Authy application to be installed on the user's mobile.<br/>
The OneTouch method does not use password, just a user validation in the Authy application.


### Time-base OTP

`Time-based OTP needs time precision.` <br/>
There is no setting to configure when choosing that type of authentication. <br/>
A TOTP application is needed on the user's mobile (like [Google Authenticator](https://play.google.com/store/apps/details?id=com.google.android.apps.authenticator2)). <br/> <br/>
The first time the user uses TOTP, a QRCode is displayed and he has to save-it into his application. `That QRcode is displayed once.` <br/>
Then, the user tape the code displayed on its mobile into Vulture portal OTP input. <br/> <br/>
That code is saved into Vulture internal database with AES cipher. If the user has lost his phone, just go to [SSO profiles](/repository/sso_profiles/) and delete the entry associated to the user.