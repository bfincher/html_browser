if [ -z $VIRTUAL_ENV ]; then
    image_name=html_browser
else
    image_name=$(basename $VIRTUAL_ENV)
fi
docker build -t $image_name --pull .
