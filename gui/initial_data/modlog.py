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
__doc__ = 'Initial data of Modlog model'

from gui.models.modlog_settings import ModLog
from gui.models.repository_settings import MongoDBRepository


class Import(object):

    def process(self):
        """ Function in charge to import Vulture Log Profiles into database

        :return:
        """
        try:
            ModLog.objects.get(name='Default Log Profile (File)')
        except ModLog.DoesNotExist as e:
            ModLog(name='Default Log Profile (File)').save(bootstrap=True)
            print("Default Log profile successfully imported")
        try:
            ModLog.objects.get(name='Default Log Profile (Repo)')
        except ModLog.DoesNotExist as e:

            """ If we are here, we are in the bootstraping of a Vulture Master node
                We don't want to call API at this time, so set bootstrap=True in save()
            """
            try:
                internal_repo = MongoDBRepository.objects.get(is_internal=True)
                modlog = ModLog(name='Default Log Profile (Repo)')
                modlog.repository_type = 'data'
                modlog.data_repository = internal_repo.id
                modlog.save(bootstrap=True)
                print("Internal MongoDB repository successfully imported")
            except MongoDBRepository.DoesNotExist as e:
                print(e)
                pass
            except Exception as e:
                print(e)
                pass