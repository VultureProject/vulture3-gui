#!/home/vlt-gui/env/bin/python
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
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = """This migration script create indexes in Mongo database to prevent COLLSCAN searches """

import os
import sys

sys.path.append('/home/vlt-gui/vulture')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", 'vulture.settings')

import django
django.setup()

from gui.models.monitor_settings import Monitor
from gui.models.repository_settings import MongoDBRepository
from vulture_toolkit.log.mongodb_client import MongoDBClient


if __name__ == '__main__':

    try:
        repo = MongoDBRepository.objects.get(repo_name='Vulture Internal Database')
        client = MongoDBClient(repo)
        con = client._get_connection()
        if not con.is_primary:
            print("Current node is not master mongo, quitting.")
            sys.exit(0)

        # Ensure index exists on Monitor collection (vulture database)
        Monitor.ensure_indexes()
        # And create index on access collection (logs database)
        db_logs = con.logs
        db_logs['access'].create_index([("app_name", 1),("time", 1)])

        print("Indexes creation done.")
    except Exception as e:
        print("Failed to connect to MongoDB on node {}. Aborting index creation.")
