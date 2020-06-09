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
__author__ = "Kevin Guillemot, Florian Hagniel"
__credits__ = ['Edouard Berton']
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = 'Django models dedicated to repository settings'


# Django system imports
from django.utils.translation import ugettext_lazy as _
from mongoengine import DynamicDocument, Q
from mongoengine.fields import BooleanField, IntField, ReferenceField, StringField

# Django project imports
from gui.signals.gui_signals import krb5_modified
from gui.signals.gui_signals import repo_modified
from vulture_toolkit.system.aes_utils import AESCipher
from vulture_toolkit.templates import tpl_utils
from vulture.secret_key import SECRET_KEY

# Extern modules imports
from base64 import b64encode
from requests import request, Request, Session

# Logger configuration imports
import logging
logger = logging.getLogger('debug')


PASSWORD_HASH_ALGO = (
    ('plain', 'plain (NEVER enable that on production)'),
    ('md5', 'md5 (Warning: insecure)'),
    ('sha1', 'sha1 (Warning: insecure)'),
    ('sha256', 'sha256'),
    ('sha384', 'sha384'),
    ('sha512', 'sha512'),
    ('make_password', 'django make_password'),
    ('pbkdf2-256-20000', 'pbkdf2-sha256 with 20,000 iterations (Salt is Random)'),
    ('pbkdf2-256-40000', 'pbkdf2-sha256 with 40,000 iterations (Salt is Random)'),
    ('pbkdf2-256-60000', 'pbkdf2-sha256 with 60,000 iterations (Salt is Random)'),
    ('pbkdf2-256-80000', 'pbkdf2-sha256 with 80,000 iterations (Salt is Random)'),
    ('pbkdf2-256-100000', 'pbkdf2-sha256 with 100,000 iterations (Salt is Random)'),
    ('pbkdf2-512-20000', 'pbkdf2-sha512 with 20,000 iterations (Salt is Random)'),
    ('pbkdf2-512-40000', 'pbkdf2-sha512 with 40,000 iterations (Salt is Random)'),
    ('pbkdf2-512-60000', 'pbkdf2-sha512 with 60,000 iterations (Salt is Random)'),
    ('pbkdf2-512-80000', 'pbkdf2-sha512 with 80,000 iterations (Salt is Random)'),
    ('pbkdf2-512-100000', 'pbkdf2-sha512 with 100,000 iterations (Salt is Random)'),

)

PASSWORD_SALT_POSITION = (
    ('', '---'),#FIXME
    ('begin', 'Begin'),
    ('end', 'End'),
)



class SSOProfile(DynamicDocument):
    """ Class for SSO Profile

    encrypted_name: The encrypted name of the stored value
    encrypted_value: The encrypted value

    Encryption Key is derived from the main user login, the application id, the backend_id  and the value name
        encryption_key=sha256('app_id' + 'backend_id' + 'login' + 'name')
        Encryption is done via AES256
    """
    encrypted_name  = StringField(required=True)
    encrypted_value = StringField(required=True)
    app_name        = StringField(required=True)
    app_id        = StringField(required=True)
    repo_name       = StringField(required=True)
    repo_id       = StringField(required=True)
    login           = StringField(required=True)


    def get_data(self, to_decrypt, app_id, backend_id, login, name):
        """
        :return: Return the password in cleartext
        """
        self.encrypted_value = to_decrypt
        aes = AESCipher(str(SECRET_KEY)+str(app_id)+str(backend_id)+str(login)+str(name))
        self.encrypted_name = aes.key.hex()
        return aes.decrypt(self.encrypted_value)


    def set_data(self, app_id, app_name, backend_id, repo_name, login, name, value):
        """
        :return: Return the encrypted value
        """
        aes = AESCipher(str(SECRET_KEY)+str(app_id)+str(backend_id)+str(login)+str(name))
        self.app_name  = str(app_name)
        self.app_id  = str(app_id)
        self.repo_name = str(repo_name)
        self.repo_id = str(backend_id)
        self.login = str(login)
        self.encrypted_value = aes.encrypt(str(value)).decode('utf8')
        self.encrypted_name = aes.key.hex()
        return self.encrypted_value


    def store(self):
        self.save()



class BaseAbstractRepository(DynamicDocument):
    """ Base Abstract class of Repository Object

    repo_name: Friendly name of repository
    repo_type: Type of repo. 2 Types are availables, Authentication repository
        and data store repository
    """

    REPO_TYPE = (
        ('data', 'Data'),
        ('auth', 'Authentication'),
        ('otp', 'OTP Authentication'),
    )
    repo_name = StringField(verbose_name=_('Repository name'), required=True,
                            help_text=_('Friendly name of your repository'))
    repo_type = StringField(verbose_name=_('Repository type'), choices=REPO_TYPE,
                            help_text=_('Type of Repo'))

    @classmethod
    def get_repositories(cls):
        """ Return a list of Repository objects

        :return:
        """
        repo_lst = list()
        for obj in cls.__subclasses__():
            for ob in obj.objects.all():
                repo_lst.append(ob)
        return repo_lst

    @classmethod
    def get_data_repositories(cls):
        """ Return a list of Data Repository objects

        :return:
        """
        repo_lst = list()
        for obj in cls.__subclasses__():
            for ob in obj.objects.filter(Q(repo_type='data') | Q(is_internal=True)):

                """ We need to filter syslog repo because they are dealed as "File" repo """
                if isinstance(ob, SyslogRepository):
                    continue
                else:
                    repo_lst.append(ob)
        return repo_lst

    @classmethod
    def get_syslog_repositories(cls):
        """ Return a list of Syslog Data Repository objects

        :return:
        """
        repo_lst = list()
        for obj in cls.__subclasses__():
            for ob in obj.objects.filter(repo_type='data'):
                if isinstance(ob, SyslogRepository):
                    repo_lst.append(ob)
        return repo_lst


    @classmethod
    def search_repository(cls, object_id):
        """ Search a repository by object id

        :return:
        """
        for obj in cls.__subclasses__():
            repo = obj.objects.with_id(object_id)
            if repo:
                return repo
        return None

    @classmethod
    def get_auth_repositories(cls):
        """ Return a list of Authentication Repository objects

        :return:
        """
        repo_lst = list()
        for obj in cls.__subclasses__():
            for ob in obj.objects.filter(Q(repo_type='auth') | Q(is_internal=True)):
                repo_lst.append(ob)
        return repo_lst

    def __unicode__(self):
        return "{} ({})".format(self.repo_name, self.__class__.__name__)

    meta = {
        'abstract': True
    }

    def is_ssl(self):
        """ Return True if the repository use SSL """
        raise NotImplemented("Need to redifine this method")


    def type_uri(self):
        """Method called in some repository views. Returned value must match
        URI name of repository. See example below for more informations.
        ex for LDAP Repo:
        url: /repository/ldap/
        ==> We must return "ldap"

        :return: String with Repo URI
        """
        raise NotImplemented("type_uri is mandatory in order to make"
                             "repository views work")

    def get_backend(self):
        """ Return Backend object. This object is used by Django Auth
        mechanism

        :return:
        """
        raise NotImplemented("You have to redefine this method")

    def save(self, **kwargs):
        """ if bootstrap is set to True, then don't send the
            repo_modified signal. This is to avoid timeout
            at bootstrap time when trying to contact non-existing
            API (Vulture-GUI is not started yet at this time)
        """

        boot = kwargs.get('bootstrap') or False
        if self.repo_type == 'data' and boot is False:
            repo_modified.send(sender=self.__class__)

        super(BaseAbstractRepository, self).save(**kwargs)


class SQLRepository(BaseAbstractRepository):
    """ Class used to represent SQL repository object

    db_type: Technology type of SQL Database (ex: MySQL)
    db_host: IP Address used to contact Database
    db_port: Port used to contact database
    db_name: Database name
    db_user: Database connection username
    db_password: Database connection password
    db_table: Table name of user's table
    db_user_column: Column name of "username attribute"
    db_password_column: Column name of "password attribute"
    db_password_hash_algo: Hash algorithm of password
    db_password_salt: Salt used to protect passwords
    db_password_salt_position: Position of salt
    db_change_pass_column: Column name of "need change pass" attribute
    db_change_pass_value: Expected value in order to verify if password has expired
    db_locked_column: Column name of "account locked" attribute
    db_locked_column_value: Expected value in order to verify if account is locked
    db_user_phone_column: Column name of "user phone number attribute"
    db_user_email_column: Column name of "user email address attribute"
    """

    # DB types key, need to correspond to SQLAlchemy dialect
    # CF: http://docs.sqlalchemy.org/en/latest/core/engines.html
    DB_TYPE = (
        ('mysql', 'MySQL'),
        ('postgresql', 'PostGreSQL'),
        #('oracle', 'Oracle'),
        #('mssql', 'Microsoft SQL Server'),
    )
    OAUTH2_TYPE_CHOICES = (('dict','Dictionnary of keys and values'),('list','List of values'))
    OAUTH2_TOKEN_CHOICES = (('header','Header'),('json','JSON'),('both','Header and JSON'))

    # Connection settings attributes
    db_type = StringField(verbose_name=_('Database type'), choices=DB_TYPE,
                          help_text=_('Database technology type'))
    db_host = StringField(verbose_name=_('Database host'),
                          help_text=_('IP Address of your SQL Server'),
                          required=True)
    db_port = IntField(verbose_name=_('Database port'),
                       help_text=_('Listening port of your SQL Server'),
                       required=True)
    db_name = StringField(verbose_name=_('Database name'),
                          help_text=_('Name of your database'), required=True)
    db_user = StringField(verbose_name=_('Username'),
                          help_text=_('Username used for database connection'),
                          required=True)
    db_password = StringField(verbose_name=_('Password'),
                              help_text=_('Password used for database connection'))
    # User search related attributes
    db_table = StringField(verbose_name=_('User table name'),
                           help_text=_('Name of your users table'), required=True)
    db_user_column = StringField(verbose_name=_("Username column name"),
                                 help_text=_('Database user column name'))
    db_password_column = StringField(verbose_name=_("Username's password column name"),
                                     help_text=_('User password column name'),
                                     required=True)
    db_password_hash_algo = StringField(verbose_name=_('Password hash algorythm'),
                                        choices=PASSWORD_HASH_ALGO,
                                        help_text=_('Algorithm used to hash your password'),
                                        required=True)
    db_password_salt = StringField(verbose_name=_("Password salt"),
                                   help_text=_("Salt used to secure your password"))
    db_password_salt_position = StringField(choices=PASSWORD_SALT_POSITION,
                                            verbose_name=_("Password salt position"),
                                            help_text=_("Position of salt"),
                                            null=True)
    db_change_pass_column = StringField(verbose_name=_("Change pass column"),
                                        help_text=_("Column change pass"))
    db_change_pass_value = StringField(verbose_name=_("Change pass expected value"),
                                       help_text=_("If change pass column value "
                                                    "is egals to this value, "
                                                    "user have to change his password"))
    db_locked_column = StringField(verbose_name=_("Account locked column"),
                                        help_text=_("Column locked account"))
    db_locked_value = StringField(verbose_name=_("Account locked expected value"),
                                       help_text=_("If account locked column value "
                                                    "is egals to this value, "
                                                    "user cannot login"))
    db_user_phone_column = StringField(verbose_name=_("User mobile column name"),
                                       help_text=_("Name of your column with user's "
                                                   "phone number"))
    db_user_email_column = StringField(verbose_name=_("User email address column name"),
                                       help_text=_("Name of your column with user's "
                                                   "email address"))

    enable_oauth2 = BooleanField(default=False, help_text=_('Export oauth2 attributes'))
    oauth2_attributes = StringField(required=False, help_text=_('Oauth2 attribute(s)'))
    oauth2_type_return = StringField(choices=OAUTH2_TYPE_CHOICES, default='dict',required=True, help_text='Type of returned scope values')
    oauth2_token_return = StringField(choices=OAUTH2_TOKEN_CHOICES, default='header',required=True, help_text='Token response place (in header, or in response, or both)')
    oauth2_token_ttl = IntField(default=3600, required=True, help_text='Oauth2 token time to live (in seconds)')

    is_internal = BooleanField(default=False)

    @property
    def type_uri(self):
        return 'sql'

    def get_phone_column(self):
        return self.db_user_phone_column

    def get_backend(self):
        """ Return Backend object. This object is used by Django Auth
        mechanism

        :return: SQLBackend object
        """
        from gui.sql_backend import SQLBackend
        return SQLBackend(self)

    def save(self, **kwargs):
        self.repo_type = 'auth'
        return super(SQLRepository, self).save(**kwargs)


class MongoDBRepository(BaseAbstractRepository):

    OAUTH2_TYPE_CHOICES = (('dict','Dictionnary of keys and values'),('list','List of values'))
    OAUTH2_TOKEN_CHOICES = (('header','Header'),('json','JSON'),('both','Header and JSON'))

    db_host = StringField(verbose_name=_('Database host'),
                          help_text=_('IP/Hostname of your MongoDB Server'),
                          required=True)
    db_port = IntField(verbose_name=_('Database port'),
                       help_text=_('Listening port of your MongoDB Server'),
                       required=True)
    db_name = StringField(verbose_name=_('Database name'), required=True,
                          help_text=_('Name of your database'))

    db_client_cert = ReferenceField ('SSLCertificate', verbose_name=_('Client certificate'), required=False,
                        help_text=_('For SSL Connexion, please choose the certificate to use'))

    db_user = StringField(verbose_name=_('Username'),
                          help_text=_('Username used for database connection'))
    db_password = StringField(verbose_name=_('Password'),
                              help_text=_('Password used for database connection'))

    db_collection_name = StringField(verbose_name=_('User collection name'),
                                     help_text=_('Name of your users collection'))
    db_user_column = StringField(verbose_name=_('Username field name'),
                                 help_text=_('Database user field'))
    db_password_column = StringField(verbose_name=_("Username's password field name"),
                                     help_text=_('Database user field'))
    db_password_hash_algo = StringField(verbose_name=_('Password hash algorythm'),
                                        choices=PASSWORD_HASH_ALGO, default='plain',
                                        help_text=_('Algorithm used to hash your password'))
    db_password_salt = StringField(verbose_name=_("Password salt"),
                                   help_text=_("Salt used to secure your password"))
    db_password_salt_position = StringField(choices=PASSWORD_SALT_POSITION,
                                            verbose_name=_("Password salt position"),
                                            help_text=_("Position of salt"),
                                            null=True)
    db_change_pass_column = StringField(verbose_name=_("Change pass field"),
                                        help_text=_("Field change pass"))
    db_change_pass_value = StringField(verbose_name=_("Change pass expected value"),
                                        help_text=_("If change pass field value "
                                                    "is egals to this value, "
                                                    "user have to change his password"))
    db_user_phone_column = StringField(verbose_name=_("User mobile column name"),
                                 help_text=_("Name of your column with user's "
                                             "phone number"))

    db_user_email_column = StringField(verbose_name=_("User email address column name"),
                                 help_text=_("Name of your column with user's "
                                             "email address"))

    db_access_collection_name = StringField(verbose_name=_('Access collection name'),
                                     help_text=_('Name of collection where '
                                                 'vulture will store application '
                                                 ' access logs'))

    db_packetfilter_collection_name = StringField(verbose_name=_("Packet Filter collection name"),
                                    help_text=_("Name of collection where vulture will store Packet Filter logs"),
                                    default="vulture_pf")

    db_diagnostic_collection_name = StringField(verbose_name=_("Diagnostic collection name"),
                                    help_text=_("Name of collection where vulture will store diagnostic logs"),
                                    default="vulture_diagnostic")

    db_vulturelogs_collection_name = StringField(verbose_name=_("Vulture logs collection name"),
                                    help_text=_("Name of collection where vulture will store Vulture logs"),
                                    default="vulture_logs")

    enable_oauth2 = BooleanField(default=False, help_text=_('Export oauth2 attributes'))
    oauth2_attributes = StringField(required=False, help_text=_('Oauth2 attribute(s)'))
    oauth2_type_return = StringField(choices=OAUTH2_TYPE_CHOICES,default='dict', required=True, help_text='Type of returned scope values')
    oauth2_token_return = StringField(choices=OAUTH2_TOKEN_CHOICES, default='header',required=True, help_text='Token response place (in header, or in response, or both)')
    oauth2_token_ttl = IntField(default=3600, required=True, help_text='Oauth2 token time to live (in seconds)')

    is_internal = BooleanField(default=False)
    replicaset = StringField(required=False, help_text=_('ReplicaSet name'))

    @property
    def type_uri(self):
        return 'mongodb'

    @property
    def replica_list(self):
        """ If repository is internal, return list of replica member with coma
        a separator (ex: vulture-node1:9091, vulture-node2:9091)

        :return: String with list of replica set members
        """
        if self.is_internal:
            replica_lst = ''
            from vulture_toolkit.system.replica_set_client import ReplicaSetClient
            for replica in ReplicaSetClient().get_mongodb_hosts():
                replica_lst += "{}:{},".format(replica[0], replica[1])
            return replica_lst[:-1]
        else:
            raise NotImplementedError("This property is only available with "
                                      "internal MongoDB repository")

    def is_ssl(self):
        """ Return True if the repository use ssl
            False otherwise
        """
        if self.db_client_cert is None:
            return False
        return True

    def get_phone_column(self):
        return self.db_user_phone_column

    def get_backend(self):
        """ Return Backend object. This object is used by Django Auth
        mechanism

        :return: MongoEngineBackend object if we got internal MongoDB repository,
        MongoDBBackend object otherwise
        """
        if self.is_internal:
            from mongoengine.django.auth import MongoEngineBackend
            return MongoEngineBackend()
        else:
            from gui.mongodb_backend import MongoDBBackend
            return MongoDBBackend(self)


class ElasticSearchRepository(BaseAbstractRepository):
    es_host = StringField(verbose_name=_('Hosts list'), required=True,
                          help_text=_('http://IPv4:9200,http://[IPv6]:9200'))

    es_user = StringField(verbose_name=_('Username'),
                          help_text=_('Username used for elasticsearch connection'))
    es_password = StringField(verbose_name=_('Password'),
                              help_text=_('Password used for elasticsearch connection'))
    es_access_index_name = StringField(verbose_name=_('Index name (Access logs)'),
                                       required=True, help_text=_('Index name '
                                      'used by Vulture to store access logs'))
    es_access_type_name = StringField(verbose_name=_('Type name (Access logs)'),
                                      help_text=_('Name of your type where '
                                                  'Vulture will store access logs'))

    es_packetfilter_index_name = StringField(verbose_name=_("Packet Filter index name"),
                                    help_text=_("Name of collection where vulture will store Packet Filter logs"),
                                    default="vulture_pf")

    es_packetfilter_type_name = StringField(verbose_name=_("Type name (PacketFilter logs)"),
        required=True, help_text=_("Name of your type where Vulture will store PacketFilter logs"),
        default="vulture_pf")

    es_diagnostic_index_name = StringField(verbose_name=_("Diagnostic collection name"),
                                    help_text=_("Name of collection where vulture will store diagnostic logs"),
                                    default="vulture_diagnostic")

    es_diagnostic_type_name = StringField(verbose_name=_("Type name (Diagnostic logs)"),
        required=True, help_text=_("Name of your type where Vulture will store Diagnostic logs"),
        default="vulture_diagnostic")

    es_vulturelogs_index_name = StringField(verbose_name=_("Vulture logs collection name"),
                                    help_text=_("Name of collection where vulture will store Vulture logs"),
                                    default="vulture_logs")

    es_vulturelogs_type_name = StringField(verbose_name=_("Type name (Vulture logs)"),
        required=True, help_text=_("Name of your type where Vulture will store Vulture logs"),
        default="vulture_logs")


    es_dateformat = StringField(verbose_name=_('Date format'), required=True,
                                default="%Y-%m-%d", help_text=_('Date format used')) #TODO HELPTEXT

    is_internal = BooleanField(default=False)

    @property
    def type_uri(self):
        return 'elasticsearch'

    def _send_template(self):
        """
            Send template to the Elastcsearch Repository
            Directive to not analyze string field
        """
        t_access     = tpl_utils.get_template('elasticsearch-access')[0]
        t_pf         = tpl_utils.get_template('elasticsearch-pf')[0]
        t_vulture    = tpl_utils.get_template('elasticsearch-vulture')[0]
        t_diagnostic = tpl_utils.get_template('elasticsearch-diagnostic')[0]

        templates_els = {
            "vulture_access"    : t_access.render(index_name=self.es_access_index_name),
            "vulture_pf"        : t_pf.render(index_name=self.es_packetfilter_index_name),
            "vulture_logs"      : t_vulture.render(index_name=self.es_vulturelogs_index_name),
            "vulture_diagnostic": t_diagnostic.render(index_name=self.es_diagnostic_index_name)
        }

        for host in self.es_host.split(','):
            try:
                for index_name, template in templates_els.items():
                    success = request('PUT', "{}/_template/{}_template".format(host, index_name), data=template, headers={'Content-Type': 'application/json'})

                    if success.status_code != 200:
                        logger.info("Can't send {} template to ElasticSearch Node {}. Error: {}".format(index_name, host, success.text))

            except Exception as e:
                logger.info("Node Elasticsearch on host {} is down. Error: {}".format(host, e))
                continue

    def save(self, **kwargs):
        self.repo_type = 'data'  # ElasticSearch Repo can only support data
        self._send_template()
        return super(ElasticSearchRepository, self).save(**kwargs)

    def test_connection(self):
        url = "{}/_cluster/health?pretty".format(str(self.es_host).split(',')[0])
        session = Session()

        if self.es_user and self.es_password:
            request = Request("GET", url, headers={'Authorization': 'Basic {}'.format(
                b64encode('{}:{}'.format(self.es_user, self.es_password).encode('utf8')))}).prepare()
        else:
            request = Request("GET", url).prepare()

        return session.send(request, timeout=2).content.decode('utf8')


class SyslogRepository(BaseAbstractRepository):

    PROTO = (
            ('UDP', 'UDP'),
            ('TCP', 'TCP'),
    )
    KEEPALIVE = (
            ('on', 'On'),
            ('off', 'Off'),
    )

    syslog_host = StringField(verbose_name=_('Syslog server IP address'), required=True, help_text=_('192.168.1.1'))
    syslog_port = StringField(verbose_name=_('Syslog server port number'), required=True, help_text=_('601'))
    syslog_facility = StringField(verbose_name=_('Syslog facility'), required=True, default='local0', help_text=_('Syslog facility'))
    syslog_security = StringField(verbose_name=_('Syslog security level'), required=True, default='info', help_text=_('Syslog security level'))
    syslog_protocol = StringField(verbose_name=_('Syslog protocol'), required=True, choices=PROTO, default='UDP', help_text=_('Syslog network protocol'))

    is_internal = BooleanField(default=False)

    @property
    def type_uri(self):
        return 'syslog'

    def save(self, **kwargs):
        self.repo_type = 'data'  # Syslog Repo can only support data
        return super(SyslogRepository, self).save(**kwargs)


class OTPRepository(BaseAbstractRepository):
    OTP_TYPE = (
        ('phone', 'Phone'),
        ('email', 'Email'),
        ('onetouch', 'OneTouch'),
        ('totp', 'Time-based OTP'),
    )

    OTP_PHONE_SERVICE = (
         ('authy', 'Authy (sms and mobile app)'),
    )

    OTP_MAIL_SERVICE = (
        ('vlt_mail_service', 'Vulture mail service'),
    )

    api_key           = StringField(verbose_name=_("API KEY"), required=False, help_text=_('API KEY for Authy service'))
    key_length        = IntField(verbose_name=_("KEY LENGTH"), required=False, help_text=_('Key length for email authentication'), default=8, min_value=8, max_value=20)
    otp_type          = StringField(choices=OTP_TYPE, required=True, help_text=_('Type of OTP'))
    otp_phone_service = StringField(choices=OTP_PHONE_SERVICE, required=False, help_text=_('Phone service for OTP'))
    otp_mail_service  = StringField(choices=OTP_MAIL_SERVICE, required=False, help_text=_('Mail service for OTP'))
    otp_label         = StringField(default="Vulture App", required=False, help_text=_("Label to show in phone application"))
    is_internal = BooleanField(default=False)

    @property
    def type_uri(self):
        return "otp"

    def get_backend(self):
        """ Return Backend object. This object is used by Django Auth
        mechanism
        """
        if self.otp_type == 'phone' and self.otp_phone_service == 'authy':
            from gui.authy_backend import AuthyBackend
            return AuthyBackend(self)
        elif self.otp_type == 'email' and self.otp_mail_service == 'vlt_mail_service':
            from gui.vulturemail_backend import VultureMailBackend
            return VultureMailBackend(self)
        elif self.otp_type == 'onetouch' and self.otp_phone_service == 'authy':
            from gui.authy_backend import AuthyBackend
            return AuthyBackend(self)
        elif self.otp_type == "totp":
            from gui.totp_backend import TOTPBackend
            return TOTPBackend(self)
        else:
            raise NotImplemented("OTP Backend type not implemented yet")


    def save(self, **kwargs):
        self.repo_type = 'otp'
        if self.otp_mail_service == '':
            self.otp_mail_service = None
        if self.otp_phone_service == '':
            self.otp_phone_service = None
        return super(OTPRepository, self).save(**kwargs)


class KerberosRepository(BaseAbstractRepository):
    realm = StringField(verbose_name=_('Kerberos realm'), required=True,
                                default="VULTUREPROJECT.ORG", help_text=_('Kerberos realm'))
    domain_realm = StringField(verbose_name=_('Kerberos domain realm'), required=True,
                                default=".vultureproject.org", help_text=_('Kerberos domain'))

    kdc = StringField(verbose_name=_('KDCs'), required=True,
                      default="kdc1.vultureproject.org,kdc2.vultureproject.org",
                      help_text=_('Kerberos Domain Controler(s).'))

    admin_server = StringField(verbose_name=_('Admin server'), required=True,
                     default = "kdc1.vultureproject.org",
                     help_text = _('Administration server host (Typically, the master Kerberos server).'))
    krb5_service = StringField(verbose_name=_('KRB5 Service name'), required=True,
                               default="vulture.vultureproject.org", help_text=_('Kerberos Service Name'))

    keytab = StringField(verbose_name=_('Service keytab '), required=True,
                help_text = _('Keytab of the service used to contact KDC.'))

    is_internal = BooleanField(default=False)


    @property
    def type_uri(self):
        return 'kerberos'

    def get_backend(self):
        """ Return Backend object. This object is used by Django Auth
        mechanism

        :return: LDAPBackend object
        """
        from gui.kerberos_backend import KerberosBackend
        return KerberosBackend(self)

    def save(self, **kwargs):
        self.repo_type = 'auth'  # Kerberos Repo can only support auth
        result = super(KerberosRepository, self).save(**kwargs)
        krb5_modified.send(sender=self.__class__)
        return result


class RadiusRepository(BaseAbstractRepository):
    """ Class used to represent RADIUS repository object

    radius_host: IP Address used to contact RADIUS server
    radius_port: Port used to contact RADIUS server
    radius_nas_id: NAS_ID of RADIUS server
    radius_secret: Secret used to authenticate client
    """

    # Connection related attributes
    radius_host = StringField(verbose_name=_('Host'), required=True,
                            help_text=_('IP Address of RADIUS server'))
    radius_port = IntField(verbose_name=_('Port'), default=1812, required=True,
                            help_text=_('Listening authentication port of RADIUS server'))
    radius_nas_id = StringField(verbose_name=_('NAS_ID'), default="0", required=True,
                            help_text=_('NAS_ID of the RADIUS server'))
    radius_secret = StringField(verbose_name=_("Authentication secret"), required=True,
                            help_text=_('Secret used to authenticate clients'))
    radius_retry = IntField(verbose_name=_("Max retries to authenticate clients"), required=True,
                            default=3, help_text=_('Max number of retries to contact Radius server'))
    radius_timeout = IntField(verbose_name=_("Max timeout to authenticate clients"), required=True,
                            default=2, help_text=_('Max timeout to contact Radius server'))

    is_internal = BooleanField(default=False)


    @property
    def type_uri(self):
        return 'radius'

    def get_backend(self):
        """ Return Backend object. This object is used by Django Auth
        mechanism

        :return: RADIUSBackend object
        """
        from gui.radius_backend import RadiusBackend
        return RadiusBackend(self)

    def save(self, **kwargs):
        self.repo_type = 'auth'  # RADIUS Repo can only support authentication
        return super(RadiusRepository, self).save(**kwargs)


class LDAPRepository(BaseAbstractRepository):
    """ Class used to represent LDAP repository object

    ldap_host: IP Address used to contact LDAP server
    ldap_port: Port used to contact LDAP server
    ldap_protocol: LDAP protocol version
    ldap_encryption_scheme: Encryption scheme used by LDAP Server
    ldap_connection_dn: DN of LDAP service account
    ldap_password: password of LDAP service account
    ldap_base_dn: Base DN of LDAP filter
    ldap_user_scope: User LDAP search scope
    ldap_user_dn: User DN of LDAP filter (concatenated with Base DN)
    ldap_user_attr: Attribute which identify user (ex: SamAccountName)
    ldap_user_filter: User search filter
    ldap_user_account_locked_attr: Filter which permit to identify a locked
    account
    ldap_user_change_password_attr: Filter which permit to identify an expired
    password
    ldap_user_groups_attr: LDAP Attribute with list of group membership
    ldap_user_mobile_attr: LDAP attribute with user phone number
    ldap_user_email_attr: LDAP attribute with user email address
    ldap_group_scope: Group LDAP search scope
    ldap_group_dn: Group DN of LDAP filter (concatenated with Base DN)
    ldap_group_attr: Attribute which identify group
    ldap_group_filter: Group search filter
    ldap_group_member_attr: LDAP Attribute with list of users
    """

    LDAP_PROTO = (
            (2, 'LDAP v2'),
            (3, 'LDAP v3'),
    )
    LDAP_ENC_SCHEMES = (
            ('none', 'None (usual port: 389)'),
            ('ldaps', 'LDAPS (usual port: 636)'),
            ('start-tls', 'Start-TLS (usual port: 389)'),
    )
    LDAP_SCOPES = (
            (2, 'subtree (all levels under suffix)'),
            (1, 'one (one level under suffix)'),
            (0, 'base (the suffix entry only)'),
    )
    OAUTH2_TYPE_CHOICES = (('dict','Dictionnary of keys and values'),('list','List of values'))
    OAUTH2_TOKEN_CHOICES = (('header','Header'),('json','JSON'),('both','Header and JSON'))

    # Connection related attributes
    ldap_host = StringField(verbose_name=_('Host'), required=True,
                            help_text=_('IP Address of LDAP server'))
    ldap_port = IntField(verbose_name=_('Port'), default=389, required=True,
                         help_text=_('Listening port of LDAP server'))
    ldap_protocol = IntField(verbose_name=_('Protocol'), choices=LDAP_PROTO,
                             help_text=_('Version of your LDAP protocol'))
    ldap_encryption_scheme = StringField(verbose_name=_("Encryption scheme"),
                                         choices=LDAP_ENC_SCHEMES,
                                         help_text=_('LDAP encryption scheme'))
    ldap_connection_dn = StringField(verbose_name=_("Service account DN"),
                                     help_text=_('DN used by Vulture to perform'
                                                 ' LDAP query'), required=True)
    ldap_password = StringField(verbose_name=_("Service account password"),
                                help_text=_('Password of service account'),
                                required=True)
    ldap_base_dn = StringField(verbose_name=_("Base DN"), required=True,
                               help_text=_('Location in the directory from '
                                           'which the LDAP search begins'))
    # User search related attributes
    ldap_user_scope = IntField(verbose_name=_("User search scope"), choices=LDAP_SCOPES,
                               help_text=_('Deep of search operation'))
    ldap_user_dn = StringField(verbose_name=_("User DN"),
                               help_text=_('Location in the directory from '
                                           'which the user LDAP search begins'))
    ldap_user_attr = StringField(verbose_name=_("User attribute"), required=True, default='cn',
                                 help_text=_('Attribute which identify user'))
    ldap_user_filter = StringField(verbose_name=_("User search filter"), default='(objectclass=person)',
                                   help_text=_('Filter used to found user. '
                                               'Ex: (objectClass=person)'),
                                   required=True)
    ldap_user_account_locked_attr = StringField(verbose_name=_("Account locked "
                                                               "filter"),
                                                help_text=_('Filter used to'
                                                            'identify if an '
                                                            'account is locked. '
                                                            'Ex: (lockoutTime>=1)'))
    ldap_user_change_password_attr = StringField(verbose_name=_("Need change password "
                                                               "filter"),
                                                help_text=_('Filter used to'
                                                            'identify if an '
                                                            'account need to change'
                                                            'its password. Ex:'
                                                            ' (pwdLastSet=0)'))
    ldap_user_groups_attr = StringField(verbose_name=_("Group attribute"),
                                        help_text=_("Attribute which contains "
                                                    "user's group list"))
    ldap_user_mobile_attr = StringField(verbose_name=_("Mobile attribute"),
                                        help_text=_("Attribute which contains "
                                                    "user's mobile number"))
    ldap_user_email_attr = StringField(verbose_name=_("Email attribute"),
                                        help_text=_("Attribute which contains "
                                                    "user's email address"))
    # Group search related attributes
    ldap_group_scope = IntField(verbose_name=_("Group search scope"),
                                choices=LDAP_SCOPES,
                                help_text=_('Deep of search operation'))
    ldap_group_dn = StringField(verbose_name=_("Group DN"),
                                help_text=_('Location in the directory from '
                                           'which the group LDAP search begins'))
    ldap_group_attr = StringField(verbose_name=_("Group attribute"),
                                  help_text=_("Attribute which identify group"))
    ldap_group_filter = StringField(verbose_name=_("Group search filter"),
                                   help_text=_('Filter used to found group. Ex:'
                                               ' (objectClass=group)'))
    ldap_group_member_attr = StringField(verbose_name=_("Members attribute"),
                                         help_text=_("Attribute which contains"
                                                     " list of group members"))

    enable_oauth2 = BooleanField(default=False, help_text=_('Export oauth2 attributes'))
    oauth2_attributes = StringField(required=False, help_text=_('Oauth2 attribute(s)'))
    oauth2_type_return = StringField(choices=OAUTH2_TYPE_CHOICES,default='dict',required=True, help_text='Type of returned scope values')
    oauth2_token_return = StringField(choices=OAUTH2_TOKEN_CHOICES, default='header',required=True, help_text='Token response place (in header, or in response, or both)')
    oauth2_token_ttl = IntField(default=3600, required=True, help_text='Oauth2 token time to live (in seconds)')

    is_internal = BooleanField(default=False)

    @property
    def type_uri(self):
        return 'ldap'

    def get_backend(self):
        """ Return Backend object. This object is used by Django Auth
        mechanism

        :return: LDAPBackend object
        """
        from gui.ldap_backend import LDAPBackend
        return LDAPBackend(self)

    def get_phone_column(self):
        return self.ldap_user_mobile_attr

    def save(self, **kwargs):
        self.repo_type = 'auth'  # LDAP Repo can only support authentication
        return super(LDAPRepository, self).save(**kwargs)


class NTLMRepository(BaseAbstractRepository):
    pass
