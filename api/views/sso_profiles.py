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
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_GET, require_POST

__author__ = "Kevin GUILLEMOT"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = 'Django views dedicated to manage SSO Profiles'


from django.http import JsonResponse
from django.views.generic import View
from bson import ObjectId
from bson.errors import InvalidId
from gui.decorators import api_json_request

from gui.models.application_settings import Application
from gui.models.repository_settings import SSOProfile
from mongoengine.django.auth         import MongoEngineBackend
from gui.models.user_document        import VultureUser as User

from json import loads as json_loads

import logging
logger = logging.getLogger('api')


class SSOProfilesAPI(View):

    def check_user_exists(self, app, login):
        """ Check if user exists in application repository """
        backend = app.getAuthBackend().get_backend()
        if isinstance(backend, MongoEngineBackend):
            try:
                user = User.objects.get(username=login)
            except:
                user = False
        else:
            user = backend.search_user(login)
        return user

    def get(self, request, app_id, login=""):
        try:
            app = Application.objects(id=ObjectId(app_id)).no_dereference().only('name', 'auth_backend', 'sso_profile').first()
            if not app:
                raise Application.DoesNotExist()
        except (Application.DoesNotExist, InvalidId) as e:
            logger.error("SSOProfiles::GET: Application with id '{}' not found".format(app_id))
            return JsonResponse({'status': False,
                                 'error': "Application with id '{}' not found.".format(app_id)})

        insecure = str(request.GET.get('insecure', False)).lower() == "true"

        try:
            if login:
                sso_profiles = app.get_sso_profiles(login, insecure=insecure)
            else:
                sso_profiles = app.get_all_sso_profiles(insecure=insecure)

            return JsonResponse({
                'status': True,
                'sso_profiles': sso_profiles
            })

        except Exception as e:
            logger.critical(e, exc_info=1)

            return JsonResponse({
                'status': False,
                'error': str(e)
            })

    @api_json_request
    def post(self, request, app_id, login=""):
        if not login:
            return JsonResponse({'status': False, 'error': "Login missing."})
        try:
            app = Application.objects(id=ObjectId(app_id)).no_dereference().only('name', 'auth_backend', 'sso_profile').first()
            if not app:
                raise Application.DoesNotExist()
            assert app.sso_profile, "No wizard SSO configured for the application '{}'".format(app.name)
        except (Application.DoesNotExist, InvalidId) as e:
            logger.error("SSOProfiles::GET: Application with id '{}' not found".format(app_id))
            return JsonResponse({'status': False,
                                 'error': "Application with id '{}' not found.".format(app_id)})
        except AssertionError as e:
            return JsonResponse({'status': False, 'error': str(e)})

        try:
            # First check if that user is in repository
            if not self.check_user_exists(app, login):
                return JsonResponse({'status': False, 'error': "User '{}' not found "
                                                               "in repository '{}'".format(login, app.getAuthBackend())})
            # Verify if a Profile already exists
            if SSOProfile.objects.filter(app_id=str(app.id), repo_id=str(app.getAuthBackend().id),
                                         login=login).count() != 0:
                return JsonResponse({'status': False, 'error': "SSOProfile already exists."})

            # Retrieve the list of application sso_profiles
            sso_profiles_app = json_loads(app.sso_profile)
            # And verify if all fields are provided
            request_data = request.POST or request.JSON
            new_sso_profiles = {}
            unknown_fields = request_data.keys()
            for sso_profile_app in sso_profiles_app:
                if sso_profile_app['type'] in ("learn", "learn_secret"):
                    field_name = sso_profile_app['name'].split(';vlt;')[0]
                    # First try to retrieve the friendly name.
                    if sso_profile_app.get('asked_name') and request_data.get(sso_profile_app.get('asked_name')):
                        field_value = request_data.get(sso_profile_app.get('asked_name'))
                        unknown_fields.remove(sso_profile_app.get('asked_name'))
                    else:
                        field_value = request_data.get(field_name)
                        if field_name in unknown_fields:
                            unknown_fields.remove(field_name)
                    assert field_value, "Field named '{}' {} missing.".format(field_name, "friendly name '{}'".format(sso_profile_app.get('asked_name')) if sso_profile_app.get('asked_name') else "")
                    new_sso_profiles[field_name] = field_value
            # Check if a field provided is not in application's sso_profiles
            if unknown_fields:
                # Correctly format fields for error
                if len(unknown_fields) == 1:
                    unknown_fields = unknown_fields.pop()
                else:
                    unknown_fields = ",".join(list(unknown_fields))
                raise Exception("Field(s) '{}' not found in Application learning fields.".format(unknown_fields))

            app.set_sso_profiles(login, new_sso_profiles)

            return JsonResponse({
                'status': True
            })

        except Exception as e:
            logger.critical(e, exc_info=1)

            return JsonResponse({
                'status': False,
                'error': str(e)
            })

    @api_json_request
    def put(self, request, app_id, login=""):
        if not login:
            return JsonResponse({'status': False, 'error': "Login missing."})
        try:
            app = Application.objects(id=ObjectId(app_id)).no_dereference().only('name', 'auth_backend', 'sso_profile').first()
            if not app:
                raise Application.DoesNotExist()
        except (Application.DoesNotExist, InvalidId) as e:
            logger.error("SSOProfiles::GET: Application with id '{}' not found".format(app_id))
            return JsonResponse({'status': False,
                                 'error': "Application with id '{}' not found.".format(app_id)})

        try:
            # First check if that user is in repository
            if not self.check_user_exists(app, login):
                return JsonResponse({'status': False, 'error': "User '{}' not found "
                                                               "in repository '{}'".format(login, app.getAuthBackend())})

            # Verify if a Profile already exists
            if SSOProfile.objects.filter(app_id=str(app.id), repo_id=str(app.getAuthBackend().id),
                                         login=login).count() == 0:
                return JsonResponse({'status': False,
                                     'error': "No SSOProfile found with application '{}', repository '{}' "
                                              "and login '{}'".format(app.name, app.getAuthBackend().repo_name, login)})

            request_data = request.POST or request.JSON
            # Retrieve the list of application sso_profiles
            sso_profiles_app = json_loads(app.sso_profile)
            # And verify if all fields are provided
            unknown_fields = request_data.keys()
            new_sso_profiles = {}
            for sso_profile_app in sso_profiles_app:
                if sso_profile_app['type'] in ("learn", "learn_secret"):
                    field_name = sso_profile_app['name'].split(';vlt;')[0]
                    # First try to retrieve the friendly name.
                    logger.info(field_name)
                    if sso_profile_app.get('asked_name') and request_data.get(sso_profile_app.get('asked_name')):
                        field_value = request_data.get(sso_profile_app.get('asked_name'))
                        unknown_fields.remove(sso_profile_app.get('asked_name'))
                    elif request_data.get(field_name):
                        field_value = request_data.get(field_name)
                        if field_name in unknown_fields:
                            unknown_fields.remove(field_name)
                    else:
                        continue
                    new_sso_profiles[field_name] = field_value
            # Check if a field provided is not in application's sso_profiles
            if unknown_fields:
                if len(unknown_fields) == 1:
                    unknown_fields = unknown_fields.pop()
                else:
                    unknown_fields = ",".join(list(unknown_fields))
                raise Exception("Field(s) '{}' not found in Application '{}' learning fields.".format(unknown_fields.encode('utf8'),
                                                                                                      app.name))

            app.set_sso_profiles(login, new_sso_profiles)

            return JsonResponse({
                'status': True
            })

        except Exception as e:
            logger.critical(e, exc_info=1)

            return JsonResponse({
                'status': False,
                'error': str(e)
            })

    @api_json_request
    def delete(self, request, app_id, login=""):
        if not login:
            return JsonResponse({'status': False, 'error': "Login missing."})
        try:
            app = Application.objects(id=ObjectId(app_id)).no_dereference().only('name', 'auth_backend', 'sso_profile').first()
            if not app:
                raise Application.DoesNotExist()
        except (Application.DoesNotExist, InvalidId) as e:
            logger.error("SSOProfiles::GET: Application with id '{}' not found".format(app_id))
            return JsonResponse({'status': False,
                                 'error': "Application with id '{}' not found.".format(app_id)})

        try:
            # Check is an sso_profile does exists
            if SSOProfile.objects.filter(app_id=str(app.id), repo_id=str(app.getAuthBackend().id),
                                         login=login).count() == 0:
                return JsonResponse({'status': False,
                                     'error': "No SSOProfile found with application '{}', repository '{}' "
                                              "and login '{}'".format(app.name, app.getAuthBackend().repo_name, login)})
            app.delete_sso_profile(login)

            return JsonResponse({'status': True})
        except Exception as e:
            logger.exception(e)

            return JsonResponse({
                'status': False,
                'error': str(e)
            }, status=500)
