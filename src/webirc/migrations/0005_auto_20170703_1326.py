# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-07-03 13:26
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('webirc', '0004_remove_ircserver_ipv6'),
    ]

    operations = [
        migrations.DeleteModel(
            name='IRCScreen',
        ),
        migrations.AlterModelOptions(
            name='ircserver',
            options={'verbose_name': 'IRC server'},
        ),
    ]
