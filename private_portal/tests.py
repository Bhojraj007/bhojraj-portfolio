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

    def test_inquiry_list_edit_and_delete(self):
        from public_portal.models import ContactMessage
        
        staff_user = User.objects.create_user(username='staffuser', password='staffpassword', is_staff=True)
        self.client.login(username='staffuser', password='staffpassword')

        inquiry1 = ContactMessage.objects.create(
            name='Nepal Bank Ltd',
            email='it@nbl.com.np',
            phone='+977 9801234567',
            inquiry_type='IbiSAP Enterprise Demo',
            message='Need a banking ERP demonstration.'
        )
        inquiry2 = ContactMessage.objects.create(
            name='Literary Reader',
            email='reader@poem.np',
            inquiry_type='Poetry Inquiry',
            message='Inquiring about your published collection.'
        )

        # List view with tabs
        list_url = reverse('private_portal:sm_inquiry_list')
        resp = self.client.get(list_url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Nepal Bank Ltd')
        self.assertContains(resp, 'Literary Reader')

        # Filter by demos tab
        resp_demos = self.client.get(list_url + '?tab=demos')
        self.assertEqual(resp_demos.status_code, 200)
        self.assertContains(resp_demos, 'Nepal Bank Ltd')
        self.assertNotContains(resp_demos, 'Literary Reader')

        # Edit view (GET and POST)
        edit_url = reverse('private_portal:sm_inquiry_edit', kwargs={'pk': inquiry1.pk})
        resp_edit_get = self.client.get(edit_url)
        self.assertEqual(resp_edit_get.status_code, 200)

        resp_edit_post = self.client.post(edit_url, {
            'name': 'Nepal Bank Ltd (Updated)',
            'email': 'cto@nbl.com.np',
            'phone': '+977 9809998888',
            'inquiry_type': 'IbiSAP Enterprise Demo',
            'message': 'Updated urgent enterprise request.'
        }, follow=True)
        self.assertEqual(resp_edit_post.status_code, 200)
        inquiry1.refresh_from_db()
        self.assertEqual(inquiry1.name, 'Nepal Bank Ltd (Updated)')
        self.assertEqual(inquiry1.email, 'cto@nbl.com.np')

        # Delete view (GET and POST)
        del_url = reverse('private_portal:sm_inquiry_delete', kwargs={'pk': inquiry2.pk})
        resp_del_get = self.client.get(del_url)
        self.assertEqual(resp_del_get.status_code, 200)

        resp_del_post = self.client.post(del_url, follow=True)
        self.assertEqual(resp_del_post.status_code, 200)
        self.assertFalse(ContactMessage.objects.filter(pk=inquiry2.pk).exists())

