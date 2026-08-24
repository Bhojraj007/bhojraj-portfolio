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
