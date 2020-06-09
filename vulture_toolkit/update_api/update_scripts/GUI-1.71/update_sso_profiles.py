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
__author__ = "Kevin Guillemot"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = """This migration script reload Rsyslog and Logrotate configurations, and restart services if needed """

import os
import sys

sys.path.append('/home/vlt-gui/vulture')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", 'vulture.settings')

import django
django.setup()

from gui.models.application_settings import Application
from gui.models.repository_settings import BaseAbstractRepository, SSOProfile

if __name__ == '__main__':

    for sso_profile in SSOProfile.objects.all():
        try:
            app = Application.objects.get(name=sso_profile.app_name)
        except:
            print("Error updating SSOProfile '<SSOProfile(app={},repo={},login={}' : Application named '{}' not found."
                  .format(sso_profile.app_name, sso_profile.repo_name, sso_profile.login, sso_profile.app_name))
        else:
            sso_profile.app_id = app.id
            # Search for repository
            for repo in BaseAbstractRepository.get_auth_repositories():
                if repo.repo_name == sso_profile.repo_name:
                    sso_profile.repo_id = repo.id
            sso_profile.store()

    print("SSO learning profiles updated.")
