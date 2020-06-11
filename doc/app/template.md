---
title: "Portal Template"
currentMenu: template
parentMenu: template
---

## Overview

From this menu you can manage portal templates and media (Images) used in vulture's dialog with users. <br/>
Portal templates are used whenever Vulture needs to interact with users <br/>
You can create as many templates as you need, and assign them in the [application configuration](/doc/app/backend.html) <br/>
In a template you can configure : <br/>
 - The global CSS form, used by all dialogs within the template.
 - The "Login" template, displayed during user authentication.
 - The "Logout" template, displayed whenever a user logs out an application, if configured in [application's config](/doc/app/sso_forward.html).
 - The "Learning" template, displayed during learning mode in [HTML Authentication](/doc/app/authentication.html).
 - The "Self-service" template, displayed when user accesses to the [self-service portal](/doc/authentication/self.html).
 - The "Password" template, displayed in user password change dialogs.
 - The "Email & Dialogs", used when Vulture send emails ([OTP](/doc/repositories/otp.html)) or displays status messages.
 - The "OTP" template, used when Vulture prompts for [OTP](/doc/repositories/otp.html) code.
 - The "Message" template, used for various Vulture messages, such as error message.
 - The "HTML Error" template, used for HTML response messages, when Error code 403-Forbidden, 404-NOT Found and 500-Server Error messages are triggered.

You will also be able to upload images so that you can used them into HTML templates. <br/>
<br>
In any tab of the template interface, you may **preview your work** by clicking on 'Preview'.<br/>
You can also **automatically insert image link**, by clicking on 'Show images' (See below).

If you want to use static element, such as CSS or JS script, you will need to place them first on *Every vulture nodes*. <br/>
The directory where to place static portal content is `/home/vlt-gui/vulture/portal/static/<some_content>`. <br/>
Once done, you will be able to access this content, `without any access control` from everywhere by using an HTML link with `src='templates/static/<some_content>'`. <br/>
 > Note that there is no '/' at the beginning of this URI.





## Portal templates

### Global Settings

 - `Friendly name`: A friendly name for the Portal template.

### Style

Here you may edit a global CSS style sheet. <br/>
This CSS will be available to every HTML templates defined below.

### Login

Here you may design the HTML form displayed when Vulture prompt for authentication. <br/>
The page will be displayed "as is" in the user's web browser. <br/>
You may use the following jinja2 tags inside the HTML content:
 - `{{style}}`: This tag will be replaced by the CSS style sheet created previously (see above).
 - `{{error_message}}`: The error message displayed if authentication goes wrong.
 - `{{form_begin}}`: The starting "&lt;form action='...'&gt;", **This is a mandatory tag**.
 - `{{form_end}}`: The ending "&lt;/form&gt;", **This is a mandatory tag**.
 - `{{input_login}}`: The Login Input for authentication portal, **This is a mandatory tag**.
 - `{{input_password}}`: The Password Input for authentication portal, **This is a mandatory tag**.
 - `{{input_submit}}`: The 'login' button, **This is a mandatory tag**.
 - `{{lostPassword}}`: The URI for lost password.
 - `{{captcha}}`: This tag will be replaced by a captcha, if configured in application's [HTML Authentication](/doc/app/authentication.html).
 - `{{input_captcha}}`: The captcha text input zone.


### Logout

Here you can design the HTML form displayed when Vulture destroys the user session, after user clicks on the ['disconnect URI'](/doc/app/sso_forward.html) <br/>
The page will be displayed "as is" in the user's web browser. <br/>
You may use the following jinja2 tags inside the HTML content:
 - `{{style}}`: This tag will be replaced by the CSS style sheet created previously (see above).

### Learning

Here you can design the HTML form displayed when Vulture ask for data to be [learned](/doc/app/sso_forward.html).
The page will be displayed "as is" in the user's web browser. <br/>
You may use the following jinja2 tags inside the HTML content:
 - `{{style}}`: This tag will be replaced by the CSS style sheet created previously (see above).
 - `{{form_begin}}`: The starting "&lt;form action='...'&gt;", **This is a mandatory tag**.
 - `{{form_end}}`: The ending "&lt;/form&gt;", **This is a mandatory tag**.
 - `{{input_submit}}`: All the input fields needed for learning, **This is a mandatory tag**.

### Self-service

Here you can design the HTML form displayed when the user access the [self-service portal](/doc/authentication/self.html).
The page will be displayed "as is" in the user's web browser. <br/>
You may use the following jinja2 tags inside the HTML content:

 - `{{application_list}}`: A list of applications on which the user has access. Applications have the following attributes:
    - `{{name}}`: The friendly name of the application.
    - `{{uri}}`: The public URI of the application.
    - `{{status}}`: Indicates whether the user has an active session on the application.
 - `{{style}}`: The Cascading Style sheet section.
 - `{{changePassword}}`: The URI to change the user's password.
 - `{{logout}}`: The URI to disconnect from all applications (full portal disconnection).
 - `{{username}}`: The name of the current logged user.
 - `{{error_message}}`: A Vulture message telling what happens during [self-service portal](/doc/authentication/self.html) dialogs (ex: "Your password has been changed", see below).

### Password

Here you may design the HTML form displayed when the user wants to change its password. This is the same template used when the user wants to interactively change its password or when the user wants to reset his password by email (without knowing the old password). You will notice a 'If' statement in this template to handle both cases.
The page will be displayed "as is" in the user's web browser. <br/>
You may use the following jinja2 tags inside the HTML content:
 - `{{style}}`: The Cascading Style sheet section.
 - `{{form_begin}}`: The starting "&lt;form action='...'&gt;", **This is a mandatory tag**.
 - `{{form_end}}`: The ending "&lt;/form&gt;", **This is a mandatory tag**.
 - `{{input_password_old}}`: The old password input, **This is a mandatory tag**.
 - `{{input_password_1}}`: The new password input (#1), **This is a mandatory tag**.
 - `{{input_password_2}}`: The new password input (#2), **This is a mandatory tag**.
 - `{{input_email}}`: The email input, to recover password, **This is a mandatory tag**.
 - `{{input_submit}}`: The 'submit' button, **This is a mandatory tag**.
 - `{{dialog_change}}`: Boolean: True if password changes.
 - `{{dialog_lost}}`: Boolean: True if lost password..
 - `{{error_message}}`: The message telling what happened.

### Emails & Dialogs

You can customize various messages used in Vulture's Email or error messages:
 - `Email From:`: The email's "from" address used to send Vulture's [OTP](/doc/repositories/otp.html) email messages.
 - `Email Subject:`: The email's subject used to send Vulture's [OTP](/doc/repositories/otp.html) email messages.
 - `Email Body:`: The email's content used to send Vulture's [OTP](/doc/repositories/otp.html) email messages.
 - `'Password has been changed'`: The message displayed when password has been changed in the self-service.
 - `'Password cannot be changed'`: The message displayed when password cannot been changed in the self-service.
 - `'An email has been sent'`: The message displayed when a 'reset password email' has been sent.

You may use the following jinja2 tags inside the **Email body** for OTP messages:
 - `{{resetLink}}`: The URI of the reset link for password. It will point on the Vulture's [self-service portal](/doc/authentication/self.html). **This is a mandatory tag**
 - `{{app.name}}`: The name of the application from which the users want to reset their password.
 - `{{app.url}}`: The URL of the application from which the users want to reset their password.

### OTP

Here you can design the HTML form displayed when the user has to type in its OTP code.<br/>
The page will be displayed "as is" in the user's web browser. <br/>
You may use the following jinja2 tags inside the HTML content:

 - `{{style}}`: The Cascading Style sheet section.
 - `{{error_message}}`: The error message when OTP code verification goes wrong.
 - `{{form_begin}}`: The starting "&lt;form action='...'&gt;", **This is a mandatory tag**.
 - `{{form_end}}`: The ending "&lt;/form&gt;", **This is a mandatory tag**.
 - `{{input_key}}`: The key input, **This is a mandatory tag**.
 - `{{input_submit}}`: The 'login' button, **This is a mandatory tag**.
 - `{{resend_button}}`: The 'resend mail/sms' button.
 - `{{qrcode}}`: The 'src' html tag of the TOTP QRcode. (Only with TOTP authentication).

### Message

This is a generic template used to display generic message, when needed by Vulture.
The page will be displayed "as is" in the user's web browser. <br/>
You may use the following jinja2 tags inside the HTML content:

 - `{{style}}`: The Cascading Style sheet section.
 - `{{message}}`: The message displayed by Vulture.
 - `{{link_redirect}}`: A link displayed by Vulture to go back to somewhere.

### HTML Errors

Here you can customize the HTML error messages that Vulture can display when :
 - A 403 Error code is sent (ex: When Vulture denies a connection for security reasons).
 - A 404 Error code if a resource is not found.

> Note that by default, Vulture will forward backend's error messages. <br/>
> If you want Vulture to override backed's error messages with these ones, you will need to [configure it](/doc/app/backend.html).


## Images

From this tab you can upload Images into Vulture's MongoEngine database. Once uploaded, Image may be inserted inside above HTML templates. Just click on "Show image", then select your image and its URI will be automatically copied into clipboard. <br/>
You then only have to press CTRL+V to paste the link in your tempalte HTML FORM. Don't forget to add the &lt;img src=''&gt; tag for the image to render properly.
<br/><br/>
In your template, you should have something like that:
```
<img src='portal_statics/fb0f91b75a87b75f6cc9851cd53432b825cc0c55'/>
```
