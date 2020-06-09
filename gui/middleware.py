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
__doc__ = 'Vulture middleware'

from django.http import HttpResponse
from pymongo.errors import AutoReconnect


class MongoReconnect(object):
    def process_exception(self, request, exception):
        """ Catch AutoReconnect exception, this exception is raised when
        mongodb switch his primary node after a failover

        """
        if not isinstance(exception, AutoReconnect):
            return None
        #TODO Fix it : Used to replay POST request 
        #return HttpResponse('<script>location.reload(true);</script>')
        return HttpResponse('MongoDB Issues')