from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

class UserModelTests(TestCase):
    def test_create_user(self):
        u = User.objects.create_user(username='test', email='t@t.com', password='p')
        self.assertEqual(u.username, 'test')
        self.assertTrue(u.check_password('p'))
        
        with self.assertRaises(ValueError):
            User.objects.create_user(username='', email='t@t.com')
        with self.assertRaises(ValueError):
            User.objects.create_user(username='test', email='')

    def test_create_superuser(self):
        u = User.objects.create_superuser(username='admin', email='a@a.com', password='p')
        self.assertTrue(u.is_staff)
        self.assertTrue(u.is_superuser)
        
        with self.assertRaises(ValueError):
            User.objects.create_superuser(username='a', email='a@a.com', password='p', is_staff=False)

class UserViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='u', email='u@u.com', password='p')
        self.client = Client()

    def test_login_view(self):
        resp = self.client.get(reverse('users:login'))
        self.assertEqual(resp.status_code, 200)
        
        # Invalid
        resp = self.client.post(reverse('users:login'), {'username': 'u', 'password': 'wrong'})
        self.assertEqual(resp.status_code, 200)
        # Check messages in context instead of HTML content, as template might not render them in test environment
        messages = list(resp.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Invalid username or password.")
        
        # Valid
        resp = self.client.post(reverse('users:login'), {'username': 'u', 'password': 'p'})
        self.assertRedirects(resp, reverse('core:homepage'))

    def test_logout_view(self):
        self.client.login(username='u', password='p')
        resp = self.client.get(reverse('users:logout'))
        self.assertRedirects(resp, reverse('users:login'))

    def test_profile_view(self):
        self.client.login(username='u', password='p')
        resp = self.client.get(reverse('users:profile'))
        self.assertEqual(resp.status_code, 200)

    def test_edit_profile_view(self):
        self.client.login(username='u', password='p')
        resp = self.client.get(reverse('users:edit_profile'))
        self.assertEqual(resp.status_code, 200)
        
        resp = self.client.post(reverse('users:edit_profile'), {'imgurl': 'http://example.com/img.jpg'})
        self.assertRedirects(resp, reverse('users:profile'))
        self.user.refresh_from_db()
        self.assertEqual(self.user.imgurl, 'http://example.com/img.jpg')
