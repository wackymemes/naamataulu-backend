import os
import glob
import time
from random import shuffle
from functools import reduce

from django.test import TestCase
from rest_framework.test import APIRequestFactory, APIClient, RequestsClient

from django.contrib.auth.models import User as DjangoUser
from rest_framework.authtoken.models import Token
from api.models import User
from api.views import UserViewSet

class UserTestCase(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

        admin = DjangoUser(username='admin', is_staff=True)
        admin.save()
        self.token = Token(user=admin)
        self.token.save()
        self.bad_token = 'asdf'
        
        self.faces = {}
        face_dir = os.path.join('api', 'tests', 'faces', 'att')

        for subject in os.listdir(face_dir):
          subject_dir = os.path.join(face_dir, subject)
          if os.path.isdir(subject_dir):
            self.faces[subject] = glob.glob(os.path.join(subject_dir, '*.jpg'))

        User.objects.create(username='Markku')

    def test_user_exists_list(self):
        request = self.factory.get('/api/v1/users', HTTP_AUTHORIZATION='Token {}'.format(self.token))
        view = UserViewSet.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.data[0]['username'], 'Markku')

    def test_user_exists(self):
        request = self.factory.get('/api/v1/users/1', HTTP_AUTHORIZATION='Token {}'.format(self.token))
        view = UserViewSet.as_view({'get': 'retrieve'})
        response = view(request, pk=1)
        self.assertEqual(response.data['username'], 'Markku')

    def test_user_enroll(self):
        # Enrol all users
        start = time.time()
        for subject, faces in self.faces.items():
          for i in range(1):
            user = User.objects.create(username=subject+"_"+str(i))
            user.save()
            with open(faces[0], 'rb') as data:
              request = self.factory.post('/api/v1/users/%d' % user.id, {'faces': data}, format='multipart', HTTP_AUTHORIZATION='Token {}'.format(self.token))
              view = UserViewSet.as_view({'post': 'enroll'})
              response = view(request, pk=user.id)
              self.assertEqual(response.status_code, 200)

        print('Enrolled %d users in %f seconds.' % (len(self.faces), time.time()-start))


        false_negatives = 0
        false_positives = 0
        hard_false_positives = 0
        successful = 0
        not_recognized = 0
        no_face = 0

        no_face_imgs = []
        not_recognized_imgs = []
        recognize_times = []

        for subject, faces in self.faces.items():
          user = User.objects.get(username=subject+"_0")
          for face in faces:
            start = time.time()
            with open(face, 'rb') as data:
              request = self.factory.post('/api/v1/users', {'faces': data}, format='multipart', HTTP_AUTHORIZATION='Token {}'.format(self.token))
              view = UserViewSet.as_view({'post': 'recognize'})
              try:
                  response = view(request)
                  if response.status_code == 200:
                      response_user_ids = list(map(lambda u: u['id'], response.data))
                      print(user.id, response_user_ids)
                      if user.id in response_user_ids:
                          successful += 1
                      else:
                          if len(response.data) > 1:
                            false_positives += 1
                          else:
                            hard_false_positives += 1
                  else:   
                      false_negatives += 1
                      not_recognized += 1
                      not_recognized_imgs.append(face)

              except IndexError:
                  false_negatives += 1
                  no_face += 1
                  no_face_imgs.append(face)
            print('Recognized in %s ms' % ((time.time()-start)*1000))
            recognize_times.append(time.time()-start)

        avg = reduce(lambda x, y: x + y, recognize_times) / len(recognize_times)

        print('False negatives: %s' % false_negatives)
        print('Hard false positives: %s' % hard_false_positives)
        print('False positives: %s' % false_positives)
        print('Successful: %s' % successful)
        print('Not recognized: %s, No faces detected: %s' % (not_recognized, no_face))

        print('Not recognized: %s' % not_recognized_imgs)
        print('No face: %s' % no_face_imgs)

        print('Average recognition time: %f ms' % (avg*1000))

    def test_unauthenticated_get_user_should_fail(self):
      request = self.factory.get('/api/v1/users', HTTP_AUTHORIZATION='Token {}'.format(self.bad_token))
      view = UserViewSet.as_view({'get': 'list'})
      response = view(request)
      self.assertEqual(response.status_code, 401)   

    def test_unauthenticated_enroll_user_should_fail(self):
      with open(self.faces['s1'][0], 'rb') as data:
        request = self.factory.post('/api/v1/users/1', {'faces': data}, format='multipart', HTTP_AUTHORIZATION='Token {}'.format(self.bad_token))
        view = UserViewSet.as_view({'post': 'enroll'})
        response = view(request, pk=1)
        self.assertEqual(response.status_code, 401)

    def test_unauthenticated_recognize_user_should_fail(self):
      with open(self.faces['s1'][0], 'rb') as data:
        request = self.factory.post('/api/v1/users', {'faces': data}, format='multipart', HTTP_AUTHORIZATION='Token {}'.format(self.bad_token))
        view = UserViewSet.as_view({'post': 'recognize'})
        response = view(request, pk=1)
        self.assertEqual(response.status_code, 401)    

    def test_put_last_and_first_name(self):
        request = self.factory.put('/api/v1/users/1', {'first_name': 'Markku', 'last_name': 'Virtanen'}, format='multipart', HTTP_AUTHORIZATION='Token {}'.format(self.token))
        view = UserViewSet.as_view({'put': 'partial_update'})
        response = view(request, pk=1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.get(pk=1).first_name, 'Markku')
        self.assertEqual(User.objects.get(pk=1).last_name, 'Virtanen')

    def test_multiple_features_on_single_user_returns_only_closest_feature(self):
        subject = 's1'
        faces = self.faces[subject]
        user = User.objects.create(username=subject)
        user.save()

        for face in faces:
            with open(face, 'rb') as data:
                request = self.factory.post('/api/v1/users/%d' % user.id, {'faces': data}, format='multipart', HTTP_AUTHORIZATION='Token {}'.format(self.token))
                view = UserViewSet.as_view({'post': 'enroll'})
                response = view(request, pk=user.id)
                self.assertEqual(response.status_code, 200)
            
            with open(face, 'rb') as data:
                request = self.factory.post('/api/v1/users', {'faces': data}, format='multipart', HTTP_AUTHORIZATION='Token {}'.format(self.token))
                view = UserViewSet.as_view({'post': 'recognize'})
                response = view(request)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(len(response.data), 1)
