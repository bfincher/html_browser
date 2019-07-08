#!/bin/sh
set -e

#while true; do date; sleep 1; done

export USER=hb

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
    su ${USER} -c "cp /hb/html_browser/local_settings/local_settings.json ${APP_CONFIG}/local_settings.json"
fi

if [ $(stat -c "%u:%g" ${APP_CONFIG}) != "${APP_CONFIG_UIDGID}" ]; then
    chown -R ${APP_CONFIG_UIDGID} "$APP_CONFIG"
fi

/init_db.sh

su ${USER} -c "python manage.py migrate"
python manage.py create_superuser_with_password --user admin --password pass --noinput --email 'admin@example.com' --if-no-superuser

CRON_CMD="cd /hb/ && bash -l -c 'python manage.py thumbnail cleanup > /dev/null'"

CRON_PERIOD="0 0 * * *"
(crontab -u $USER -l ; echo "${CRON_PERIOD}   ${CRON_CMD}") | sort - | uniq - | crontab -u $USER -

/usr/sbin/nginx
su ${USER} -c 'gunicorn html_browser.wsgi:application --bind 0.0.0.0:8000 --timeout 300'

