if [ -z $VIRTUAL_ENV ]; then
    image_name=bfincher/html_browser:alpine-sqlite
else
    image_name=bfincher/$(basename $VIRTUAL_ENV):alpine-sqlite
fi
docker build -t $image_name .
