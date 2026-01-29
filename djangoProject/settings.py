from pathlib import Path
import ssl
import os
from django.conf import settings

ssl._create_default_https_context = ssl._create_unverified_context

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-9^61cl@$!-l71$$lg5(*vc_)(#+liix)3y62cyhrqop)*!p_m!'

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    "myapp.apps.MyappConfig",
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

ROOT_URLCONF = 'djangoProject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'djangoProject.wsgi.application'

# Database
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }

DATABASES = {

    'default': {
        'ENGINE': 'django.db.backends.mysql',  # 默认
        'NAME': 'data_practice',  #一定要存在的数据库名
        'HOST': '127.0.0.1',  # mysql的ip地址
        'PORT': 3306, # mysql的端口
        'USER': 'root',  # mysql的用户名
        'PASSWORD': 'zhai3716'  # mysql的密码
    }

}

# Password validation
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
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# 缓存配置
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '[%(asctime)s] [%(levelname)s] %(name)s: %(message)s',
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',          # 设置日志级别（DEBUG/INFO/WARNING/ERROR/CRITICAL）
            'class': 'logging.FileHandler',
            'filename': os.path.join(settings.BASE_DIR, 'logs/debug.log'),  # 日志文件路径
            'formatter': 'standard',
        },
    },
    'loggers': {
        '': {  # 根日志记录器
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'your_app_name': {  # 你的应用名称
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': False,  # 防止重复记录
        },
    },
}
# 阈值分割
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')  # 存储上传和处理后的文件
MEDIA_URL = '/media/'  # 访问媒体文件的 URL 前缀