#!/usr/bin/env bash
# start-server.sh
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ] ; then
    (cd adaptive_policy_sync; python manage.py createsuperuser --no-input)
fi
if [ -n "$DJANGO_SUPERUSER_APIKEY" ] ; then
    (cd adaptive_policy_sync; python manage.py runscript import_token --script-args $DJANGO_SUPERUSER_USERNAME $DJANGO_SUPERUSER_APIKEY)
fi
(cd adaptive_policy_sync; gunicorn adaptive_policy_sync.wsgi --user www-data --bind 0.0.0.0:8010 --workers 3) &
nginx -g "daemon off;"
