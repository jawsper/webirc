# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-07-05 08:41
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('webirc', '0010_enterexitevent_message'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='message',
            name='screen',
        ),
    ]
