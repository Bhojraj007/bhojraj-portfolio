from django.test import TestCase, Client, override_settings
from django.urls import reverse
from .models import Skill, Experience, Education, Project, ContactMessage, IbiSAPModule, SiteConfiguration

@override_settings(SECURE_SSL_REDIRECT=False)
class PublicPortalTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        Skill.objects.create(name='SAP Business One', category='ERP & Business Systems')
        Experience.objects.create(role='IT Officer', company='National Laghubitta', date_range='2025-Present', description='CBS Operations')
        IbiSAPModule.objects.create(title='Nepali Miti Engine', badge='Core', description='Bikram Sambat')

    def test_home_page_renders_successfully(self):
        response = self.client.get(reverse('public_portal:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Rajabhoj')
        self.assertContains(response, 'IbiSAP')

    def test_ibisap_dedicated_page_renders(self):
        response = self.client.get(reverse('public_portal:ibisap'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Enterprise IbiSAP')
        self.assertContains(response, 'Retail IbiSAP')
        self.assertContains(response, 'Comparison Matrix')
        self.assertContains(response, 'Nepali Miti Engine')

    def test_contact_form_submission(self):
        data = {
            'name': 'Test Client',
            'email': 'client@example.com',
            'inquiry_type': 'Enterprise IbiSAP Implementation',
            'message': 'We need an ERP for our microfinance institution.'
        }
        response = self.client.post(reverse('public_portal:home'), data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ContactMessage.objects.count(), 1)
        msg = ContactMessage.objects.first()
        self.assertEqual(msg.name, 'Test Client')
        self.assertIn('Enterprise IbiSAP Implementation', msg.inquiry_type)

    def test_ibisap_demo_request_submission(self):
        data = {
            'name': 'MFI Manager',
            'email': 'mfi@example.com.np',
            'inquiry_type': 'Enterprise IbiSAP Implementation',
            'message': 'We want an on-premises demo for 20 branches.'
        }
        response = self.client.post(reverse('public_portal:ibisap'), data, follow=True)
        self.assertEqual(response.status_code, 200)
        msg = ContactMessage.objects.filter(email='mfi@example.com.np').first()
        self.assertIsNotNone(msg)
        self.assertEqual(msg.name, 'MFI Manager')

    def test_gallery_page_renders(self):
        response = self.client.get(reverse('public_portal:gallery'))
        self.assertEqual(response.status_code, 200)

    def test_blog_detail_and_comment_submission(self):
        from private_portal.models import Blog, Comment
        from django.contrib.contenttypes.models import ContentType

        blog = Blog.objects.create(
            title='The Poetry of Code',
            category='poem',
            content='Lines of logic woven in the night...',
            is_public=True
        )

        # Detail page renders with comment section
        detail_url = reverse('public_portal:blog_detail', kwargs={'slug': blog.slug})
        resp = self.client.get(detail_url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Reflections &amp; Discourse')

        # Submit comment as guest via POST
        post_url = reverse('public_portal:add_public_comment')
        comment_data = {
            'content_type': 'blog',
            'object_id': blog.id,
            'author_name': 'Suman Adhikari',
            'author_email': 'suman@example.com',
            'text': 'Beautiful resonance between systems engineering and lyrical verses.'
        }
        post_resp = self.client.post(post_url, comment_data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(post_resp.status_code, 200)
        json_data = post_resp.json()
        self.assertEqual(json_data['status'], 'ok')
        self.assertEqual(json_data['comments_count'], 1)

        # Verify in DB
        blog_ct = ContentType.objects.get_for_model(Blog)
        c = Comment.objects.filter(content_type=blog_ct, object_id=blog.id).first()
        self.assertIsNotNone(c)
        self.assertEqual(c.display_author, 'Suman Adhikari')
        self.assertEqual(c.author_email, 'suman@example.com')

        # Test AJAX fetch
        list_url = reverse('public_portal:get_comments_ajax', kwargs={'content_type': 'blog', 'object_id': blog.id})
        list_resp = self.client.get(list_url)
        self.assertEqual(list_resp.status_code, 200)
        self.assertEqual(list_resp.json()['count'], 1)

    def test_image_comment_ajax(self):
        from private_portal.models import Photo, Comment
        from django.contrib.contenttypes.models import ContentType

        photo = Photo.objects.create(title='Nepal Mountains', is_public=True)

        post_url = reverse('public_portal:add_public_comment')
        resp = self.client.post(post_url, {
            'content_type': 'photo',
            'object_id': photo.id,
            'author_name': 'Himalayan Explorer',
            'text': 'Spectacular framing and lighting!'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['status'], 'ok')

        photo_ct = ContentType.objects.get_for_model(Photo)
        self.assertEqual(Comment.objects.filter(content_type=photo_ct, object_id=photo.id).count(), 1)

    def test_anonymous_get_does_not_create_sessionid_cookie(self):
        resp = self.client.get(reverse('public_portal:home'))
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn('sessionid', resp.cookies)
        self.assertIn('csrftoken', resp.cookies)

    def test_security_headers_present(self):
        resp = self.client.get(reverse('public_portal:home'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('Permissions-Policy', resp.headers)
        self.assertEqual(resp.headers['Permissions-Policy'], 'camera=(), microphone=(), geolocation=()')
        self.assertIn('Content-Security-Policy-Report-Only', resp.headers)
        self.assertIn("default-src 'self'", resp.headers['Content-Security-Policy-Report-Only'])
        self.assertIn("fonts.googleapis.com", resp.headers['Content-Security-Policy-Report-Only'])
        self.assertIn("cdnjs.cloudflare.com", resp.headers['Content-Security-Policy-Report-Only'])
        self.assertEqual(resp.headers.get('X-Content-Type-Options'), 'nosniff')

    @override_settings(DEBUG=False, SECURE_SSL_REDIRECT=True, SECURE_HSTS_SECONDS=63072000, SECURE_HSTS_INCLUDE_SUBDOMAINS=True, SECURE_HSTS_PRELOAD=True, SESSION_COOKIE_SECURE=True, CSRF_COOKIE_SECURE=True)
    def test_production_ssl_and_hsts(self):
        # Unsecure HTTP redirect
        resp_http = self.client.get(reverse('public_portal:home'), secure=False, HTTP_HOST='rajabhoj.com.np')
        self.assertEqual(resp_http.status_code, 301)
        self.assertTrue(resp_http['Location'].startswith('https://'))

        # Secure HTTPS request
        resp_https = self.client.get(reverse('public_portal:home'), secure=True, HTTP_HOST='rajabhoj.com.np', HTTP_X_FORWARDED_PROTO='https')
        self.assertEqual(resp_https.status_code, 200)
        self.assertEqual(resp_https.headers.get('Strict-Transport-Security'), 'max-age=63072000; includeSubDomains; preload')
        self.assertTrue(resp_https.cookies['csrftoken']['secure'])

