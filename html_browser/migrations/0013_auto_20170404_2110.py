# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-04-04 21:10
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('html_browser', '0012_custom_convert_perm_20170404'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='grouppermission',
            name='permission',
        ),
        migrations.RemoveField(
            model_name='userpermission',
            name='permission',
        ),
    ]