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
__doc__ = ''

from gui.models.repository_settings import MongoDBRepository


class Import(object):
    """ Class in charge to import Vulture default Repository, IE MongoDB repo

    """

    def process(self):
        # Checking if repository exist
        try:
            MongoDBRepository.objects.get(repo_name='Vulture Internal Database')
        except MongoDBRepository.DoesNotExist as e:

            """ If we are here, we are in the bootstraping of a Vulture Master node
                We don't want to call API at this time, so set bootstrap=True in save()
            """
            vlt_repo = MongoDBRepository()
            vlt_repo.is_internal = True
            vlt_repo.repo_name = 'Vulture Internal Database'
            # Fake values for host, port. Cuz fields are required but not used in internal repo
            vlt_repo.db_name = 'N/A'
            vlt_repo.db_host = 'N/A'
            vlt_repo.db_port = 9999
            vlt_repo.save(bootstrap=True)
            print("Vulture internal repository successfully imported")