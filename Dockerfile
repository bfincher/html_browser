from ubuntu:xenial

env PYTHONBUFFERED 1

RUN mkdir /hb
workdir /hb

run apt update && apt install -y python3 python3-pillow shadow bash nginx net-tools python3-pip

copy requirements.txt /hb/requirements.txt

run ln -s /usr/bin/python3.6 /usr/bin/python && \
    ln -s /usr/bin/pip3 /usr/bin/pip && \
    pip install --no-cache -r requirements.txt && \
    pip install --no-cache gunicorn==19.9.0 && \
    rm /etc/nginx/conf.d/default.conf && \
    mkdir -p /run/nginx && \
    apt uninstall -y python3-pip && \
    apt auto-remove -y && \
    find /usr/local \
        \( -type d -a -name test -o -name tests \) \
        -o \( -type f -a -name '*.pyc' -o -name '*.pyo' \) \
        -exec rm -rf '{}' + 

copy docker/nginx.conf /etc/nginx/conf.d
copy html_browser/ /hb/html_browser/
copy html_browser/local_settings/local_settings_docker_sqlite.py /hb/html_browser/local_settings/local_settings.py
copy html_browser/local_settings/local_settings_docker_sqlite.json /hb/html_browser/local_settings/local_settings.json

ENV APP_CONFIG="/config"

copy media/ /hb/media/

copy manage.py /hb
copy docker/entrypoint.sh /entrypoint.sh
copy docker/init_sqlite.sh /init_db.sh

EXPOSE 80
VOLUME /config /data1 /data2

#ENTRYPOINT ["/bin/bash"]
ENTRYPOINT ["/entrypoint.sh"]
