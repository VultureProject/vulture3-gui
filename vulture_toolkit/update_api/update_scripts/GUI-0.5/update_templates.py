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
__author__     = "Jeremie Jourdin"
__credits__    = []
__license__    = "GPLv3"
__version__    = "3.0.0"
__maintainer__ = "Vulture Project"
__email__      = "contact@vultureproject.org"
__doc__        = """This migration script update Templates to add new fields"""

import os
import sys

sys.path.append('/home/vlt-gui/vulture')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", 'vulture.settings')

import django
django.setup()

from gui.models.template_settings import portalTemplate

def update():
    tpl_list=('html_login', 'html_logout', 'html_learning', 'html_self', 'html_password', 'email_subject', 'email_body')
    for template in portalTemplate.objects.filter():
        template.save()

        for tpl in tpl_list:
            try:
                f = open("/home/vlt-gui/vulture/portal/templates/portal_%s_%s.conf" % (str(template.id),tpl), 'w')
                html = getattr(template, tpl)
                if tpl not in ["email_subject","email_body"]:
                    html = html.replace ("{{form_begin}}","{{form_begin}}{% csrf_token %}")
                    html = "{% autoescape off %}\n" + html + "\n" + "{% endautoescape %}"
                f.write(html.encode("UTF-8"))
                f.close()
            except Exception as e:
                pass


        try:
            f = open("/home/vlt-gui/vulture/portal/templates/portal_%s.css" % (str(template.id)), 'w')
            f.write(template.css.encode("UTF-8"))
            f.close()
        except Exception as e:
            pass



if __name__ == "__main__":
    update()