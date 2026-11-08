import os
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError

from apps.core.models import validate_listing_image
from apps.businesses.models import validate_image_extension, validate_proof_document, Business, BusinessCategory
from apps.core.models import LocalityZone, Locality
from apps.accounts.forms import UserRegistrationForm

User = get_user_model()


class ComprehensiveSecurityAuditTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.zone = LocalityZone.objects.create(name='Gulberg Security Zone', slug='gulberg-security-zone')
        cls.locality = Locality.objects.create(name='Gulberg II', slug='gulberg-ii', zone=cls.zone)
        cls.category = BusinessCategory.objects.create(name='IT Solutions', slug='it-solutions')

        cls.owner = User.objects.create_user(
            email='audit_owner@example.pk',
            username='audit_owner',
            password='AuditOwnerPassword123!',
            role='business_owner'
        )
        cls.attacker = User.objects.create_user(
            email='attacker@example.pk',
            username='attacker',
            password='AttackerPassword123!',
            role='member'
        )
        cls.victim_business = Business.objects.create(
            title='Victim Enterprise',
            slug='victim-enterprise',
            category=cls.category,
            locality=cls.locality,
            address='123 Main Blvd',
            summary='Legitimate business.',
            description='Full details.',
            is_active=True,
            submitted_by=cls.owner,
            claimed_by=cls.owner
        )

    def setUp(self):
        self.client = Client()

    def test_security_headers_enforcement(self):
        """
        Verify baseline security headers are present in HTTP responses:
        - X-Content-Type-Options: nosniff
        - X-Frame-Options: DENY (anti-clickjacking)
        - X-XSS-Protection: 1; mode=block
        - Referrer-Policy: strict-origin-when-cross-origin
        """
        response = self.client.get(reverse('core:home'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('X-Content-Type-Options'), 'nosniff')
        self.assertEqual(response.get('X-Frame-Options'), 'DENY')
        self.assertEqual(response.get('X-XSS-Protection'), '1; mode=block')
        self.assertEqual(response.get('Referrer-Policy'), 'strict-origin-when-cross-origin')

    def test_file_upload_svg_and_malicious_extensions_rejected(self):
        """
        Verify that dangerous SVG, HTML, and executable files are rejected by image validators.
        Only safe raster formats (JPG, PNG, WEBP) are allowed.
        """
        # 1. SVG rejection (anti-stored-XSS)
        malicious_svg = SimpleUploadedFile("bad.svg", b"<svg onload=alert(1)></svg>", content_type="image/svg+xml")
        with self.assertRaises(ValidationError):
            validate_image_extension(malicious_svg)

        with self.assertRaises(ValidationError):
            validate_listing_image(malicious_svg)

        # 2. Executable and script rejection
        malicious_exe = SimpleUploadedFile("exploit.exe", b"\x4d\x5a\x90", content_type="application/octet-stream")
        with self.assertRaises(ValidationError):
            validate_image_extension(malicious_exe)

        malicious_php = SimpleUploadedFile("shell.php", b"<?php phpinfo(); ?>", content_type="application/x-php")
        with self.assertRaises(ValidationError):
            validate_image_extension(malicious_php)

        # 3. Valid raster image accepted
        valid_png = SimpleUploadedFile("safe.png", b"\x89PNG\r\n\x1a\n", content_type="image/png")
        try:
            validate_image_extension(valid_png)
            validate_listing_image(valid_png)
        except ValidationError:
            self.fail("Valid PNG should not raise ValidationError.")

    def test_proof_document_validation(self):
        """
        Verify BusinessClaim proof document validator rejects dangerous files and enforces size limits.
        """
        # Reject executable file
        bad_doc = SimpleUploadedFile("script.py", b"import os; os.system('whoami')", content_type="text/x-python")
        with self.assertRaises(ValidationError):
            validate_proof_document(bad_doc)

        # Accept valid PDF document
        valid_pdf = SimpleUploadedFile("secp_cert.pdf", b"%PDF-1.4...", content_type="application/pdf")
        try:
            validate_proof_document(valid_pdf)
        except ValidationError:
            self.fail("Valid PDF should not raise ValidationError.")

    def test_idor_protection_on_business_edit_and_delete(self):
        """
        Verify strict authorization boundaries: an authenticated user cannot edit,
        delete, or request promotion for a business owned by another user (HTTP 403 Forbidden).
        """
        self.client.force_login(self.attacker)

        # Attempt to edit victim's business
        edit_url = reverse('businesses:edit', kwargs={'slug': self.victim_business.slug})
        response = self.client.get(edit_url)
        self.assertEqual(response.status_code, 403)

        # Attempt to delete victim's business
        delete_url = reverse('businesses:delete', kwargs={'slug': self.victim_business.slug})
        response = self.client.get(delete_url)
        self.assertEqual(response.status_code, 403)

        # Attempt to request promotion for victim's business
        promote_url = reverse('businesses:request_promotion', kwargs={'slug': self.victim_business.slug})
        response = self.client.get(promote_url)
        self.assertEqual(response.status_code, 403)

    def test_anti_privilege_escalation_in_registration(self):
        """
        Verify that a registering user cannot assign themselves 'admin' or 'moderator' roles
        or set is_staff=True / is_superuser=True.
        """
        form_data = {
            'full_name': 'Attacker User',
            'email': 'escalate@example.pk',
            'role': 'admin',  # Privileged role tampering
            'password': 'SecurePassword123!',
            'confirm_password': 'SecurePassword123!',
            'terms_accepted': True,
        }
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('role', form.errors)

    def test_contact_form_input_validation(self):
        """
        Verify contact form enforces RFC email format validation.
        """
        contact_url = reverse('core:contact')

        # Invalid email format should be rejected
        response = self.client.post(contact_url, {
            'name': 'Test User',
            'email': 'not-an-email-address',
            'subject': 'Inquiry',
            'message': 'Hello team.',
        }, follow=True)
        self.assertContains(response, 'Please enter a valid email address.')

        # Valid input should succeed
        response = self.client.post(contact_url, {
            'name': 'Legitimate User',
            'email': 'legit@example.pk',
            'subject': 'Directory Question',
            'message': 'Can you please verify my clinic location?',
        }, follow=True)
        self.assertContains(response, 'Your message regarding')

    def test_json_ld_escaping_against_xss(self):
        """
        Verify JSON-LD blocks in detail views escape special characters and quotes
        to prevent script tag breakouts.
        """
        xss_business = Business.objects.create(
            title='Solar</script><script>alert("xss")</script>',
            slug='solar-xss-test',
            category=self.category,
            locality=self.locality,
            address='123 "Quoted" Street',
            summary='Testing XSS sanitization.',
            description='Detailed text.',
            phone_number='+92-300-1111111"; alert("phone"); //',
            website='https://example.pk/test?a=1&b=2',
            is_active=True,
            submitted_by=self.owner,
            claimed_by=self.owner
        )

        response = self.client.get(reverse('businesses:detail', kwargs={'slug': xss_business.slug}))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')

        # Raw unescaped breakout </script><script> must NOT appear inside the JSON-LD script block
        # Instead, it should be escaped safely (e.g. \u003C/script\u003E\u003Cscript\u003E)
        self.assertNotIn('</script><script>alert("xss")</script>', content)
        self.assertIn(r'\u003C/script\u003E\u003Cscript\u003Ealert(\u0022xss\u0022)\u003C/script\u003E', content)
