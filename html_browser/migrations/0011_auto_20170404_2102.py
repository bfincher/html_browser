# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-04-04 21:02
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('html_browser', '0010_folder_links'),
    ]

    operations = [
        migrations.AddField(
            model_name='grouppermission',
            name='p2',
            field=models.SmallIntegerField(choices=[(1, 'Read Only'), (2, 'Read/Write'), (3, 'Read/Write/Delete')], default=1),
        ),
        migrations.AddField(
            model_name='userpermission',
            name='p2',
            field=models.SmallIntegerField(choices=[(1, 'Read Only'), (2, 'Read/Write'), (3, 'Read/Write/Delete')], default=1),
        ),
    ]
