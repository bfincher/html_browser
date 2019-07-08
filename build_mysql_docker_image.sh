if [ -z $VIRTUAL_ENV ]; then
    image_name=bfincher/html_browser:alpine-mysql
else
    image_name=bfincher/$(basename $VIRTUAL_ENV):alpine-mysql
fi
docker build -t $image_name -f Dockerfile_mysql . 
