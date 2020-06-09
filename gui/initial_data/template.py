#!/usr/bin/python
#-*- coding: utf-8 -*-
"""This file is part of Vulture 3.

Vulture 3 is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Vulture 3 is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Vulture 3.  If not, see http://www.gnu.org/licenses/.
"""
__author__ = "Jérémie Jourdin"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = 'Initial data of Template model'

from django.template import Context, Template

from gui.models.template_settings import portalTemplate


class Import(object):

    def process(self):
        """ Function in charge to import Vulture Template into database

        :return:
        """
        try:
            portalTemplate.objects.get(name='My Template')
            print("Default Template already inserted")
        except portalTemplate.DoesNotExist as e:
            template = portalTemplate(name="My Template", html_login="", css="")
            template.error_password_change_ok = "Your password has been changed"
            template.error_password_change_ko = "Error when trying to change your password"
            template.error_email_sent = "An email has been sent to you with instructions to reset your password"
            tpl_list = ('html_login',
                        'html_logout',
                        'html_otp',
                        'html_learning',
                        'html_message',
                        'html_registration',
                        'email_register_subject',
                        'email_register_body'
                        'html_self',
                        'html_password',
                        'email_subject',
                        'email_body',
                        )


            template.html_login = """<!DOCTYPE html>
<html>
 <head>
    <meta charset="utf-8" />
    <title>Vulture Login</title>
    <link rel="stylesheet" href="templates/static/html/bootstrap.min.css" integrity="sha384-1q8mTJOASx8j1Au+a5WDVnPi2lkFfwwEAa8hDDdjZlpLegxhjVME1fgjWPGmkzs7" crossorigin="anonymous">
    {{style}}
 </head>
 <body>
    <div class="container">
        <div class="card card-container">
            {{form_begin}}
                <img id="vulture_img" src="templates/static/img/vulture-logo-small.png"/>
                {% if error_message != "" %}
                  <div class="alert alert-danger" role="alert">{{error_message}}</div>
                {% endif %}
                <span id="reauth-email" class="reauth-email"></span>
                {{input_login}}
                {{input_password}}
                {% if captcha %}
                    {{captcha}}
                    {{input_captcha}}
                {% endif %}
                {{input_submit}}
                <a href='{{lostPassword}}'>Forgotten password ?</a>
            {{form_end}}
        </div>
    </div>
 </body>
</html>
"""

            template.html_logout = """<!DOCTYPE html>
<html>
 <head>
    <meta charset="utf-8" />
    <title>Vulture Logout</title>
     <link rel="stylesheet" href="templates/static/html/bootstrap.min.css" integrity="sha384-1q8mTJOASx8j1Au+a5WDVnPi2lkFfwwEAa8hDDdjZlpLegxhjVME1fgjWPGmkzs7" crossorigin="anonymous">
     {{style}}
 </head>
 <body>
    <div class="container">
        <div class="card card-container" style="text-align:center;">
            <p style="font-size:15px;font-weight:bold;">You have been successfully disconnected</p>
            <a href='{{app_url}}'>Return to the application</a>
        </div>
    </div>
 </body>
</html>"""

            template.html_learning = """<!DOCTYPE html>
<html>
 <head>
    <meta charset="utf-8" />
    <title>Vulture Learning</title>
    <link rel="stylesheet" href="templates/static/html/bootstrap.min.css" integrity="sha384-1q8mTJOASx8j1Au+a5WDVnPi2lkFfwwEAa8hDDdjZlpLegxhjVME1fgjWPGmkzs7" crossorigin="anonymous">
    {{style}}
 </head>
 <body>
    <div class="container">
        <div class="card card-container" style="text-align:center;">
            <p>Learning form</p>
            {{form_begin}}
                {{input_submit}}
            {{form_end}}
        </div>
    </div>
 </body>
</html>"""

            template.html_self = """<!DOCTYPE html>
<html>
 <head>
    <meta charset="utf-8" />
    <title>Vulture Self-Service</title>
    <link rel="stylesheet" href="templates/static/html/bootstrap.min.css" integrity="sha384-1q8mTJOASx8j1Au+a5WDVnPi2lkFfwwEAa8hDDdjZlpLegxhjVME1fgjWPGmkzs7" crossorigin="anonymous">
    {{style}}
 </head>
 <body>
    <div class="container">
        <div class="card card-container" style="text-align:center;" id="self_service">
            <img id="vulture_img" src="templates/static/img/vulture-logo-small.png"/>
            <br><br>
            {% if error_message != "" %}
                <div class="alert alert-danger">{{error_message}}</div>
            {% endif %}
            <p>Hello <b>{{username}}</b>!</p>
            <p>You currently have access to the following apps:</p>
            <ul class="list-group">
                {% for app in application_list %}
                  <li class="list-group-item"><b>{{app.name}}</b> - <a href='{{app.url}}'>{{app.url}}</a>{% if app.status %}<span class="badge">Logged</span>{% endif %}</li>
                {% endfor %}
            </ul>
            <a href="{{changePassword}}">Change password</a>
            <br><a href="{{logout}}">Logout</a>
        </div>
    </div>
 </body>
</html>"""

            template.html_password = """<!DOCTYPE html>
<html>
 <head>
    <meta charset="utf-8" />
    <title>Vulture Change Password</title>
    <link rel="stylesheet" href="../templates/static/html/bootstrap.min.css" integrity="sha384-1q8mTJOASx8j1Au+a5WDVnPi2lkFfwwEAa8hDDdjZlpLegxhjVME1fgjWPGmkzs7" crossorigin="anonymous">
    {{style}}
 </head>
 <body>
    <div class="container">
        <div class="card card-container" style="text-align:center;">
            {{form_begin}}
                <img id="vulture_img" src="templates/static/img/vulture-logo-small.png"/>
                {% if error_message %}
                    <div class="alert alert-danger">{{error_message}}</div>
                {% endif %}
                {% if dialog_change %}
                    <p>Please fill the form to change your current password :</p>
                    {{input_password_old}}
                    {{input_password_1}}
                    {{input_password_2}}
                    {{input_submit}}

                {% elif dialog_lost %}
                    <p>Please enter an email address to reset your password:</p>

                    {{input_email}}
                    {{input_submit}}

                {% endif %}
            {{form_end}}
        </div>
    </div>
 </body>
</html>
"""

            template.html_otp = """<!DOCTYPE html>
<html>
 <head>
    <meta charset="utf-8" />
    <title>Vulture OTP Authentication</title>
    <link rel="stylesheet" href="templates/static/html/bootstrap.min.css" integrity="sha384-1q8mTJOASx8j1Au+a5WDVnPi2lkFfwwEAa8hDDdjZlpLegxhjVME1fgjWPGmkzs7" crossorigin="anonymous">
    {{style}}
 </head>
 <body> 
    <div class="container">
        <div class="card card-container" style="text-align:center;">
            {% if error_message != "" %}
                  <div class="alert alert-danger" role="alert">{{error_message}}</div>
            {% endif %}
            <p>OTP Form</p>
            {{form_begin}}
                {{input_key}}
                {{input_submit}}
            {{form_end}}
            {{form_begin}}
                {% if resend_button %}
                    {{resend_button}}
                {% endif %}
                {% if qrcode %}
                    <p>Register the following QRcode on your phone :
                    <img {{qrcode}} alt="Failed to display QRcode" height="270" width="270" />
                    </p>
                {% endif %}
            {{form_end}}
        </div>
    </div>
 </body>
</html>
"""

            template.html_message = """<!DOCTYPE html>
<html>
 <head>
    <meta charset="utf-8" />
    <title>Vulture Info</title>
    <link rel="stylesheet" href="templates/static/html/bootstrap.min.css" integrity="sha384-1q8mTJOASx8j1Au+a5WDVnPi2lkFfwwEAa8hDDdjZlpLegxhjVME1fgjWPGmkzs7" crossorigin="anonymous">
    {{style}}
 </head>
 <body>
    <div class="container">
        <div class="card card-container">
            <img id="vulture_img" src="templates/static/img/vulture-logo-small.png"/>
            <p>{{message}}</p>
            {% if link_redirect %}<a href='{{link_redirect}}'>Go back</a>{% endif %}
        </div>
    </div>
 </body>
</html>"""

            template.html_registration = """<!DOCTYPE html>
<html>
 <head>
    <meta charset="utf-8" />
    <title>Titre</title>
    <link rel="stylesheet" href="templates/static/html/bootstrap.min.css" integrity="sha384-1q8mTJOASx8j1Au+a5WDVnPi2lkFfwwEAa8hDDdjZlpLegxhjVME1fgjWPGmkzs7" crossorigin="anonymous">
    {{style}}
 </head>
 <body>
    <div class="container">
        <div class="card card-container" style="text-align:center;">
            {{form_begin}}
                <img id="vulture_img" src="templates/static/img/vulture-logo-small.png"/>
                {% if error_message %}
                    <div class="alert alert-danger">{{error_message}}</div>
                {% endif %}
                {{captcha}}
                {{input_captcha}}
                {% if step2 %}
                    <p>Please fill the form to register your account :</p>
                    {{input_username}}
                    {% if ask_phone %}
                    {{input_phone}}
                    {% endif %}
                    {{input_password_1}}
                    {{input_password_2}}
                    {{input_submit}}

                {% elif step1 %}
                    <p>Please enter your email address to receive the registration mail :</p>
                    {{input_email}}
                    {{input_submit}}
                {% endif %}
            {{form_end}}
        </div>
    </div>
 </body>
</html>"""
            template.email_register_from = "no-reply@vulture"
            template.email_register_subject = "Registration request for {{ app.name }}"
            template.email_register_body = """<html>
    <head>
        <title>Vulture registration</title>
    </head>
    <body>
        <p>Dear Sir or Madam, <br><br>

        We got a request to register your account on {{ app.url }}.<br><br>

        Click here to validate the registration : <a href="{{registerLink}}">Register account</a><br><br>

        If you ignore this message, your account won't be confirmed.<br>
        If you didn't request a registration, <a href='mailto:abuse@vulture'>let us know</a><br>
    </body>
</html>"""
            template.html_error_403 = "403 Forbidden"
            template.html_error_404 = "404 Not found"
            template.html_error_500 = "500 Internal Server Error"
            template.html_error = """<!DOCTYPE html>
<html>
 <head>
    <meta charset="utf-8" />
    <title>Vulture Error</title>
    <link rel="stylesheet" href="templates/static/html/bootstrap.min.css" integrity="sha384-1q8mTJOASx8j1Au+a5WDVnPi2lkFfwwEAa8hDDdjZlpLegxhjVME1fgjWPGmkzs7" crossorigin="anonymous">
    <style>
        {{style}}
    </style>
 </head>
 <body>
    <div class="container">
        <div class="card card-container">
            <img id="vulture_img" src="https://www.vultureproject.org/assets/images/logo_mini.png"/>
            <p>{{message}}</p>
        </div>
    </div>
 </body>
</html>"""

            template.css = """
/*
 * Specific styles of signin component
 */
/*
 * General styles
 */
body, html {
    height: 100%;
    background: #FBFBF0 linear-gradient(135deg, #70848D, #21282E) repeat scroll 0% 0%;
}

.card-container.card {
    max-width: 350px;
    padding: 40px 40px;
}

#self_service {
    max-width: 450px;
    padding: 40px 40px;
}

.list-group-item {
    text-align: left;
}

.btn {
    font-weight: 700;
    height: 36px;
    -moz-user-select: none;
    -webkit-user-select: none;
    user-select: none;
    cursor: default;
}

/*
 * Card component
 */
.card {
    text-align:center;
    background-color: #F7F7F7;
    /* just in case there no content*/
    padding: 20px 25px 30px;
    margin: 0 auto 25px;
    margin-top: 50px;
    /* shadows and rounded borders */
    -moz-border-radius: 2px;
    -webkit-border-radius: 2px;
    border-radius: 2px;
    -moz-box-shadow: 0px 2px 2px rgba(0, 0, 0, 0.3);
    -webkit-box-shadow: 0px 2px 2px rgba(0, 0, 0, 0.3);
    box-shadow: 0px 2px 2px rgba(0, 0, 0, 0.3);
}

#vulture_img{
    width:150px;
}

.form-signin{
    text-align: center;
}

#captcha{
    border:1px solid #c5c5c5;
    margin-bottom: 10px;
}

.alert{
    margin-bottom: 0px;
    margin-top:15px;
}

.reauth-email {
    display: block;
    color: #404040;
    line-height: 2;
    margin-bottom: 10px;
    font-size: 14px;
    text-align: center;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    -moz-box-sizing: border-box;
    -webkit-box-sizing: border-box;
    box-sizing: border-box;
}

.form-signin #inputEmail,
.form-signin #inputPassword {
    direction: ltr;
    height: 44px;
    font-size: 16px;
}

input[type=email],
input[type=password],
input[type=text],
button {
    width: 100%;
    display: block;
    margin-bottom: 10px;
    z-index: 1;
    position: relative;
    -moz-box-sizing: border-box;
    -webkit-box-sizing: border-box;
    box-sizing: border-box;
}

.form-signin .form-control:focus {
    border-color: rgb(104, 145, 162);
    outline: 0;
    -webkit-box-shadow: inset 0 1px 1px rgba(0,0,0,.075),0 0 8px rgb(104, 145, 162);
    box-shadow: inset 0 1px 1px rgba(0,0,0,.075),0 0 8px rgb(104, 145, 162);
}

.btn.btn-signin {
    background-color: #F1A14C;
    padding: 0px;
    font-weight: 700;
    font-size: 14px;
    height: 36px;
    -moz-border-radius: 3px;
    -webkit-border-radius: 3px;
    border-radius: 3px;
    border: none;
    -o-transition: all 0.218s;
    -moz-transition: all 0.218s;
    -webkit-transition: all 0.218s;
    transition: all 0.218s;
}

.btn.btn-signin:hover{
    cursor: pointer;
}

.forgot-password {
    color: rgb(104, 145, 162);
}

.forgot-password:hover,
.forgot-password:active,
.forgot-password:focus{
    color: rgb(12, 97, 33);
}
"""

            template.email_from = "no-reply@vulture"
            template.email_subject = "Password reset request for {{ app.name }}"
            template.email_body = """<html>
<head>
</head>
<body>
<p>Dear Sir or Madam, <br><br>

We got a request to reset your account on {{ app.url }}.<br><br>

Click here to reset your password: <a href="{{resetLink}}">Reset password</a><br><br>

If you ignore this message, your password won't be changed.<br>
If you didn't request a password reset, <a href='mailto:abuse@vulture'>let us know</a><br>
</body>
</html>
"""

            template.save()
            for tpl in tpl_list:
                try:
                    f = open("/home/vlt-gui/vulture/portal/templates/portal_%s_%s.conf" % (str(template.id), tpl), 'w')
                    html = getattr(template, tpl)
                    if tpl not in ["email_subject", "email_body", "email_register_subject", "email_register_body"]:
                        html = html.replace("{{form_begin}}", "{{form_begin}}{% csrf_token %}")
                        html = "{% autoescape off %}\n" + html + "\n" + "{% endautoescape %}"
                    f.write(html.encode("UTF-8"))
                    f.close()
                except Exception as e:
                    pass


            try:
                with open("/home/vlt-gui/vulture/portal/templates/portal_%s.css" % (str(template.id)), 'w') as f:
                    f.write(template.css.encode("UTF-8"))
            except Exception as e:
                pass

            for message in ('html_error_403', 'html_error_404', 'html_error_500'):
                tpl = Template(template.html_error)
                tpl = tpl.render(Context({'message': getattr(template, message), 'style': template.css}))
                with open("/home/vlt-gui/vulture/portal/templates/portal_{}_{}.html".format(str(template.id), message), 'w') as f:
                    f.write(tpl)

            print("Default Template successfully imported")
