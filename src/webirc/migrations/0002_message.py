# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-07-01 00:24
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('webirc', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sender', models.CharField(max_length=100)),
                ('moment', models.DateTimeField()),
                ('text', models.TextField()),
                ('screen', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='webirc.Screen')),
            ],
        ),
    ]
