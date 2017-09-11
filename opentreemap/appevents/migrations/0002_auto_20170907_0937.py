# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-09-07 14:37
from __future__ import unicode_literals

from django.db import migrations
import treemap.DotDict
import treemap.json_field


class Migration(migrations.Migration):

    dependencies = [
        ('appevents', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='appevent',
            name='data',
            field=treemap.json_field.JSONField(blank=True, default=treemap.DotDict.DotDict),
        ),
    ]
