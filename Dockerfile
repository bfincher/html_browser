from html_browser_base:2.0.0

env PYTHONBUFFERED 1

RUN mkdir /hb
workdir /hb

copy html_browser/ /hb/html_browser/
copy html_browser_site/ /hb/html_browser_site/
copy html_browser_site/local_settings_docker.py /hb/html_browser_site/local_settings.py
copy html_browser_site/local_settings_docker.json /hb/html_browser_site/local_settings.json

ENV APP_CONFIG="/config"

copy media/ /hb/media/

copy manage.py /hb
copy requirements.txt /hb/requirements.txt

run grep -v mysql requirements.txt | grep -v Pillow > requirements_minus_mysql.txt && \ 
    pip install --no-cache -r requirements_minus_mysql.txt && \
    rm requirements.txt requirements_minus_mysql.txt && \
    find /usr/local \
        \( -type d -a -name test -o -name tests \) \
        -o \( -type f -a -name '*.pyc' -o -name '*.pyo' \) \
        -exec rm -rf '{}' + 

copy entrypoint.sh /

EXPOSE 8000
VOLUME /config /data1 /data2

#ENTRYPOINT ["/bin/bash"]
ENTRYPOINT ["/entrypoint.sh"]
