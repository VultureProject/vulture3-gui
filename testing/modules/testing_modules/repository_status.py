import os
import sys

import django

from testing.core.testing_module import TestingModule
sys.path.append('/home/vlt-gui/vulture')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", 'vulture.settings')
django.setup()

from vulture_toolkit.auth.sql_client import SQLClient
from vulture_toolkit.auth.mongodb_client import MongoDBClient
from vulture_toolkit.auth.ldap_client import LDAPClient
from gui.models.repository_settings import (BaseAbstractRepository, LDAPRepository, 
    SQLRepository, MongoDBRepository,
    ElasticSearchRepository)


class Module(TestingModule):
    def __init__(self):
        super(Module, self).__init__()
        self.log_level = 'debug'
        self.repositories = BaseAbstractRepository.get_repositories()

    def __str__(self):
        return "Repository status"

    def status_elasticsearch(self):
        """
        Check ElasticSearch repositories connection
        """
        dead_repositories = []
        for els in ElasticSearchRepository.objects():
            try:
                data = els.test_connection()
            except:
                dead_repositories.append(els)

        assert (not dead_repositories), 'Unable to contact ElasticSearch repositories {}'.format([els.repo_name for els in dead_repositories])

    def status_mongodb(self):
        """
        Check MongoDB repositories connection
        """
        dead_repositories = []
        for mongo in MongoDBRepository.objects.filter(is_internal=False):
            mongodb_client = MongoDBClient(mongo)
            status = mongodb_client.test_mongodb_connection()

            if not status['status']:
                dead_repositories.append(mongo)

        assert (not dead_repositories), 'Unable to contact MongoDB repositories {}'.format([m.repo_name for m in dead_repositories])

    def status_sql(self):
        """
        Check SQL repositories connection
        """
        dead_repositories = []
        for sql in SQLRepository.objects():
            sql_client = SQLClient(sql)
            status = sql_client.test_sql_connection()

            if not status['status']:
                dead_repositories.append(sql)

        assert (not dead_repositories), 'Unable to contact SQL repositories {}'.format([sql.repo_name for sql in dead_repositories])

    def status_ldap(self):
        """
        Check LDAP repositories connection
        """
        dead_repositories = []
        for ldap in LDAPRepository.objects():
            ldap_client = LDAPClient(ldap)
            status = ldap_client.test_ldap_connection()

            if not status['status']:
                dead_repositories.append(ldap)

        assert (not dead_repositories), 'Unable to contact LDAP repositories {}'.format([ldap.repo_name for ldap in dead_repositories])



