"""
A set of request processors that return dictionaries to be merged into a
template context. Each function takes the request object as its only parameter
and returns a dictionary to add to the context.

These are referenced from the 'context_processors' option of the configuration
of a DjangoTemplates backend and used by RequestContext.
"""

from .constants import _constants as const


def images(request): #pylint: disable=unused-argument
    return {'IMAGE_URL': const.IMAGE_URL}


def media(request): #pylint: disable=unused-argument
    return {'MEDIA_URL': const.MEDIA_URL}
