"""
A set of request processors that return dictionaries to be merged into a
template context. Each function takes the request object as its only parameter
and returns a dictionary to add to the context.

These are referenced from the 'context_processors' option of the configuration
of a DjangoTemplates backend and used by RequestContext.
"""

from __future__ import unicode_literals

import itertools

from django.conf import settings
from django.middleware.csrf import get_token
from django.utils.encoding import smart_text
from django.utils.functional import SimpleLazyObject, lazy

def images(request):
    """
    Adds media-related context variables to the context.
    """
    return {'IMAGE_URL': settings.IMAGE_URL}

