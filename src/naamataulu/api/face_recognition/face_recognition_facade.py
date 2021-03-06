import math
import time
import os
from multiprocessing import Pool, Array

from django.db import transaction
from django.core.paginator import Paginator

from .face_recognition_interface import FaceRecognitionInterface
from .face_recognition_template import FaceRecognitionTemplateImplementer
from .face_recognition_template import DlibFaceRecognition

from api.models import FaceFeatures
from api.environ import getEnvironmentVariable
import numpy as np

DEFAULT_IMPLEMENTER = getEnvironmentVariable(str, 'DEFAULT_IMPLEMENTER', 'dlib')
MAX_FEATURES_PER_USER = getEnvironmentVariable(int, 'MAX_FEATURES_PER_USER', 3)
MULTITHREAD = getEnvironmentVariable(bool, 'MULTITHREAD', False)
PROCESS_COUNT = getEnvironmentVariable(int, 'PROCESS_COUNT', 4)
MAX_RECOGNIZED_USERS = getEnvironmentVariable(int, 'MAX_RECOGNIZED_USERS', 3)

class FaceRecognitionFacade:
    def __init__(self):
        self.tolerance = 0.6

        # Implementers listed here
        recognition_implementers = {
            'template': FaceRecognitionTemplateImplementer,
			      'dlib': DlibFaceRecognition,
        }

        # Wrap implementers inside interface
        self.recognition_implementers = {}
        for key, implementer in recognition_implementers.items():
            self.recognition_implementers[key] = FaceRecognitionInterface(implementer)

    @transaction.atomic
    def add_new_features(self, user, face_features, implementer):
        if len(FaceFeatures.objects.filter(user=user)) >= MAX_FEATURES_PER_USER:
            user_features = FaceFeatures.objects.filter(user=user).order_by('-created')[MAX_FEATURES_PER_USER-1:]
            FaceFeatures.objects.filter(pk__in=list(user_features.values_list('id', flat=True))).delete()

        new_face_features = FaceFeatures.objects.create(user=user, face_features=face_features, face_recognition_implementer=implementer)
        new_face_features.save()     

    def enroll(self, faces, user, implementer):
        # Get features serialized to a string
        imp = self.recognition_implementers[implementer]
        features = imp.get_features(faces)

        # Write features and implementer to face features, delete old
        vector = np.array2string(features, separator=' ')

        self.add_new_features(user, vector, implementer)

    def get_distance_element(self, a):
        user_certainty_tuples = []
        users_list, features, key, implementer = a
        
        start = time.time()
        for user in users_list:
            distance = implementer.is_face(features, user.face_features)
            user_certainty_tuples.append((user.user, distance, features, key))

        return user_certainty_tuples

    # Returns Django user
    def recognize(self, face):
        
        user_certainty_tuples = []
        start = time.time()
        # Go through all implementers
        for key, implementer in self.recognition_implementers.items():
            # Filter users using given implementer
            users_with_implementer = list(FaceFeatures.objects.filter(face_recognition_implementer=key).all())
            # Get features of face to be recognized using implementer
            start_features = time.time()
            features = implementer.get_features(face)
            time_features = (time.time()-start_features)*1000

            # Get certainty that face is user's for all user using
            # the implementer
            start_distance = time.time()
            if not MULTITHREAD:
              for user in users_with_implementer:
                  distance = implementer.is_face(features, user.face_features)
                  user_certainty_tuples.append((user.user, distance, features, key))
            else:
              page_size = math.ceil(len(users_with_implementer)/PROCESS_COUNT)
              if page_size > 0:
                  # Split to pages
                  paginator = Paginator(users_with_implementer, page_size)
                  args = []
                  for page in paginator.page_range:
                      args.append((paginator.get_page(page), features, key, implementer))

                  # One page per process
                  with Pool(processes=PROCESS_COUNT) as pool:
                      results = pool.map(self.get_distance_element, args)
                      for result in results:
                          user_certainty_tuples.extend(result)

        # Filter matches to tolerance
        user_distance_tuples = list(filter(lambda x: x[1] <= self.tolerance, user_certainty_tuples))
        user_distance_tuples = sorted(user_distance_tuples, key= lambda tup: tup[1], reverse=False)

        # Filter matches to contain only one instance per user
        user_distance_tuples_temp = []
        added_user_ids = []
        for user_tuple in user_distance_tuples:
            if user_tuple[0].id not in added_user_ids:
                added_user_ids.append(user_tuple[0].id)
                user_distance_tuples_temp.append(user_tuple)

        # Cap the list length to specified maximum
        user_distance_tuples = user_distance_tuples_temp[:MAX_RECOGNIZED_USERS]

        print(list(map(lambda u: u[1], user_distance_tuples)))

        # Matches within tolerance
        matches = []
        for match_user, match_distance, face_features, implementer in user_distance_tuples:
            matches.append(match_user)
        
        if len(matches) > 0:
            return matches
        else:
            return None