#!/bin/bash
#java -version
#java -jar /usr/local/tomcat/thumbnail.jar /mnt/nfs/Pictures /usr/local/tomcat/webapps/thumbs > /usr/local/tomcat/logs/thumbnail.log

python thumbnail.py /mnt/nfs/Pictures /srv/www/hb/media/thumbs > /var/log/thumbnail.log 2>&1

