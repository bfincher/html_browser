# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2016-10-23 01:17


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('html_browser', '0006_auto_20161022_1644'),
    ]

    operations = [
        migrations.CreateModel(
            name='FilesToDelete',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('filePath', models.CharField(max_length=250)),
                ('time', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]