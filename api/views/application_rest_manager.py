#!/usr/bin/python
# coding: utf-8

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

__author__ = "Olivier de Régis"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = 'Django views dedicated to Vulture Cluster API'

from django.views.decorators.csrf import csrf_exempt
from gui.models.application_settings import Application
from django.http import JsonResponse
import json
import logging.config

logger = logging.getLogger('cluster')


def stats(request):
    """ displays various stats about the apps """
    try:
        total = Application.objects.count()
        models = Application.objects.filter(is_model=True).count()
        total_app = total - models
        enabled_app = Application.objects.filter(enabled=True).count()
        not_enabled_app = total_app - enabled_app

        to_return = {
            "models": models,
            "applications": {
                "enabled": enabled_app,
                "not_enabled": not_enabled_app,
                "total": total_app
            },
            "total": total
        }

        return JsonResponse(to_return,
                            content_type='application/json')

    except Exception as error:
        logger.exception(error)

        return JsonResponse({
            'status': False,
            'error': str(error)
        }, content_type='application/json')


def get_all(request, fields=None):
    """ return a list of dumps of all applications.
    Fields can be given to filter out the result """
    try:
        fields = fields.split("|")
    except Exception:
        pass

    try:
        to_return = []

        for app in Application.objects():
            to_return.append(app.dump(fields))

        return JsonResponse(
            to_return, content_type='application/json', safe=False
        )

    except Exception as error:
        logger.exception(error)

        return JsonResponse({
            'status': False,
            'error': str(error)
        }, content_type='application/json')


def get_all_apps(request, fields=None):
    """ return a list of dumps of all applications.
    Fields can be given to filter out the result """
    try:
        fields = fields.split("|")
    except Exception:
        pass

    try:
        to_return = [app.dump(fields)
                     for app in Application.objects.filter(is_model=False)]

        return JsonResponse(
            to_return, content_type='application/json', safe=False
        )

    except Exception as error:
        logger.exception(error)

        return JsonResponse({
            'status': False,
            'error': str(error)
        }, content_type='application/json')


def get_all_models(request, fields=None):
    """ return a list of dumps of all applications.
    Fields can be given to filter out the result """
    try:
        fields = fields.split("|")
    except Exception:
        pass

    try:
        to_return = [app.dump(fields)
                     for app in Application.objects.filter(is_model=True)]

        return JsonResponse(
            to_return, content_type='application/json', safe=False
        )

    except Exception as error:
        logger.exception(error)

        return JsonResponse({
            'status': False,
            'error': str(error)
        }, content_type='application/json')


@csrf_exempt
def generate(request, is_reload=False):
    """ generate a new application with a given description """
    try:
        is_reload = (is_reload == "reload")
    except Exception:
        pass

    try:
        Application.generate(json.loads(request.body), is_reload)

        return JsonResponse({
            'status': True
        }, content_type='application/json')

    except Exception as error:
        logger.exception(error)

        return JsonResponse({
            'status': False,
            'error': str(error)
        }, content_type='application/json')


@csrf_exempt
def update(request, app_name):
    """ update an application with a given description """
    try:
        app = Application.objects.get(name=app_name)
        app.update(json.loads(request.body))

        return JsonResponse({
            'status': True
        }, content_type='application/json')

    except Exception as error:
        logger.exception(error)

        return JsonResponse({
            'status': False,
            'error': str(error)
        }, content_type='application/json')


def get_by_name(request, app_name, fields=None):
    """ return a dump of an application according to the name given.
    Fields can be given to filter out the result """
    try:
        fields = fields.split("|")
    except Exception:
        pass

    try:
        app = Application.get_app_by_name(app_name)

        return JsonResponse(app.dump(fields),
                            content_type='application/json')

    except Exception as error:
        logger.exception(error)

        return JsonResponse({
            'status': False,
            'error': str(error)
        }, content_type='application/json')


def get_by_regex(request, regex, fields=None):
    """ return one or several dump(s) according to the regex given.
    Fields can be given to filter out the result """
    try:
        fields = fields.split("|")
    except Exception:
        pass

    try:
        app_list = Application.get_apps_by_regex(regex)

        to_return = []

        for app in app_list:
            to_return.append(app.dump(fields))

        return JsonResponse(
            to_return, content_type='application/json', safe=False
        )

    except Exception as error:
        logger.exception(error)

        return JsonResponse({
            'status': False,
            'error': str(error)
        }, content_type='application/json')


def delete(request, app_name):
    """ delete an application according to the name given """
    try:
        app = Application.objects.get(name=app_name)
        app.destroy()

        return JsonResponse({
            'status': True
        }, content_type='application/json')

    except Exception as error:
        logger.exception(error)

        return JsonResponse({
            'status': False,
            'error': str(error)
        }, content_type='application/json')
