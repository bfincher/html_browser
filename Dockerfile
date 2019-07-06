from bfincher/alpine-python3:3.10

env PYTHONBUFFERED 1

RUN mkdir /hb
workdir /hb
copy requirements.txt /hb/requirements.txt

run apk add --no-cache py3-pillow nginx && \
    grep -v Pillow requirements.txt | pip install --no-cache -r /dev/stdin && \
    pip install --no-cache gunicorn==19.9.0 && \
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
