"""
A set of request processors that return dictionaries to be merged into a
template context. Each function takes the request object as its only parameter
and returns a dictionary to add to the context.

These are referenced from the 'context_processors' option of the configuration
of a DjangoTemplates backend and used by RequestContext.
"""

from .constants import _constants as const
from django.conf import settings


def images(request):
    return {'IMAGE_URL': const.IMAGE_URL}


def media(request):
    return {'MEDIA_URL': const.MEDIA_URL}
