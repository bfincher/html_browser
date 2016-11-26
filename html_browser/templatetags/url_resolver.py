from django import template
from django.core.urlresolvers import reverse

from html_browser.views.base_view import reverseContentUrl

import logging
import os

logger = logging.getLogger('html_browser.base_view')

register = template.Library()

@register.simple_tag(takes_context=True)
def get_content_url(context, currentFolder=None):
    if currentFolder is None:
        currentFolder = context['currentFolder']
    currentPath = context.get('currentPath', None)

    return reverseContentUrl(currentFolder, currentPath)

@register.simple_tag(takes_context=True)
def get_download_url(context, fileName):
    currentFolder = context['currentFolder']
    currentPath = context.get('currentPath', None)

    if currentPath:
        path = os.path.join(currentPath.encode('utf-8'), fileName.encode('utf-8'))
    else:
        path = fileName

    return reverse('download', kwargs={'currentFolder': currentFolder, 'path': path})

@register.simple_tag(takes_context=True)
def get_imageview_url(context, fileName):
    currentFolder = context['currentFolder']
    currentPath = context['currentPath']

    if currentPath:
        path = os.path.join(currentPath.encode('utf-8'), fileName.encode('utf-8'))
    else:
        path = fileName.encode('utf-8')
    return reverse('imageView', kwargs={'currentFolder': currentFolder, 'currentPath': path}) 
    
