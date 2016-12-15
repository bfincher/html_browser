# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2016-10-22 21:31


from django.db import migrations


def convertPerm(permModel):
    for perm in permModel.objects.all():
        if perm.tempOldpermission == 'R':
            perm.permission = 1
        elif perm.tempOldpermission == 'W':
            perm.permission = 2
        elif perm.tempOldpermission == 'D':
            perm.permission = 3
        else:
            raise Exception('Unexpected perm: %s' % perm.tempOldpermission[1])
        perm.save()


class Migration(migrations.Migration):

    def postMigrate(apps, schema_editor):
        userPermModel = apps.get_model('html_browser', 'UserPermission')
        convertPerm(userPermModel)

        groupPermModel = apps.get_model('html_browser', 'GroupPermission')
        convertPerm(groupPermModel)

    dependencies = [
        ('html_browser', '0004_auto_20161022_1631'),
    ]

    operations = [
        migrations.RunPython(postMigrate),
    ]
