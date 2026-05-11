"""
Django settings for core project.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


def _env_csv(name, defaults):
    raw = os.getenv(name)
    if not raw or not raw.strip():
        return list(defaults)
    return [x.strip() for x in raw.split(',') if x.strip()]


def _merge_unique(base: tuple[str, ...], from_env_var: str) -> list[str]:
    '''Junta valores do .env aos de base, sem repetir ordem-preservada primeiro o que veio da env.'''
    return list(dict.fromkeys(_env_csv(from_env_var, base) + list(base)))


SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-!tt^&00ol0gb#=51ym(3^&6md-en@(+yvbll5*f85rd%w&8_gv')

DEBUG = os.getenv('DEBUG', 'False') == 'True'

_LOCAL_ALLOWED_HOSTS = ('localhost', '127.0.0.1', '0.0.0.0')
ALLOWED_HOSTS = _merge_unique(_LOCAL_ALLOWED_HOSTS, 'ALLOWED_HOSTS')

_LOCAL_CSRF_ORIGINS = (
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'http://localhost',
    'http://127.0.0.1',
)
CSRF_TRUSTED_ORIGINS = _merge_unique(_LOCAL_CSRF_ORIGINS, 'CSRF_TRUSTED_ORIGINS')


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'brain',
    'chat',
    'documents',
    'hub',
    'users',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# Database: PostgreSQL when POSTGRES_DB is set (e.g. Docker Compose); else SQLite.
if os.getenv('POSTGRES_DB'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ['POSTGRES_DB'],
            'USER': os.environ.get('POSTGRES_USER', 'postgres'),
            'PASSWORD': os.environ.get('POSTGRES_PASSWORD', ''),
            'HOST': os.environ.get('POSTGRES_HOST', 'localhost'),
            'PORT': os.environ.get('POSTGRES_PORT', '5432'),
        }
    }
else:
    DATABASE_PATH = BASE_DIR / 'db.sqlite3'
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': DATABASE_PATH,
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Persistent data (media, Chroma) — set DATA_DIR in Docker (e.g. /app/data)
_data_dir = os.getenv('DATA_DIR')
if _data_dir:
    DATA_DIR = Path(_data_dir)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
else:
    DATA_DIR = BASE_DIR

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = DATA_DIR / 'media'
MEDIA_ROOT.mkdir(parents=True, exist_ok=True)


# Auth
AUTH_USER_MODEL = 'users.User'
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'users.backends.EmailBackend',
]

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'landing'

# RAG
CHROMA_DB_PATH = DATA_DIR / 'chroma_db'
Path(CHROMA_DB_PATH).mkdir(parents=True, exist_ok=True)

LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'openai')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
AGENT_MODEL = os.getenv('AGENT_MODEL', 'gpt-5.4-mini')
AGENT_MAX_HISTORY = 10
OPENAI_EMBEDDING_MODEL = os.getenv('OPENAI_EMBEDDING_MODEL', 'text-embedding-3-small')

# Upload limits
MAX_UPLOAD_SIZE = 10 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = MAX_UPLOAD_SIZE
DATA_UPLOAD_MAX_MEMORY_SIZE = MAX_UPLOAD_SIZE

# Email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = f'Crivopy <{os.getenv("EMAIL_HOST_USER", "noreply@crivopy.com")}>'

SITE_URL = os.getenv('SITE_URL', 'http://127.0.0.1:8000')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
