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
__author__ = "Florian Hagniel"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = 'Vulture decorators'

from django.contrib.auth.decorators import user_passes_test
from mongoengine.django.auth import Group
from functools import wraps
from django.http import HttpRequest, HttpResponseForbidden, HttpResponseBadRequest
from json import loads as json_loads
import logging
logger = logging.getLogger('debug')


def group_required(*group_names):
    """ Decorator used to check user membership in at least on of the groups
    passed in

    :param group_names: List of groups
    :return:
    """
    def in_groups(u):
        if u.is_authenticated():
            groups = Group.objects(name__in=group_names)
            if bool(u.is_member_of(groups)) | u.is_superuser:
                return True
        return False
    return user_passes_test(in_groups, login_url='/unauthorized/')


def api_json_request(func):
    """ Decorator used to fill-in JSON attribute of request
          if content-type=application/json
    """
    def decorator(*args, **kwargs):
        request = args[1]
        if request.method in ("PATCH", "PUT", "POST", "DELETE") and request.META.get("CONTENT_TYPE") == "application/json":
            try:
                request.JSON = json_loads(request.body)
            except ValueError as error:
                logger.error("Bad POST data format : No valid json.")
                return HttpResponseBadRequest(
                    "Unable to parse JSON data: {error}".format(error=error)
                )
        return func(*args, **kwargs)
    return decorator

