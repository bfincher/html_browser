if [ -z $VIRTUAL_ENV ]; then
    image_name=bfincher/html_browser
else
    image_name=bfincher/$(basename $VIRTUAL_ENV)
fi
docker build -t $image_name .
