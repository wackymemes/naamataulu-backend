# Generated by Django 2.1.2 on 2018-11-26 19:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_auto_20181126_1848'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='face_features',
        ),
        migrations.RemoveField(
            model_name='user',
            name='face_recognition_implementer',
        ),
    ]
