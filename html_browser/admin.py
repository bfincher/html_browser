from django.contrib import admin

from .models import Folder, GroupPermission, UserPermission


class FolderAdmin(admin.ModelAdmin):
    pass


class UserPermissionAdmin(admin.ModelAdmin):
    pass


class GroupPermissionAdmin(admin.ModelAdmin):
    pass


admin.site.register(Folder, FolderAdmin)
admin.site.register(UserPermission, UserPermissionAdmin)
admin.site.register(GroupPermission, GroupPermissionAdmin)
