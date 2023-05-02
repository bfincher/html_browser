#!/bin/bash -e

flake8 .
./pylint.sh ./html_browser
mypy html_browser
python manage.py test
