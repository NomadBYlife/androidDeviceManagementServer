"""
Django settings for androidDeviceManagementServer project.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

import os

from django.utils.log import DEFAULT_LOGGING as DJANGO_DEFAULT_LOGGING

from log_config import syslog_tup, handler_list, set_log_level

# try:
#     from db_config import DATABASES
# except ImportError as e:
#     log = set_log_level()
#     log.critical("Error! Failed to Load 'DATABASE' config from config file db_config.py!")
#     print(e)
#     exit(1)

log = set_log_level()

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

team_city_build_id = os.environ.get("TEAMCITY_BUILD_ID")
TEST_RUNNER = 'django.test.runner.DiscoverRunner'
if team_city_build_id is not None:
    TEST_RUNNER = 'teamcity.django.TeamcityDjangoRunner'

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'x=0ffgl=&qzf$x--)t$&%^!f*#%o4*zmg)ii4q9&&!5_$r^j=@'

# SECURITY WARNING: don't run with debug turned on in production!
# BUG WARNING: If you don't the admin page is messed up since Django 2.1.7+
DEBUG = True
# DEBUG = False

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'emulators1.testagent.dev.kobil.com', '*']

# Application definition

INSTALLED_APPS = [
    'channels',
    'django.contrib.admindocs',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'devices.apps.DevicesConfig',
    'background_task',
    'notifications',
    'socket_client',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'androidDeviceManagementServer.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'devices', 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'devices.models.context_refresh',
            ],
        },
    },
]

WSGI_APPLICATION = 'androidDeviceManagementServer.wsgi.application'

# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases
# configured in db_config.py located in root folder of this project

DATABASES = { # TEST
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        # 'NAME': 'armstestdb',
        'NAME': 'db_learn',
        # 'USER': 'armstestuser',
        'USER': 'postgres',
        # 'PASSWORD': 'atu-Passwd-123',
        'PASSWORD': 'postgres',
        # 'HOST': 'test-postgres-db.teamcity.dev.kobil.com',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}
# DATABASES = { # prod
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql_psycopg2',
#         'NAME': 'armsproddb',
#         'USER': 'kobil',
#         'PASSWORD': 'kobil123',
#         'HOST': 'emulators1.testagent.dev.kobil.com',
#         'PORT': '5432',
#     }
# }

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/Berlin'

USE_I18N = True

USE_L10N = True

USE_TZ = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_URL = '/static/'

# example of how to add items to the default logger
# '%(asctime)s#%(levelname)s#%(module)s#%(funcName)s#line:%(lineno)d\n\t%(message)s'
DJANGO_DEFAULT_LOGGING['formatters'].update({
    'adms.views': {
        'format': '%(asctime)s # %(levelname)s # %(module)s # %(funcName)s # line:%(lineno)d\n\t%(message)s',
    }
})
DJANGO_DEFAULT_LOGGING['handlers'].update({
    'adms.console': {
        'level': 'NOTSET',
        'class': 'logging.StreamHandler',
        'formatter': 'adms.views',
    },
    'adms.syslog': {
        'level': 'NOTSET',
        'class': 'logging.handlers.SysLogHandler',
        'address': syslog_tup,
        'formatter': 'adms.views',
    }
})

DJANGO_DEFAULT_LOGGING['loggers'].update({
    'adms.views': {
        'handlers': handler_list,
        'level': 'INFO',
        'propagate': False
    },
    'django.server': {
        'level': 21,
    }
})
"""
DEFAULT_LOGGING['handlers']['console'].update({
    'level': 'DEBUG'
})
DEFAULT_LOGGING['handlers']['django.server'].update({
    'level': 'DEBUG'
})
DEFAULT_LOGGING['loggers']['django'].update({
        'level': 'DEBUG',
})
DEFAULT_LOGGING['loggers']['django.server'].update({
        'level': 'DEBUG',
})
"""

# Конфигурация Channels
ASGI_APPLICATION = "androidDeviceManagementServer.asgi.application"
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}
