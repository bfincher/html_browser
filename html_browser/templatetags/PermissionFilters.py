from django import template
from html_browser.models import Permission

register = template.Library()

@register.filter
def readId(perm):
    return str(perm.getUserOrGroup()) + "-" + str(perm.getUserOrGroupName) + "-read"

@register.filter
def writeId(perm):
    return str(perm.getUserOrGroup()) + "-" + str(perm.getUserOrGroupName) + "-write"

@register.filter
def deleteId(perm):
    return str(perm.getUserOrGroup()) + "-" + str(perm.getUserOrGroupName) + "-delete"

@register.filter
def readDisabled(perm):
    if perm.permission == 'R':
        return ""
    else:
        return "disabled=disabled"

@register.filter
def writeChecked(perm):
    if perm.permission == 'R':
        return ""
    else:
        return "checked=checked"

@register.filter
def writeDisabled(perm):
    if perm.permission == 'D':
        return "disabled=disabled"
    else:
        return ""

@register.filter
def deleteChecked(perm):
    if perm.permission == 'D':
        return "checked=checked"
    else:
        return ""
