#!/home/vlt-gui/env/bin/python2.7
# coding:utf-8

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
__author__     = "Kevin Guillemot"
__credits__    = []
__license__    = "GPLv3"
__version__    = "3.0.0"
__maintainer__ = "Vulture Project"
__email__      = "contact@vultureproject.org"
__doc__        = """Migration script to add the new templates : users registration"""

import os
import sys

sys.path.append('/home/vlt-gui/vulture')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", 'vulture.settings')

import django

django.setup()

from gui.models.template_settings import portalTemplate



if __name__ == '__main__':
    for template in portalTemplate.objects.all():
        if not hasattr(template, "html_registration") or not template.html_registration:
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

        if not hasattr(template, "email_register_subject") or not template.email_register_subject:
            template.email_register_subject = "Registration request for {{ app.name }}"

        if not hasattr(template, "email_register_from") or not template.email_register_from:
            template.email_register_from = "no-reply@vulture"

        if not hasattr(template, "email_register_body") or not template.email_register_body:
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

        template.save()

    for tpl in ('html_registration',
                'email_register_subject',
                'email_register_body'):
        try:
            f = open("/home/vlt-gui/vulture/portal/templates/portal_%s_%s.conf" % (str(template.id), tpl), 'w')
            html = getattr(template, tpl)
            if tpl not in ["email_register_subject","email_register_body"]:
                html = html.replace ("{{form_begin}}","{{form_begin}}{% csrf_token %}")
                html = "{% autoescape off %}\n" + html + "\n" + "{% endautoescape %}"
            f.write(html.encode("UTF-8"))
            f.close()
        except Exception as e:
            pass

    print "Templates successfully updated"

