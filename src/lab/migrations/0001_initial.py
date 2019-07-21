# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2018-10-25 02:39
from __future__ import unicode_literals

from django.db import migrations, models
import lab.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Lab',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=15)),
                ('title', models.CharField(max_length=50)),
                ('synopsis', models.TextField(default='')),
                ('document', models.FileField(upload_to=lab.models.user_directory_path)),
            ],
        ),
    ]
