from alpine:3.9.4

env PYTHONBUFFERED 1

RUN mkdir /hb
workdir /hb

run apk add --no-cache py3-pillow shadow bash nginx mariadb mariadb-client

copy requirements.txt /hb/requirements.txt

run ln -s /usr/bin/python3.6 /usr/bin/python && \
    ln -s /usr/bin/pip3 /usr/bin/pip && \
    apk add --no-cache --virtual .builddeps mariadb-dev gcc musl-dev && \
    pip install --no-cache -r requirements.txt && \
    pip install --no-cache gunicorn==19.9.0 && \
    apk del .builddeps && \
    rm /etc/nginx/conf.d/default.conf && \
    mkdir -p /run/nginx && \
    find /usr/local \
        \( -type d -a -name test -o -name tests \) \
        -o \( -type f -a -name '*.pyc' -o -name '*.pyo' \) \
        -exec rm -rf '{}' + \
    && runDeps="$( \
        scanelf --needed --nobanner --recursive /usr/local \
                | awk '{ gsub(/,/, "\nso:", $2); print "so:" $2 }' \
                | sort -u \
                | xargs -r apk info --installed \
                | sort -u \
    )" \
    && apk add --virtual .rundeps $runDeps 

copy docker/nginx.conf /etc/nginx/conf.d
copy html_browser/ /hb/html_browser/
copy html_browser/local_settings/local_settings_docker.py /hb/html_browser/local_settings/local_settings.py
copy html_browser/local_settings/local_settings_docker.json /hb/html_browser/local_settings/local_settings.json

ENV APP_CONFIG="/config"

copy media/ /hb/media/

copy manage.py /hb
copy docker/entrypoint.sh /

EXPOSE 80
VOLUME /config /data1 /data2

#ENTRYPOINT ["/bin/bash"]
ENTRYPOINT ["/entrypoint.sh"]
