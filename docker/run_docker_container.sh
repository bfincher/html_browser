THIS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

UID=1000
GID=1000
USERNAME=$(getent passwd $UID | gawk -F':' '{ print $1}')
GROUPNAME=$(getent group $GID | gawk -F':' '{ print $1}')

if [ -z $VIRTUAL_ENV ]; then
    image_name=html_browser_web
    CONFIG=${THIS_DIR}/config
else
    image_name=$(basename $VIRTUAL_ENV)
    CONFIG=${THIS_DIR}/config_$image_name
fi

if [ ! -d $CONFIG ]; then
    mkdir $CONFIG
fi

chown -R ${USERNAME}:${GROUPNAME} $CONFIG


if [ $# -eq 1 ]; then
    port=$1
else
    port=8000
fi

docker run -d \
    -p $port:80 \
    -v ${CONFIG}:/config \
    -v /Volumes/data1:/data1 \
    -e APP_UID=$UID \
    -e APP_GID=$GID \
    --name=$image_name \
    --restart unless-stopped \
    $image_name