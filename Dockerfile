from python:3.5

env PYTHONBUFFERED 1

RUN mkdir /hb
workdir /hb

copy html_browser/ /hb/html_browser/
copy html_browser_site/ /hb/html_browser_site/
copy html_browser_site/local_settings_docker.py /hb/html_browser_site/local_settings.py
copy html_browser_site/local_settings_docker.json /hb/html_browser_site/local_settings.json
copy media/ /hb/media/

copy manage.py /hb
copy requirements.txt /hb

run pip install -r requirements.txt 

ENV APP_CONFIG="/config"
copy entrypoint.sh /

EXPOSE 8000
VOLUME /config /data1 /data2

ENTRYPOINT ["/entrypoint.sh"]
CMD ["manage.py runserver 0.0.0.0:8000
