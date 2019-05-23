#!/bin/sh
set -e

USER=hb

getent passwd $USER || useradd $USER -m -d /hb

if [ ! -z "$APP_UID" ]; then
    usermod -u $APP_UID $USER
fi

if [ ! -z "$APP_GID" ]; then
    getent group $APP_GID || groupadd -g $APP_GID g_"$APP_GID"
    usermod -g $APP_GID $USER
fi

cd /hb
APP_CONFIG_UIDGID="${APP_UID:=0}:${APP_GID:=0}"

if [ ! -d ${APP_CONFIG}/logs/hb ]; then
    su ${USER} -c "mkdir -p ${APP_CONFIG}/logs/hb"
fi

if [ ! -f ${APP_CONFIG}/local_settings.json ]; then
    su ${USER} -c "cp /hb/html_browser_site/local_settings_docker.json ${APP_CONFIG}/local_settings.json"
fi

if [ ! -f ${APP_CONFIG}/hb.db ]; then
    su ${USER} -c "python manage.py migrate"
    echo "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@example.com', 'pass')" | python manage.py shell
fi
if [ $(stat -c "%u:%g" ${APP_CONFIG}) != "${APP_CONFIG_UIDGID}" ]; then
    chown -R ${APP_CONFIG_UIDGID} "$APP_CONFIG"
fi

chown -R ${USER}:g_${APP_GID} /hb/folder_links

su ${USER} -c 'python manage.py runserver 0.0.0.0:8000'



