# Generated by Django 2.1.2 on 2018-11-26 18:48

from django.db import migrations


def face_features_to_own_model(apps, schema_editor):
    User = apps.get_model('api', 'User')
    FaceFeatures = apps.get_model('api', 'FaceFeatures')
    
    for user in User.objects.all():
        face_features = FaceFeatures.objects.create(user=user, face_features=user.face_features, face_recognition_implementer=user.face_recognition_implementer)
        face_features.save()

class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_facefeatures'),
    ]

    operations = [
      migrations.RunPython(face_features_to_own_model),
    ]