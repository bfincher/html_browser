# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2016-10-22 21:31


from django.db import migrations


def convertPerm(permModel):
    for perm in permModel.objects.all():
        perm.p2 = int(perm.permission)
        perm.save()


class Migration(migrations.Migration):

    def postMigrate(apps, schema_editor):
        userPermModel = apps.get_model('html_browser', 'UserPermission')
        convertPerm(userPermModel)

        groupPermModel = apps.get_model('html_browser', 'GroupPermission')
        convertPerm(groupPermModel)

    dependencies = [
        ('html_browser', '0011_auto_20170404_2102'),
    ]

    operations = [
        migrations.RunPython(postMigrate),
    ]
