import re
from typing import Dict

from html_browser import settings
from html_browser.models import Folder

BEGIN_DYNAMIC_CONFIG = '#BEGIN_DYNAMIC_CONFIG'
END_DYNAMIC_CONFIG = '#END_DYNAMIC_CONFIG'
DOWNLOAD_URL_PREFIX = 'download_'

LOCATION_REGEX = re.compile(fr'/{DOWNLOAD_URL_PREFIX}(.*?)/')


class IllegalStateError(RuntimeError):
    pass


def read_config() -> Dict[str, str]:
    if not settings.NGINX_DOWNLOADS:
        raise IllegalStateError()

    with open(settings.NGINX_CONFIG_FILE, 'r') as f:
        lines = [line.rstrip() for line in f]

    i = 0
    while not lines[i].startswith(BEGIN_DYNAMIC_CONFIG):
        i += 1

    i += 1
    firstIdx = i
    while not lines[i].startswith(END_DYNAMIC_CONFIG):
        i += 1

    lastIdx = i

    i = firstIdx
    while i <= lastIdx:

