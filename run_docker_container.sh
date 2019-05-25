docker run -d \
    -p 8000:8000 \
    -v /Volumes/data1/code/workspace/html_browser/config:/config \
    -v /Volumes/data1:/data1 \
    -e APP_UID=1009 \
    -e APP_GID=1009 \
    --name=html_browser \
    --restart unless-stopped \
    html_browser_web
