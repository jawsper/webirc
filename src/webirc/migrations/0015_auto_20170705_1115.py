# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-07-05 11:15
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webirc', '0014_auto_20170705_0930'),
    ]

    operations = [
        migrations.AddField(
            model_name='enterexitevent',
            name='reason',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AlterField(
            model_name='enterexitevent',
            name='source',
            field=models.CharField(default='', max_length=100),
        ),
        migrations.AlterField(
            model_name='enterexitevent',
            name='target',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AlterField(
            model_name='enterexitevent',
            name='type',
            field=models.IntegerField(choices=[(0, 'Unknown'), (1, 'Join'), (2, 'Part'), (3, 'Kick')], default=0),
        ),
    ]