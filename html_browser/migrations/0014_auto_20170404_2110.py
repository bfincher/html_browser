# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-04-04 21:10
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('html_browser', '0013_auto_20170404_2110'),
    ]

    operations = [
        migrations.RenameField(
            model_name='grouppermission',
            old_name='p2',
            new_name='permission',
        ),
        migrations.RenameField(
            model_name='userpermission',
            old_name='p2',
            new_name='permission',
        ),
    ]