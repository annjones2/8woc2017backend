# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-06-29 13:29
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_auto_20170628_2336'),
    ]

    operations = [
        migrations.CreateModel(
            name='Book',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(blank=True, max_length=3, unique=True)),
                ('name', models.CharField(blank=True, max_length=100)),
                ('booknum', models.IntegerField(default=0)),
            ],
        ),
        migrations.RemoveField(
            model_name='meta',
            name='take',
        ),
        migrations.RemoveField(
            model_name='language',
            name='lang',
        ),
        migrations.AddField(
            model_name='language',
            name='name',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='take',
            name='anthology',
            field=models.CharField(blank=True, max_length=2),
        ),
        migrations.AddField(
            model_name='take',
            name='chapter',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='take',
            name='endv',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='take',
            name='markers',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='take',
            name='mode',
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AddField(
            model_name='take',
            name='startv',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='take',
            name='version',
            field=models.CharField(blank=True, max_length=3),
        ),
        migrations.AlterField(
            model_name='language',
            name='code',
            field=models.CharField(blank=True, max_length=20, unique=True),
        ),
        migrations.DeleteModel(
            name='Meta',
        ),
        migrations.AddField(
            model_name='take',
            name='book',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='api.Book'),
        ),
    ]
