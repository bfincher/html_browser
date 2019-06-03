version=$(cat version.txt)
if [ -z $VIRTUAL_ENV ]; then
    image_name=html_browser_web:$version
else
    image_name=$(basename $VIRTUAL_ENV):$version
fi
docker build -t $image_name .
