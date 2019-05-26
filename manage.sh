#!/bin/bash
VE=${VIRTUAL_ENV:-/usr}
py3=$VE/bin/python3
$py3 manage.py $@
