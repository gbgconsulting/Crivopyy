#!/bin/sh
set -e
python manage.py migrate --noinput
python manage.py collectstatic --noinput

_reload=
_workers='2'
case "${GUNICORN_RELOAD:-1}" in
    0|false|FALSE|no|NO|'')
        ;;
    *)
        _reload='--reload'
        _workers='1'
        ;;
esac

exec gunicorn core.wsgi:application --bind "0.0.0.0:${PORT:-8000}" --workers "${_workers}" --timeout 120 ${_reload}
