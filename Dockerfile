from bfincher/ubuntu-python3:bionic

env PYTHONBUFFERED 1

RUN mkdir /hb
workdir /hb

copy requirements.txt /hb/requirements.txt

run apt-get install -y python3-pillow nginx cron && \
    pip install --no-cache -r requirements.txt && \
    pip install --no-cache gunicorn==19.9.0 && \
    find /usr/local \
        \( -type d -a -name test -o -name tests \) \
        -o \( -type f -a -name '*.pyc' -o -name '*.pyo' \) \
        -exec rm -rf '{}' + 

copy docker/nginx.conf /etc/nginx/sites-enabled/default
copy html_browser/ /hb/html_browser/
copy html_browser/local_settings/local_settings_docker_sqlite.py /hb/html_browser/local_settings/local_settings.py
copy html_browser/local_settings/local_settings_docker_sqlite.json /hb/html_browser/local_settings/local_settings.json

run /etc/init.d/nginx stop && /etc/init.d/nginx start

ENV APP_CONFIG="/config"

copy media/ /hb/media/

copy manage.py /hb
copy docker/entrypoint.sh /entrypoint.sh
copy docker/init_sqlite.sh /init_db.sh

EXPOSE 80
VOLUME /config /data1 /data2

#ENTRYPOINT ["/bin/bash"]
ENTRYPOINT ["/entrypoint.sh"]
