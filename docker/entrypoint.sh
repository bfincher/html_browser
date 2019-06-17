#!/bin/sh
set -e

#while true; do date; sleep 1; done

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
    su ${USER} -c "cp /hb/html_browser/local_settings/local_settings_docker.json ${APP_CONFIG}/local_settings.json"
fi

if [ -f ${APP_CONFIG}/hb.db.bak8 ]; then
    su ${USER} -c "cp ${APP_CONFIG}/hb.db.bak8 ${APP_CONFIG}/hb.db.bak9"
fi
if [ -f ${APP_CONFIG}/hb.db.bak7 ]; then
    su ${USER} -c "cp ${APP_CONFIG}/hb.db.bak7 ${APP_CONFIG}/hb.db.bak8"
fi
if [ -f ${APP_CONFIG}/hb.db.bak6 ]; then
    su ${USER} -c "cp ${APP_CONFIG}/hb.db.bak6 ${APP_CONFIG}/hb.db.bak7"
fi
if [ -f ${APP_CONFIG}/hb.db.bak5 ]; then
    su ${USER} -c "cp ${APP_CONFIG}/hb.db.bak5 ${APP_CONFIG}/hb.db.bak6"
fi
if [ -f ${APP_CONFIG}/hb.db.bak4 ]; then
    su ${USER} -c "cp ${APP_CONFIG}/hb.db.bak4 ${APP_CONFIG}/hb.db.bak5"
fi
if [ -f ${APP_CONFIG}/hb.db.bak3 ]; then
    su ${USER} -c "cp ${APP_CONFIG}/hb.db.bak3 ${APP_CONFIG}/hb.db.bak4"
fi
if [ -f ${APP_CONFIG}/hb.db.bak2 ]; then
    su ${USER} -c "cp ${APP_CONFIG}/hb.db.bak2 ${APP_CONFIG}/hb.db.bak3"
fi
if [ -f ${APP_CONFIG}/hb.db.bak1 ]; then
    su ${USER} -c "cp ${APP_CONFIG}/hb.db.bak1 ${APP_CONFIG}/hb.db.bak2"
fi

if [ -f ${APP_CONFIG}/hb.db ]; then
    su ${USER} -c "cp ${APP_CONFIG}/hb.db ${APP_CONFIG}/hb.db.bak1"
else
    su ${USER} -c "python manage.py migrate"
    echo "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@example.com', 'pass')" | python manage.py shell
fi

if [ $(stat -c "%u:%g" ${APP_CONFIG}) != "${APP_CONFIG_UIDGID}" ]; then
    chown -R ${APP_CONFIG_UIDGID} "$APP_CONFIG"
fi

CRON_CMD="cd /hb/ && bash -l -c 'python manage.py thumbnail cleanup > /dev/null'"

CRON_PERIOD="0 0 * * *"
(crontab -u $USER -l ; echo "${CRON_PERIOD}   ${CRON_CMD}") | sort - | uniq - | crontab -u $USER -

/usr/sbin/nginx
su ${USER} -c 'gunicorn html_browser.wsgi:application --bind 0.0.0.0:8000 --timeout 300'

