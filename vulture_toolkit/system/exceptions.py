#!/usr/bin/python
# --*-- coding: utf-8 --*--
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
__maintainer__ =\
    "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = 'System toolkit utils exceptions'


class ServiceError(Exception):
    """ """
    def __init__(self, message, trying_to):
        super(ServiceError, self).__init__(message)
        self.trying_to = trying_to


class ServiceConfigError(ServiceError):
    """ """
    def __init__(self, message):
        super(ServiceConfigError, self).__init__(message, "Write conf")


class ServiceNoConfigError(ServiceError):
    """ """
    def __init__(self, message):
        super(ServiceNoConfigError, self).__init__(message, "Get conf")


class ServiceStartError(ServiceError):
    """ """
    def __init__(self, message):
        super(ServiceStartError, self).__init__(message, "Start")


class ServiceStopError(ServiceError):
    """ """
    def __init__(self, message):
        super(ServiceStopError, self).__init__(message, "Stop")



