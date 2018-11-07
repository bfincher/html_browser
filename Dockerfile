from python:2.7.12

env PYTHONBUFFERED 1

RUN mkdir /hb
workdir /hb

add html_browser /hb
add html_browser_site /hb
add manage.py /hb
add requirements.txt /hb

run pip install -r requirements.txt

