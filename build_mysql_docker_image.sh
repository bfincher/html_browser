if [ -z $VIRTUAL_ENV ]; then
    image_name=html_browser_mysql
else
    image_name=$(basename $VIRTUAL_ENV)_mysql
fi
docker build -t $image_name -f Dockerfile_mysql . 
