#!/usr/bin/python
# -*- coding: utf-8 -*-
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
__doc__ = 'Django views dedicated to application configuration'

import logging
import logging.config

from django.conf import settings
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseForbidden, HttpResponseRedirect

from gui.decorators import group_required
from gui.models.repository_settings import SSOProfile, BaseAbstractRepository
from gui.models.application_settings import Application
from bson import ObjectId
from bson.errors import InvalidId

from json import loads as json_loads

logging.config.dictConfig(settings.LOG_SETTINGS)
logger = logging.getLogger('debug')


@group_required('administrator', 'application_manager', 'security_manager')
def profile_list(request):
    """ Page dedicated to show application list
    """
    # Retrieve unicity of (app_id, repo_id, login)
    profile_list = list(SSOProfile.objects.aggregate({"$group": {"_id": {"login": "$login",
                                                                    "app_id": "$app_id",
                                                                    "repo_id": "$repo_id"}}},
                                                {"$project": {"_id":0, "login": "$_id.login",
                                                              "app_id": "$_id.app_id",
                                                              "login": "$_id.login",
                                                              "repo_id": "$_id.repo_id"}}))
    for profile in profile_list:
        profile['app_name']  = Application.objects.get(id=ObjectId(profile['app_id'])).name
        profile['repo_name'] = BaseAbstractRepository.search_repository(profile['repo_id']).repo_name

    return render_to_response('sso_profiles.html', {'profiles': profile_list}, context_instance=RequestContext(request))


@group_required('administrator')
def profile_edit(request, app_id, login):
    try:
        app = Application.objects(id=ObjectId(app_id)).no_dereference().only('name', 'auth_backend',
                                                                             'sso_profile', 'sso_forward').first()
    except (Application.DoesNotExist, InvalidId) as e:
        logger.error("SSOProfiles::GET: Application with id '{}' not found".format(app_id))
        return HttpResponseForbidden("Application with id '{}' not found.".format(app_id))

    # Check if user exists ?
    if app.sso_forward == "basic":
        sso_profiles_app = [{'type': "learn", 'name': "basic_username;vlt;", 'asked_name': "username"},
                            {'type': "learn_secret", 'name': "basic_password;vlt;", 'asked_name': "password"}]
    elif app.sso_forward == "kerberos":
        sso_profiles_app = [{'type': "learn", 'name': "kerberos_username;vlt;", 'asked_name': "username"},
                            {'type': "learn_secret", 'name': "kerberos_password;vlt;", 'asked_name': "password"}]
    else:
        # Retrieve the list of application sso_profiles
        try:
            sso_profiles_app = json_loads(app.sso_profile)
        except:
            raise Exception("No SSO wizard configured for this application. Cannot retrieve user profiles.")

    errors = []
    profiles = []
    try:
        if request.method == "POST":
            # And verify if all fields are provided
            request_data = request.POST
            user_profiles = {}
            for sso_profile_app in sso_profiles_app:
                if sso_profile_app['type'] in ("learn", "learn_secret"):
                    field_name, field_id = sso_profile_app['name'].split(';vlt;')
                    field_value = request_data.get(field_name)
                    # If a learning_secret field has not been modified, no need to update it
                    if field_value == "*"*len(field_value):
                        continue
                    elif field_value is None:
                        errors.append("Field named '{}' missing.".format(field_name))
                    else:
                        user_profiles[field_name] = field_value

            # Check if a field provided is not in application's sso_profiles
            unknown_fields = list(set(request_data.keys()).difference(set(user_profiles.keys())))
            if not unknown_fields:
                errors.append("Field(s) {} not found in Application learning fields".format(",".join(unknown_fields)))

            if not errors:
                app.set_sso_profiles(login, user_profiles)
                return HttpResponseRedirect("/repository/sso_profiles")

        else:
            user_profiles = app.get_sso_profiles(login)

        # Get application sso wizard, in case some field(s) has been added
        for profile in sso_profiles_app:
            if profile['type'] in ("learn", "learn_secret"):
                profile_name = profile['name'].split(";vlt;")[0]
                if profile.get('asked_name'):
                    profile_value = user_profiles.get(profile.get('asked_name'))
                if not profile_value:
                    profile_value = user_profiles.get(profile_name, "")
                profiles.append((profile_name,
                                 profile.get("asked_name", "Not field"),
                                 profile_value,
                                 profile['type']))

    except Exception as e:
        logger.critical(e, exc_info=1)
        errors = [str(e)]

    return render_to_response("sso_profiles_edit.html", {'profiles': profiles,
                                                         'app_name': app.name,
                                                         'repository': app.getAuthBackend().repo_name,
                                                         'login': login,
                                                         'error': errors},
                              context_instance=RequestContext(request))
