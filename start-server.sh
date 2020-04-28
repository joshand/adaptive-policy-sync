#!/usr/bin/env bash
# start-server.sh
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ] ; then
    (cd adaptive_policy_sync; python manage.py createsuperuser --no-input)
fi
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ] && [ -n "$DJANGO_SUPERUSER_APIKEY" ] ; then
    (cd adaptive_policy_sync; python manage.py runscript import_token --script-args $DJANGO_SUPERUSER_USERNAME $DJANGO_SUPERUSER_APIKEY)
fi
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ] && [ -n "$SIMULATED_ENVIRONMENT_URL" ] ; then
    (cd adaptive_policy_sync; python manage.py runscript dashboard_simulator --script-args 10 5 5 5; python manage.py runscript ise_ers_simulator --script-args 5 5 5; cd scripts; chown www-data:www-data *.json)
    echo "===================================================="
    echo "For Cisco ISE, use the following settings:"
    echo "1) IP Address: $SIMULATED_ENVIRONMENT_URL/ise"
    echo "2) Username/Password: (not required; enter anything)"
    echo "===================================================="
    echo "For Meraki Dashboard, use the following settings:"
    echo "1) Path: $SIMULATED_ENVIRONMENT_URL/meraki/api/v1"
    echo "2) API Key: (not required; enter anything)"
    echo "===================================================="
fi
(cd adaptive_policy_sync; gunicorn adaptive_policy_sync.wsgi --user www-data --bind 0.0.0.0:8010 --workers 3 --preload) &
#(cd adaptive_policy_sync; python manage.py runscript dashboard_monitor) &
#(cd adaptive_policy_sync; python manage.py runscript ise_monitor) &
#(cd adaptive_policy_sync; python manage.py runscript clean_tasks) &
nginx -g "daemon off;"
