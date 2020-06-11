#!/bin/sh
#
# This migration script update /home/vlt-sys/script/install_updates
#
#

script_filename="/home/vlt-sys/scripts/install_updates"

/bin/echo "#!/usr/bin/env /home/vlt-gui/env/bin/python2.7
# -*- coding: utf-8 -*-
from __future__ import print_function
\"\"\"This file is part of Vulture 3.

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
\"\"\"
__author__ = \"Florian Hagniel\"
__credits__ = []
__license__ = \"GPLv3\"
__version__ = \"3.0.0\"
__maintainer__ = \"Vulture Project\"
__email__ = \"contact@vultureproject.org\"
__doc__ = ''
import sys
import os


nb_args = len(sys.argv)
if nb_args == 2:
    update_type = sys.argv[1]
    allowed_updates = (
        'gui',
        'engine'
    )
    if update_type in allowed_updates:
        import logging
        logger = logging.getLogger('cluster')
        # Django setup part
        sys.path.append(\"/home/vlt-gui/vulture/\")
        os.environ.setdefault(\"DJANGO_SETTINGS_MODULE\", 'vulture.settings')
        import django
        django.setup()

        from vulture_toolkit.update_api.update_utils import UpdateUtils
        from gui.models.system_settings import Cluster

        node = Cluster.objects.get().get_current_node()
        version = getattr(node.version, \"{}_last_version\".format(update_type))
        updater = UpdateUtils.get_updater(update_type)
        try:
            status = updater.install(version)
        except Exception as e:
            logger.error(\"An error as occurred during installation of {}\".format(version))
            logger.exception(e)
            status = False
        if status:
            # Re-retrieve node, to prevent error if new attributes has been added during maj
            node = Cluster.objects.get().get_current_node()
            setattr(node.version, '{}_version'.format(update_type), updater.current_version)
            node.save()
            print(\"Successfull Vulture upgrade\", file=sys.stdout)
            sys.exit(0)
    else:
        print(\"This kind of update is not allowed, {}\".format(update_type), file=sys.stderr)
print(\"An error has occurred during upgrade process\", file=sys.stderr)
sys.exit(2)" > "$script_filename"

echo "[+] $script_filename successfully updated"
