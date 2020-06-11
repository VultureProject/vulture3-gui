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
__author__ = "Florian Hagniel"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = 'Django views used to handle authentication events'

import logging
import logging.config

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

logger = logging.getLogger('gui_authentication')


def log_in(request):
    """ Handle authentication in Vulture GUI

    :param request: Django request object
    :returns: Home page if user auth succeed. Logon page if auth failed
    """
    if request.POST:
        username = request.POST.get('username')
        password = request.POST.get('password')
        #FIXME SECURITY CLEAN
        user = authenticate(username=username, password=password)
        # User is authenticate, log this event and redirect to home page or last page
        if user is not None:
            login(request, user)
            logger.info(username + " successfully connected")
            return HttpResponseRedirect(request.POST.get('next'))
        # Auth failed => log event and redirect to logon page
        else:
            logger.warn(username + " failed to authenticate")
            return HttpResponseRedirect("/")
    else:
        try:
            next_url = request.GET['next'].split('=')[1]
        except:
            next_url = "/"

        return render_to_response('logon.html', {'next': next_url},
                                  context_instance=RequestContext(request))


def log_out(request):
    """ Handle logout event in Vulture GUI
    
    :param request: Django request object
    :returns: Logon page
    """
    username = request.user.username
    logout(request)
    logger.info(username + " successfully disconnected")
    return render_to_response('logon.html', {'next': '/'},
                              context_instance=RequestContext(request))


@login_required()
def unauthorized(request):
    return render_to_response('unauthorized.html',
                              context_instance=RequestContext(request))

@login_required()
def handler403(request):
    response = render_to_response('403.html', {},
                                  context_instance=RequestContext(request))
    response.status_code = 403
    return response

@login_required()
def handler404(request):
    response = render_to_response('404.html', {},
                                  context_instance=RequestContext(request))
    response.status_code = 404
    return response

@login_required()
def handler500(request):
    response = render_to_response('500.html', {},
                                  context_instance=RequestContext(request))
    response.status_code = 500
    return response