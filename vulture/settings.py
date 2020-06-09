"""
Django settings for vulture project.
"""

import logging
import os

from vulture_toolkit.system.replica_set_client import ReplicaSetClient, ReplicaConnectionFailure

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Retrieving Django SECRET_KEY
try:
    from secret_key import SECRET_KEY
# File doesn't exist, we need to create it
except ImportError:
    from django.utils.crypto import get_random_string
    SETTINGS_DIR = os.path.abspath(os.path.dirname(__file__))
    chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
    secret_key = get_random_string(50, chars)

    with open(os.path.join(SETTINGS_DIR, 'secret_key.py'), 'w') as f:
        f.write("SECRET_KEY = '{}'\n".format(secret_key))

    from secret_key import SECRET_KEY

from vulture_toolkit.log.settings import LOG_SETTINGS, LOG_SETTINGS_FALLBACK

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ALLOWED_HOSTS = ["*"]

CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

CONN_MAX_AGE = None

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'gui',
    'api',
    "mongoengine.django.mongo_auth"
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    #'vulture.profiling.ProfileMiddleware',
)

TEMPLATE_DIRS = (
    '/home/vlt-gui/vulture/gui/templates/gui',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.request',
)

ROOT_URLCONF = 'vulture.urls'

WSGI_APPLICATION = 'vulture.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.dummy'
    }
}


AUTHENTICATION_BACKENDS = (
    'mongoengine.django.auth.MongoEngineBackend',
    #'gui.gui_auth_backend.GuiAuthBackend',
)

AUTH_USER_MODEL = 'mongo_auth.MongoUser'
MONGOENGINE_USER_DOCUMENT = 'gui.models.user_document.VultureUser'

SESSION_ENGINE = 'vulture_toolkit.auth.session'
SESSION_IDLE_TIMEOUT = 180
SESSION_COOKIE_AGE = 3600
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_NAME = "vltsessid"


LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

MEDIA_ROOT = '/home/vlt-gui/vulture/static/'
STATIC_URL = '/static/'

API_PORT = 8000
API_PROTO = 'https'
CACERT_DIR = '/var/db/mongodb/'
CONF_DIR = '/home/vlt-sys/Engine/conf/'
MONGODBPORT = 9091
MONGODBARBPORT = 9092
REDISIP='127.0.0.1'
REDISPORT='6379'
SENTINELPORT = '26379'
OS = "FreeBSD"
SVC_TEMPLATES_DIR = '/home/vlt-gui/vulture/vulture_toolkit/templates/'

# MongoDB connection
try:
    ReplicaSetClient()
except ReplicaConnectionFailure as e:
    pass

try:
    logging.config.dictConfig(LOG_SETTINGS)
except:
    logging.config.dictConfig(LOG_SETTINGS_FALLBACK)
