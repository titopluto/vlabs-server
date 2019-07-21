# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2018-10-25 02:39
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('course', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Cohort',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=10)),
                ('courses', models.ManyToManyField(blank=True, to='course.Course')),
            ],
        ),
    ]
