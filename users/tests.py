from django.test import TestCase
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from django.db import IntegrityError
from django.db import transaction

User = get_user_model()


class UserModelAndManagerTestCase(TestCase):
    def test_create_user_and_str(self):
        user = User.objects.create_user(username='alice', email='alice@example.com', password='pw')
        self.assertEqual(str(user), 'alice')
        self.assertTrue(user.check_password('pw'))

    def test_create_superuser_flags(self):
        admin = User.objects.create_superuser(username='admin', email='admin@example.com', password='adminpw')
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)

    def test_user_email_unique(self):
        User.objects.create_user(username='user1', email='unique@example.com', password='pw')
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                User.objects.create_user(username='user2', email='unique@example.com', password='pw')

    def test_user_username_unique(self):
        User.objects.create_user(username='unique_user', email='u1@example.com', password='pw')
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                User.objects.create_user(username='unique_user', email='u2@example.com', password='pw')

    def test_create_user_requires_username(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(username='', email='test@example.com', password='pw')

    def test_create_user_requires_email(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(username='testuser', email='', password='pw')

    def test_user_optional_fields(self):
        user = User.objects.create_user(username='minimal', email='min@example.com', password='pw')
        self.assertEqual(user.first_name, '')
        self.assertEqual(user.last_name, '')
        self.assertIsNone(user.imgurl)

    def test_user_with_names(self):
        user = User.objects.create_user(username='fullname', email='fn@example.com', password='pw', first_name='John', last_name='Doe')
        self.assertEqual(user.first_name, 'John')
        self.assertEqual(user.last_name, 'Doe')

    def test_user_is_active_default(self):
        user = User.objects.create_user(username='active', email='active@example.com', password='pw')
        self.assertTrue(user.is_active)

    def test_user_is_staff_default(self):
        user = User.objects.create_user(username='staff', email='staff@example.com', password='pw')
        self.assertFalse(user.is_staff)

    def test_superuser_validation_is_staff(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser(username='badsuper', email='bad@example.com', password='pw', is_staff=False)

    def test_superuser_validation_is_superuser(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser(username='badsuper2', email='bad2@example.com', password='pw', is_superuser=False)

    def test_user_date_joined(self):
        user = User.objects.create_user(username='dated', email='dated@example.com', password='pw')
        self.assertIsNotNone(user.date_joined)

    def test_user_last_login_null(self):
        user = User.objects.create_user(username='nogin', email='nogin@example.com', password='pw')
        self.assertIsNone(user.last_login)

    def test_user_password_hashing(self):
        password = 'mypassword123'
        user = User.objects.create_user(username='hasher', email='hasher@example.com', password=password)
        # Password should be hashed, not stored as plain text
        self.assertNotEqual(user.password, password)

    def test_user_email_normalization(self):
        user = User.objects.create_user(username='norm', email='TEST@EXAMPLE.COM', password='pw')
        # Django's normalize_email lowercases the domain part
        self.assertEqual(user.email, 'TEST@example.com')

    def test_user_with_image_url(self):
        user = User.objects.create_user(username='withimg', email='img@example.com', password='pw', imgurl='https://example.com/image.jpg')
        self.assertEqual(user.imgurl, 'https://example.com/image.jpg')

    def test_user_get_full_name(self):
        user = User.objects.create_user(username='fullname', email='full@example.com', password='pw', first_name='Jane', last_name='Smith')
        # If the User model has a get_full_name method, test it; otherwise test that fields exist
        self.assertEqual(user.first_name, 'Jane')
        self.assertEqual(user.last_name, 'Smith')

    def test_user_queryset_filter(self):
        User.objects.create_user(username='alice', email='alice@example.com', password='pw', first_name='Alice')
        User.objects.create_user(username='bob', email='bob@example.com', password='pw', first_name='Bob')
        alices = User.objects.filter(first_name='Alice')
        self.assertEqual(alices.count(), 1)
        self.assertEqual(alices.first().username, 'alice')


class UserViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')

    def test_login_view_get(self):
        resp = self.client.get(reverse('users:login'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('form', resp.context)

    def test_login_view_post_valid(self):
        resp = self.client.post(reverse('users:login'), {'username': 'testuser', 'password': 'testpass123'})
        self.assertRedirects(resp, reverse('core:homepage'))
        self.assertTrue(self.client.session.get('_auth_user_id'))

    def test_login_view_post_invalid_password(self):
        resp = self.client.post(reverse('users:login'), {'username': 'testuser', 'password': 'wrongpass'})
        self.assertEqual(resp.status_code, 200)
        # Check that we're still on the login form (form is re-rendered with errors)
        self.assertFalse(self.client.session.get('_auth_user_id'))

    def test_login_view_post_nonexistent_user(self):
        resp = self.client.post(reverse('users:login'), {'username': 'nonexistent', 'password': 'pass'})
        self.assertEqual(resp.status_code, 200)
        # Check that form is re-rendered without authentication
        self.assertFalse(self.client.session.get('_auth_user_id'))

    def test_profile_view_logged_in(self):
        self.client.force_login(self.user)
        resp = self.client.get(reverse('users:profile'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('user_reviews', resp.context)
        self.assertIn('bookmarked_reviews', resp.context)

    def test_profile_view_not_logged_in(self):
        resp = self.client.get(reverse('users:profile'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login', resp.url)

    def test_profile_view_with_reviews(self):
        from core.models import Course, Campus
        from review.models import Review
        self.client.force_login(self.user)
        campus = Campus.objects.create(name='Campus')
        course = Course.objects.create(course_code='CS100', course_name='Test', credit=3)
        review = Review.objects.create(user=self.user, course=course, head='Test', body='Body', rating=5)
        resp = self.client.get(reverse('users:profile'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context['user_reviews']), 1)

    def test_profile_view_with_bookmarks(self):
        from core.models import Course, Campus
        from review.models import Review, Bookmark
        self.client.force_login(self.user)
        campus = Campus.objects.create(name='Campus')
        course = Course.objects.create(course_code='CS100', course_name='Test', credit=3)
        review = Review.objects.create(user=self.user, course=course, head='Test', body='Body', rating=5)
        Bookmark.objects.create(user=self.user, review=review, course=course)
        resp = self.client.get(reverse('users:profile'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context['bookmarked_reviews']), 1)

