from .models import Folder, UserPermission, GroupPermission
from django.contrib import admin

class FolderAdmin(admin.ModelAdmin):
    pass

class UserPermissionAdmin(admin.ModelAdmin):
    pass

class GroupPermissionAdmin(admin.ModelAdmin):
    pass

admin.site.register(Folder, FolderAdmin)
admin.site.register(UserPermission, UserPermissionAdmin)
admin.site.register(GroupPermission, GroupPermissionAdmin)
