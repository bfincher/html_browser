#!/bin/bash
#java -version
#java -jar /usr/local/tomcat/thumbnail.jar /mnt/nfs/Pictures /usr/local/tomcat/webapps/thumbs > /usr/local/tomcat/logs/thumbnail.log

python /srv/www/hb/media/thumbnail.py /mnt/nfs/Pictures /srv/www/hb/media/Pictures > /var/log/thumbnail.log 2>&1

