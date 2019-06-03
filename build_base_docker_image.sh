version=$(cat version.txt)
image_name=html_browser_base:$version
docker build -f Dockerfile_base -t $image_name --pull .
