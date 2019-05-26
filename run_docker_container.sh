if [ -z $VIRTUAL_ENV ]; then
    image_name=html_browser_web
else
    image_name=$(basename $VIRTUAL_ENV)
fi

docker run -d \
    -p 8000:8000 \
    -v /Volumes/data1/code/workspace/html_browser/config:/config \
    -v /Volumes/data1:/data1 \
    -e APP_UID=1009 \
    -e APP_GID=1009 \
    --name=$image_name \
    --restart unless-stopped \
    $image_name
