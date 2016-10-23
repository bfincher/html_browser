from django import template
from html_browser.models import Permission, CAN_READ, CAN_WRITE, CAN_DELETE

register = template.Library()

@register.filter
def readId(perm):
    return str(perm.getUserOrGroup()) + "-" + str(perm.getUserOrGroupName()) + "-read"

@register.filter
def writeId(perm):
    return str(perm.getUserOrGroup()) + "-" + str(perm.getUserOrGroupName()) + "-write"

@register.filter
def deleteId(perm):
    return str(perm.getUserOrGroup()) + "-" + str(perm.getUserOrGroupName()) + "-delete"

@register.filter
def readDisabled(perm):
    if perm.permission == CAN_READ:
        return ""
    else:
        return "disabled=disabled"

@register.filter
def writeChecked(perm):
    if perm.permission >= CAN_WRITE:
        return "checked=checked"
    else:
        return ""

@register.filter
def writeDisabled(perm):
    if perm.permission >= CAN_DELETE:
        return "disabled=disabled"
    else:
        return ""

@register.filter
def deleteChecked(perm):
    if perm.permission >= CAN_DELETE:
        return "checked=checked"
    else:
        return ""
