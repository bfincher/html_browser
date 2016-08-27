# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('auth', '0006_require_contenttypes_0002'),
        ('html_browser', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Folder',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100)),
                ('localPath', models.CharField(unique=True, max_length=100)),
                ('viewOption', models.CharField(default=b'P', max_length=1, choices=[(b'P', b'View authorization set by user and group permissions'), (b'E', b'Viewable by any registered user'), (b'A', b'Viewable by anonymous users')])),
            ],
        ),
        migrations.CreateModel(
            name='GroupPermission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('permission', models.CharField(default=b'R', max_length=1, choices=[(b'R', b'Read Only'), (b'W', b'Read/Write'), (b'D', b'Read/Write/Delete')])),
                ('folder', models.ForeignKey(to='html_browser.Folder')),
                ('group', models.ForeignKey(to='auth.Group')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='UserPermission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('permission', models.CharField(default=b'R', max_length=1, choices=[(b'R', b'Read Only'), (b'W', b'Read/Write'), (b'D', b'Read/Write/Delete')])),
                ('folder', models.ForeignKey(to='html_browser.Folder')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
