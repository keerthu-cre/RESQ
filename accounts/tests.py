from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from .models import CustomUser

class AuthAPITests(APITestCase):
    def test_user_registration(self):
        url = '/api/auth/register/'
        data = {
            'username': 'new_student',
            'email': 'student@campus.edu',
            'password': 'strongpassword123',
            'confirm_password': 'strongpassword123',
            'role': 'user',
            'phone': '+1-555-9988'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])

    def test_jwt_login(self):
        user = CustomUser.objects.create_user(
            username='test_user',
            password='testpassword',
            role='user'
        )
        url = '/api/auth/login/'
        response = self.client.post(url, {'username': 'test_user', 'password': 'testpassword'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['username'], 'test_user')
