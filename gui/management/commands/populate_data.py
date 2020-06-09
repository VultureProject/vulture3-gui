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
__doc__ = 'Django Management command used to populate Vulture Database'

import importlib
import os
import re

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Populate initial data into Vulture Database'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        def process(filename):
            filename = filename.split('.py')[0]
            module = importlib.import_module('gui.initial_data.' + filename)
            import_class = getattr(module, 'Import')
            import_instance = import_class()
            import_instance.process()

        self.stdout.write('Data import in progress...')
        data_path = "{}/{}".format(settings.BASE_DIR, '/gui/initial_data/')
        """ For each file in initial_data directory """
        for filename in os.listdir(data_path):
            """ If it is a python file """
            if re.match('^[a-z_]+.py$', filename) \
                    and not filename.startswith('__init__.py') \
                    and not filename.startswith('modlog.py'):
                process(filename)

        """ Process modlog  """
        process("modlog.py")
