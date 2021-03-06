# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-07-05 08:41
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('webirc', '0009_auto_20170705_0840'),
    ]

    operations = [
        migrations.CreateModel(
            name='EnterExitEvent',
            fields=[
                ('type', models.IntegerField(choices=[(0, 'Unknown'), (1, 'Join'), (2, 'Leave'), (3, 'Kick')], default=0)),
                ('event', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='webirc.Event')),
            ],
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('event', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='webirc.Event')),
                ('sender', models.CharField(max_length=100)),
                ('moment', models.DateTimeField()),
                ('text', models.TextField()),
                ('screen', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='webirc.Screen')),
            ],
        ),
    ]
