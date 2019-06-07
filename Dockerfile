from alpine:3.9.4

env PYTHONBUFFERED 1

RUN mkdir /hb
workdir /hb

run apk add --no-cache py3-pillow shadow bash nginx

copy requirements.txt /hb/requirements.txt

run ln -s /usr/bin/python3.6 /usr/bin/python && \
    ln -s /usr/bin/pip3 /usr/bin/pip && \
    grep -v mysql requirements.txt | grep -v Pillow > requirements_minus_mysql.txt && \ 
    pip install --no-cache -r requirements_minus_mysql.txt && \
    rm requirements.txt requirements_minus_mysql.txt && \
    pip install --no-cache gunicorn==19.9.0 && \
    rm /etc/nginx/conf.d/default.conf && \
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

copy nginx.conf /etc/nginx/conf.d
copy html_browser/ /hb/html_browser/
copy html_browser_site/ /hb/html_browser_site/
copy html_browser_site/local_settings_docker.py /hb/html_browser_site/local_settings.py

ENV APP_CONFIG="/config"

copy media/ /hb/media/

copy manage.py /hb
copy entrypoint.sh /

EXPOSE 8000
VOLUME /config /data1 /data2

#ENTRYPOINT ["/bin/bash"]
ENTRYPOINT ["/entrypoint.sh"]
