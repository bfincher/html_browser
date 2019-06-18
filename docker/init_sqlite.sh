#!/bin/bash

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
fi