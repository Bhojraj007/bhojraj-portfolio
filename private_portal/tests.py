from django.test import TestCase, Client, override_settings
from django.urls import reverse
from accounts.models import User
from private_portal.models import Photo

@override_settings(SECURE_SSL_REDIRECT=False)
class PrivatePortalTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.photo = Photo.objects.create(title='Test Photo', description='Test Description')
        
    def test_public_views(self):
        # Public views should be accessible to anyone
        response = self.client.get(reverse('public_portal:home'))
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get(reverse('public_portal:gallery'))
        self.assertEqual(response.status_code, 200)

    def test_private_views_unauthenticated(self):
        # Private views should redirect to login if unauthenticated
        response = self.client.get(reverse('private_portal:dashboard'))
        self.assertRedirects(response, f"/accounts/login/?next=/private/")

        response = self.client.get(reverse('private_portal:photo_list'))
        self.assertRedirects(response, f"/accounts/login/?next=/private/photos/")

    def test_private_views_authenticated(self):
        # Private views should be accessible if authenticated
        self.client.login(username='testuser', password='testpassword')
        
        response = self.client.get(reverse('private_portal:dashboard'))
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get(reverse('private_portal:photo_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Photo')

    def test_model_str(self):
        self.assertEqual(str(self.photo), 'Test Photo')
