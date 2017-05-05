# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-05-04 12:33
from __future__ import unicode_literals

import datetime
from django.conf import settings
import django.contrib.auth.models
from django.db import migrations, models
import django.db.models.deletion
from django.utils.timezone import utc


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0008_alter_user_username_max_length'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Attachment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uploaded_file', models.FileField(upload_to='uploads/')),
                ('title', models.CharField(max_length=100)),
                ('create_time', models.DateTimeField(verbose_name='Date Created')),
            ],
        ),
        migrations.CreateModel(
            name='ContentVersion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('object_id', models.PositiveIntegerField()),
                ('text', models.TextField()),
                ('release_note', models.CharField(blank=True, max_length=255)),
                ('released', models.BooleanField(default=False)),
                ('create_time', models.DateTimeField(default=datetime.datetime(2017, 5, 4, 12, 33, 23, 165589, tzinfo=utc))),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType')),
            ],
        ),
        migrations.CreateModel(
            name='Contest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('order', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Country',
            fields=[
                ('name', models.CharField(max_length=255, primary_key=True, serialize=False)),
                ('code', models.CharField(default='', max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='FlatPage',
            fields=[
                ('slug', models.CharField(max_length=100, primary_key=True, serialize=False)),
                ('content', models.TextField(default=None)),
            ],
        ),
        migrations.CreateModel(
            name='Language',
            fields=[
                ('name', models.CharField(max_length=255, primary_key=True, serialize=False)),
                ('code', models.CharField(default='', max_length=255)),
                ('rtl', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=50)),
                ('description', models.CharField(max_length=300)),
                ('create_time', models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('enabled', models.BooleanField(default=False)),
                ('uploaded_file', models.FileField(upload_to='uploads/')),
                ('contest', models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='interp.Contest')),
            ],
        ),
        migrations.CreateModel(
            name='Translation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('freezed', models.BooleanField(default=False)),
                ('task', models.ForeignKey(default=0, on_delete=django.db.models.deletion.CASCADE, to='interp.Task')),
            ],
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('user_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('text_font_base64', models.TextField(default='')),
                ('digit_font_base64', models.TextField(default='')),
                ('raw_password', models.CharField(default='', max_length=255)),
                ('country', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='interp.Country')),
                ('language', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='interp.Language')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
            bases=('auth.user',),
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='VersionParticle',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField(default=None)),
                ('create_time', models.DateTimeField(default=datetime.datetime(2017, 5, 4, 12, 33, 23, 169294, tzinfo=utc))),
                ('translation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='interp.Translation')),
            ],
        ),
        migrations.AddField(
            model_name='translation',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='interp.User'),
        ),
    ]