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
__doc__ = 'Django views dedicated to manage Users for portal authentication'


from django.http import JsonResponse
from django.views.generic import View
from gui.decorators import api_json_request

from gui.models.repository_settings import BaseAbstractRepository, LDAPRepository
from mongoengine.django.auth         import MongoEngineBackend
from gui.models.user_document        import VultureUser as User
from pymongo.cursor import Cursor

import logging
logger = logging.getLogger('api')


class RepositoriesAPI(View):

    def check_user_exists(self, backend, login):
        """ Check if user exists in authentication repository """
        if isinstance(backend, MongoEngineBackend):
            try:
                user = User.objects.get(username=login)
            except:
                user = False
        else:
            user = backend.search_user(login)
            if user is None or (isinstance(user, Cursor) and user.count() == 0):
                return False
        return user

    def get(self, request, repo_id, login=""):
        """ Retrieve authentication repository with its id, and return informations from asked user """
        try:
            assert login, "Login missing."
            repo = BaseAbstractRepository.search_repository(repo_id)
            assert repo, "Authentication repository not found with id '{}'".format(repo_id)
            assert repo.repo_type == "auth", "Repository with id '{}' type is not authentication".format(repo_id)
        except AssertionError as e:
            logger.error("RepositoriesAPI::GET: {}".format(e))
            return JsonResponse({'status': False,
                                 'error': str(e)})
        try:
            user_infos = repo.get_backend().get_user_infos(login)

            return JsonResponse({
                'status': True,
                'user_infos': user_infos
            })

        except NotImplementedError:
            return JsonResponse({'status': False,
                                 'error': "Get user informations on this type of repository is not supported yet."})

        except Exception as e:
            logger.critical(e, exc_info=1)

            return JsonResponse({
                'status': False,
                'error': str(e)
            })

    @api_json_request
    def post(self, request, repo_id, login=""):
        try:
            assert login, "Login missing."
            repo = BaseAbstractRepository.search_repository(repo_id)
            assert repo, "Authentication repository not found with id '{}'".format(repo_id)
            assert repo.repo_type == "auth", "Repository with id '{}' type is not authentication".format(repo_id)
            backend = repo.get_backend()
        except AssertionError as e:
            logger.error("RepositoriesAPI::POST: {}".format(e))
            return JsonResponse({'status': False,
                                 'error': str(e)})

        try:
            # First check if that user is in repository
            if self.check_user_exists(backend, login):
                return JsonResponse({'status': False, 'error': "User '{}' already exists in repository "
                                                               "'{}'".format(login, repo.repo_name)})

            # Check if fields are correctly filled-in
            request_data = request.POST or (request.JSON if hasattr(request, "JSON") else dict())

            password = request_data.get('password')
            if not password:
                return JsonResponse({'status': False, 'error': "Password missing in POST data."})

            login = login.encode("utf-8")
            password = password.encode("utf-8")
            email = request_data.get('email', "").encode('utf-8')
            phone = request_data.get('phone', "").encode('utf-8')

            kwargs = {}
            if isinstance(repo, LDAPRepository):
                group = request_data.get('group')
                update_group = request_data.get('update_group')
                if not group:
                    return JsonResponse({'status': False, 'error': "Group is missing for adding user into LDAP repository."})
                else:
                    group = group.encode('utf-8')
                kwargs['group'] = group
                kwargs['update_group'] = update_group

            backend.add_new_user(login, password, email, phone, **kwargs)

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
    def put(self, request, repo_id, login=""):
        try:
            assert login, "Login missing."
            repo = BaseAbstractRepository.search_repository(repo_id)
            assert repo, "Authentication repository not found with id '{}'".format(repo_id)
            assert repo.repo_type == "auth", "Repository with id '{}' type is not authentication".format(repo_id)
            backend = repo.get_backend()
        except AssertionError as e:
            logger.error("RepositoriesAPI::POST: {}".format(e))
            return JsonResponse({'status': False,
                                 'error': str(e)})

        try:
            # First check if that user is in repository
            if not self.check_user_exists(backend, login):
                return JsonResponse({'status': False, 'error': "User '{}' does not exists in repository "
                                                               "'{}'".format(login, repo.repo_name)})

            # Check if fields are correctly filled-in
            request_data = request.POST or request.JSON

            login = login.encode("utf-8")
            email = request_data.get('email')
            phone = request_data.get('phone')
            password = request_data.get('password')
            if not email and not phone and not password:
                return JsonResponse({'status': False, 'error': "Password, Email and Phone missing in POST data. "
                                                               "Nothing to do."})
            if email:
                email = email.encode('utf-8')
            if phone:
                phone = phone.encode('utf-8')
            if email or phone:
                backend.update_user(login, email=email, phone=phone)

            if password:
                password = password.encode('utf-8')
                backend.change_password(login, "", password)

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
    def delete(self, request, repo_id, login=""):
        try:
            assert login, "Login missing."
            repo = BaseAbstractRepository.search_repository(repo_id)
            assert repo, "Authentication repository not found with id '{}'".format(repo_id)
            assert repo.repo_type == "auth", "Repository with id '{}' type is not authentication".format(repo_id)
            backend = repo.get_backend()
        except AssertionError as e:
            logger.error("RepositoriesAPI::POST: {}".format(e))
            return JsonResponse({'status': False,
                                 'error': str(e)})

        try:
            # First check if that user is in repository
            if not self.check_user_exists(backend, login):
                return JsonResponse({'status': False, 'error': "User '{}' does not exists in repository "
                                                               "'{}'".format(login, repo.repo_name)})
            request_data = request.POST or request.JSON
            if not request_data.get('confirm'):
                return JsonResponse({'status': False, 'error': "Please send confirm=true to delete "
                                                               "user {}.".format(login)})

            backend.delete_user(login)

            return JsonResponse({
                'status': True
            })

        except Exception as e:
            logger.critical(e, exc_info=1)

            return JsonResponse({
                'status': False,
                'error': str(e)
            })
