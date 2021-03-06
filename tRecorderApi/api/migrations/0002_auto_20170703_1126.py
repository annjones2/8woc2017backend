# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-07-03 15:26
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='book',
            options={'ordering': ['booknum']},
        ),
        migrations.AlterModelOptions(
            name='language',
            options={'ordering': ['name']},
        ),
        migrations.AlterModelOptions(
            name='take',
            options={'ordering': ['chapter', 'startv']},
        ),
        migrations.AlterModelOptions(
            name='user',
            options={'ordering': ['name']},
        ),
    ]
