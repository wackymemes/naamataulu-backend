# Generated by Django 2.1.2 on 2018-11-26 18:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_auto_20181125_2059'),
    ]

    operations = [
        migrations.CreateModel(
            name='FaceFeatures',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('face_features', models.TextField(blank=True, null=True)),
                ('face_recognition_implementer', models.CharField(blank=True, max_length=64, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.User')),
            ],
        ),
    ]
