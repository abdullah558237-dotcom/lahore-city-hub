from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core import mail
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse

from apps.core.models import LocalityZone, Locality
from apps.businesses.models import BusinessCategory, Business, BusinessEditRequest, BusinessClaim
from apps.accounts.decorators import role_required, business_owner_required, moderator_required

User = get_user_model()


class AuthenticationAndSecurityTests(TestCase):
    """
    Comprehensive test suite for Lahore City Hub User Authentication & Security:
    1. Registration (member, business owner, anti-privilege escalation, validation)
    2. Login & Session Management (email, username, invalid credentials, open redirect defense)
    3. Logout (session invalidation)
    4. Password Change (authenticated user, session preservation)
    5. Password Reset Workflow (anti-enumeration, cryptographic token, new password confirmation)
    6. User Profile (own profile editing, file upload safety, privacy protection)
    7. Role-Based Permissions (role_required decorator, 403 Forbidden enforcement)
    8. Business Owner Dashboard & Content Submission Status (isolation, statuses, private URL protection)
    """

    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()

        # Regular Member User
        self.member_password = 'MemberPass123!'
        self.member = User.objects.create_user(
            email='member@lahorecityhub.pk',
            username='lahore_member',
            password=self.member_password,
            first_name='Zain',
            last_name='Ali',
            role='member'
        )

        # Business Owner User
        self.owner_password = 'OwnerPass123!'
        self.owner = User.objects.create_user(
            email='owner@lahorecityhub.pk',
            username='lahore_owner',
            password=self.owner_password,
            first_name='Bilal',
            last_name='Hassan',
            role='business_owner'
        )

        # Another Business Owner User (for isolation testing)
        self.other_owner = User.objects.create_user(
            email='other_owner@lahorecityhub.pk',
            username='other_owner',
            password='OtherPass123!',
            first_name='Hamza',
            last_name='Tariq',
            role='business_owner'
        )

        # Moderator User
        self.moderator = User.objects.create_user(
            email='moderator@lahorecityhub.pk',
            username='city_moderator',
            password='ModPass123!',
            role='moderator'
        )

        # Administrator / Superuser
        self.admin = User.objects.create_superuser(
            email='admin@lahorecityhub.pk',
            username='super_admin',
            password='AdminPass123!'
        )

        # Geography & Categories for Business submissions
        self.zone = LocalityZone.objects.create(name='Gulberg Zone', slug='gulberg-zone')
        self.locality = Locality.objects.create(name='Gulberg III', slug='gulberg-iii', zone=self.zone)
        self.category = BusinessCategory.objects.create(name='Software & Technology', slug='software-tech')

        # Business submission belonging to self.owner (Published)
        self.business_published = Business.objects.create(
            title='Apex Cloud Solutions',
            slug='apex-cloud-solutions',
            category=self.category,
            locality=self.locality,
            address='Suite 401, Siddiq Trade Centre, Gulberg III',
            summary='Cloud computing and managed services.',
            description='Enterprise cloud computing provider in Lahore.',
            submitted_by=self.owner,
            is_active=True,
            verification_status='verified'
        )

        # Business submission belonging to self.owner (Pending approval)
        self.business_pending = Business.objects.create(
            title='TechHub Coworking Lahore',
            slug='techhub-coworking-lahore',
            category=self.category,
            locality=self.locality,
            address='Main Boulevard, Gulberg III',
            summary='Modern flexible workspace.',
            description='Coworking space for freelancers and startups.',
            submitted_by=self.owner,
            is_active=False,
            verification_status='pending'
        )

        # Business submission belonging to self.other_owner (Private / Pending)
        self.other_business = Business.objects.create(
            title='Secret Startup Labs',
            slug='secret-startup-labs',
            category=self.category,
            locality=self.locality,
            address='Plaza 5, MM Alam Road',
            summary='Private incubator.',
            description='Underground stealth lab.',
            submitted_by=self.other_owner,
            is_active=False,
            verification_status='unverified'
        )

    # ==========================================================
    # 1. Registration & Privilege Escalation Defense Tests
    # ==========================================================

    def test_registration_page_loads_with_form(self):
        """Registration view renders HTTP 200 with required form fields."""
        response = self.client.get(reverse('accounts:register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Join the Lahore Community')
        self.assertContains(response, 'csrfmiddlewaretoken')

    def test_registration_successful_as_member(self):
        """Valid registration creates CustomUser with role='member' and auto-signs in."""
        data = {
            'full_name': 'Fatima Zahra',
            'email': 'fatima@example.pk',
            'phone_number': '+92 300 7654321',
            'home_locality': 'DHA Phase 5',
            'role': 'member',
            'password': 'SecurePass2026!',
            'confirm_password': 'SecurePass2026!',
            'terms_accepted': 'on',
        }
        response = self.client.post(reverse('accounts:register'), data)
        self.assertRedirects(response, reverse('accounts:dashboard'))

        # Verify user record in database
        new_user = User.objects.get(email='fatima@example.pk')
        self.assertEqual(new_user.first_name, 'Fatima')
        self.assertEqual(new_user.last_name, 'Zahra')
        self.assertEqual(new_user.role, 'member')
        self.assertFalse(new_user.is_staff)
        self.assertFalse(new_user.is_superuser)
        self.assertTrue(new_user.is_active)
        # Profile check
        self.assertEqual(new_user.profile.home_locality, 'DHA Phase 5')

    def test_registration_successful_as_business_owner(self):
        """User can explicitly register as a business owner."""
        data = {
            'full_name': 'Khurram Shehzad',
            'email': 'khurram@business.pk',
            'role': 'business_owner',
            'password': 'OwnerSecurePass2026!',
            'confirm_password': 'OwnerSecurePass2026!',
            'terms_accepted': 'on',
        }
        response = self.client.post(reverse('accounts:register'), data)
        self.assertRedirects(response, reverse('accounts:dashboard'))

        new_user = User.objects.get(email='khurram@business.pk')
        self.assertEqual(new_user.role, 'business_owner')
        self.assertFalse(new_user.is_staff)
        self.assertFalse(new_user.is_superuser)

    def test_registration_privilege_escalation_denied(self):
        """Users CANNOT grant themselves 'admin' or 'moderator' roles via registration form."""
        data_admin_attempt = {
            'full_name': 'Hacker Admin Attempt',
            'email': 'hacker@example.pk',
            'role': 'admin',  # Privileged role tampering
            'is_staff': True,  # Field injection
            'is_superuser': True,
            'password': 'HackerPassword123!',
            'confirm_password': 'HackerPassword123!',
            'terms_accepted': 'on',
        }
        response = self.client.post(reverse('accounts:register'), data_admin_attempt)
        # Form validation must fail and reject the request
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email='hacker@example.pk').exists())

    def test_registration_duplicate_email_rejected(self):
        """Registration rejects already existing email addresses case-insensitively."""
        data = {
            'full_name': 'Duplicate Member',
            'email': 'MEMBER@lahorecityhub.pk',  # already exists in setUp
            'role': 'member',
            'password': 'SamplePass123!',
            'confirm_password': 'SamplePass123!',
            'terms_accepted': 'on',
        }
        response = self.client.post(reverse('accounts:register'), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'already registered')

    def test_registration_password_mismatch_rejected(self):
        """Mismatched password confirmation fields raise an error."""
        data = {
            'full_name': 'Mismatch Test',
            'email': 'mismatch@example.pk',
            'role': 'member',
            'password': 'Password123!',
            'confirm_password': 'DifferentPassword123!',
            'terms_accepted': 'on',
        }
        response = self.client.post(reverse('accounts:register'), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'did not match')

    def test_registration_missing_terms_rejected(self):
        """Registration without accepting terms is rejected."""
        data = {
            'full_name': 'No Terms Test',
            'email': 'noterms@example.pk',
            'role': 'member',
            'password': 'Password123!',
            'confirm_password': 'Password123!',
            # terms_accepted omitted
        }
        response = self.client.post(reverse('accounts:register'), data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email='noterms@example.pk').exists())

    # ==========================================================
    # 2. Login & Session Security Tests
    # ==========================================================

    def test_login_page_renders_with_csrf(self):
        """Login page returns 200 and renders CSRF token and form."""
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sign In to Lahore City Hub')
        self.assertContains(response, 'csrfmiddlewaretoken')

    def test_login_with_email_success(self):
        """Users can authenticate using their registered email address."""
        response = self.client.post(reverse('accounts:login'), {
            'username_or_email': 'member@lahorecityhub.pk',
            'password': self.member_password,
        })
        self.assertRedirects(response, reverse('accounts:dashboard'))
        self.assertEqual(int(self.client.session['_auth_user_id']), self.member.pk)

    def test_login_with_username_success(self):
        """Users can authenticate using their unique username."""
        response = self.client.post(reverse('accounts:login'), {
            'username_or_email': 'lahore_member',
            'password': self.member_password,
        })
        self.assertRedirects(response, reverse('accounts:dashboard'))
        self.assertEqual(int(self.client.session['_auth_user_id']), self.member.pk)

    def test_login_invalid_password_rejected(self):
        """Login with wrong password fails and displays user-friendly error."""
        response = self.client.post(reverse('accounts:login'), {
            'username_or_email': 'member@lahorecityhub.pk',
            'password': 'WrongPassword123!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid sign-in credentials')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_login_inactive_user_rejected(self):
        """Inactive user account cannot authenticate."""
        self.member.is_active = False
        self.member.save()

        response = self.client.post(reverse('accounts:login'), {
            'username_or_email': 'member@lahorecityhub.pk',
            'password': self.member_password,
        })
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_login_open_redirect_defense(self):
        """Open redirect attacks via 'next' query param are prevented."""
        # Attempt to redirect to external attacker URL
        malicious_url = 'http://attacker.com/malicious/phishing'
        response = self.client.post(f"{reverse('accounts:login')}?next={malicious_url}", {
            'username_or_email': 'member@lahorecityhub.pk',
            'password': self.member_password,
            'next': malicious_url,
        })
        # Must NOT redirect to attacker.com; must fall back safely to internal dashboard
        self.assertRedirects(response, reverse('accounts:dashboard'))

    def test_login_valid_next_redirect(self):
        """Legitimate internal relative 'next' URL is respected after login."""
        valid_next = '/places/'
        response = self.client.post(f"{reverse('accounts:login')}?next={valid_next}", {
            'username_or_email': 'member@lahorecityhub.pk',
            'password': self.member_password,
            'next': valid_next,
        })
        self.assertRedirects(response, valid_next)

    # ==========================================================
    # 3. Logout Tests
    # ==========================================================

    def test_logout_clears_session_and_redirects(self):
        """Logout flushes authentication session and redirects to home."""
        self.client.login(username='member@lahorecityhub.pk', password=self.member_password)
        self.assertIn('_auth_user_id', self.client.session)

        response = self.client.get(reverse('accounts:logout'))
        self.assertRedirects(response, reverse('core:home'))
        self.assertNotIn('_auth_user_id', self.client.session)

    # ==========================================================
    # 4. Password Change Tests
    # ==========================================================

    def test_password_change_requires_login(self):
        """Unauthenticated user is redirected to login with next parameter."""
        response = self.client.get(reverse('accounts:password_change'))
        expected_redirect = f"{reverse('accounts:login')}?next={reverse('accounts:password_change')}"
        self.assertRedirects(response, expected_redirect)

    def test_password_change_successful(self):
        """User can change password; session is preserved via update_session_auth_hash."""
        self.client.login(username='member@lahorecityhub.pk', password=self.member_password)
        new_password = 'BrandNewPassword2026!'

        data = {
            'old_password': self.member_password,
            'new_password1': new_password,
            'new_password2': new_password,
        }
        response = self.client.post(reverse('accounts:password_change'), data)
        self.assertRedirects(response, reverse('accounts:dashboard'))

        # User remains logged in
        self.assertEqual(int(self.client.session['_auth_user_id']), self.member.pk)

        # New password works
        self.member.refresh_from_db()
        self.assertTrue(self.member.check_password(new_password))

    def test_password_change_wrong_old_password_rejected(self):
        """Incorrect old password halts change."""
        self.client.login(username='member@lahorecityhub.pk', password=self.member_password)
        data = {
            'old_password': 'IncorrectOldPassword123!',
            'new_password1': 'BrandNewPassword2026!',
            'new_password2': 'BrandNewPassword2026!',
        }
        response = self.client.post(reverse('accounts:password_change'), data)
        self.assertEqual(response.status_code, 200)
        self.member.refresh_from_db()
        self.assertTrue(self.member.check_password(self.member_password))

    # ==========================================================
    # 5. Password Reset Workflow Tests
    # ==========================================================

    def test_password_reset_request_sends_email(self):
        """Submitting email dispatches cryptographic password reset email."""
        response = self.client.post(reverse('accounts:password_reset'), {
            'email': self.member.email,
        })
        self.assertRedirects(response, reverse('accounts:password_reset_done'))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Password Reset Requested', mail.outbox[0].subject)
        self.assertIn(self.member.email, mail.outbox[0].to)

    def test_password_reset_nonexistent_email_anti_enumeration(self):
        """Non-existent email still redirects to done view without error to prevent user enumeration."""
        response = self.client.post(reverse('accounts:password_reset'), {
            'email': 'ghost_user@unknown-domain.pk',
        })
        self.assertRedirects(response, reverse('accounts:password_reset_done'))
        # No email sent to non-existent user
        self.assertEqual(len(mail.outbox), 0)

    def test_password_reset_confirm_and_complete(self):
        """Token link allows setting new password and finalizing reset."""
        uid = urlsafe_base64_encode(force_bytes(self.member.pk))
        if isinstance(uid, bytes):
            uid = uid.decode()
        token = default_token_generator.make_token(self.member)

        confirm_url = reverse('accounts:password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
        # Follow Django's Referer-leak protection redirect
        response = self.client.get(confirm_url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Set a New Password')

        # Submit new password to the session-authenticated reset form URL
        reset_post_url = response.redirect_chain[-1][0] if response.redirect_chain else confirm_url
        post_response = self.client.post(reset_post_url, {
            'new_password1': 'ResetCompletePass2026!',
            'new_password2': 'ResetCompletePass2026!',
        })
        self.assertRedirects(post_response, reverse('accounts:password_reset_complete'))

        self.member.refresh_from_db()
        self.assertTrue(self.member.check_password('ResetCompletePass2026!'))

    # ==========================================================
    # 6. User Profile & Privacy Tests
    # ==========================================================

    def test_profile_view_requires_authentication(self):
        """Unauthenticated profile access redirects to login."""
        response = self.client.get(reverse('accounts:profile'))
        expected_redirect = f"{reverse('accounts:login')}?next={reverse('accounts:profile')}"
        self.assertRedirects(response, expected_redirect)

    def test_profile_update_successful(self):
        """User can update bio, phone, locality, and notification preferences."""
        self.client.login(username='member@lahorecityhub.pk', password=self.member_password)
        data = {
            'first_name': 'Zainul',
            'last_name': 'Abedin',
            'phone_number': '+92 301 9876543',
            'home_locality': 'Wapda Town Phase 1',
            'bio': 'Passionate about Lahore food history and architectural conservation.',
            'receive_smog_alerts': True,
            'receive_event_digests': True,
        }
        response = self.client.post(reverse('accounts:profile'), data)
        self.assertRedirects(response, reverse('accounts:profile'))

        self.member.refresh_from_db()
        self.assertEqual(self.member.first_name, 'Zainul')
        self.assertEqual(self.member.profile.home_locality, 'Wapda Town Phase 1')
        self.assertTrue(self.member.profile.receive_smog_alerts)
        self.assertTrue(self.member.profile.receive_event_digests)

    def test_profile_avatar_upload_validation(self):
        """Invalid avatar extension or corrupted binary is rejected with validation error."""
        self.client.login(username='member@lahorecityhub.pk', password=self.member_password)
        fake_binary = SimpleUploadedFile("script.sh", b"#!/bin/bash\necho 1", content_type="application/x-sh")

        data = {
            'first_name': 'Zain',
            'last_name': 'Ali',
            'avatar': fake_binary,
        }
        response = self.client.post(reverse('accounts:profile'), data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            'Upload a valid image' in response.content.decode() or
            'Only JPG, PNG, and WEBP image formats are supported' in response.content.decode()
        )

    # ==========================================================
    # 7. Role-Based Permissions & Decorator Tests
    # ==========================================================

    def test_role_required_decorator_allows_authorized_role(self):
        """Views protected by @business_owner_required allow business owners."""
        @business_owner_required
        def dummy_owner_view(request):
            return HttpResponse("Owner Access Granted")

        # Create request for owner
        request = self.factory.get('/dummy-owner/')
        request.user = self.owner
        response = dummy_owner_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "Owner Access Granted")

    def test_role_required_decorator_denies_unauthorized_role(self):
        """Regular community member accessing business owner view raises 403 PermissionDenied."""
        @business_owner_required
        def dummy_owner_view(request):
            return HttpResponse("Owner Access Granted")

        request = self.factory.get('/dummy-owner/')
        request.user = self.member  # role='member'
        with self.assertRaises(PermissionDenied):
            dummy_owner_view(request)

    def test_admin_bypasses_role_restrictions(self):
        """Administrators have universal authorization across role gates."""
        @business_owner_required
        def dummy_owner_view(request):
            return HttpResponse("Owner Access Granted")

        request = self.factory.get('/dummy-owner/')
        request.user = self.admin
        response = dummy_owner_view(request)
        self.assertEqual(response.status_code, 200)

    # ==========================================================
    # 8. Business Owner Dashboard & Content Submission Isolation
    # ==========================================================

    def test_dashboard_requires_login(self):
        """Private dashboard URLs redirect anonymous visitors to login."""
        response = self.client.get(reverse('accounts:dashboard'))
        expected_redirect = f"{reverse('accounts:login')}?next={reverse('accounts:dashboard')}"
        self.assertRedirects(response, expected_redirect)

    def test_dashboard_displays_user_submissions_and_status(self):
        """Owner dashboard shows their businesses with publication and verification statuses."""
        self.client.login(username='owner@lahorecityhub.pk', password=self.owner_password)
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Content Submission Status')
        self.assertContains(response, 'Apex Cloud Solutions')
        self.assertContains(response, 'Published & Live')
        self.assertContains(response, 'TechHub Coworking Lahore')
        self.assertContains(response, 'Pending Editorial Approval')

    def test_dashboard_enforces_object_level_isolation(self):
        """User A's dashboard must NEVER expose User B's unpublished submissions."""
        self.client.login(username='owner@lahorecityhub.pk', password=self.owner_password)
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
        # self.owner's submissions are visible
        self.assertContains(response, 'Apex Cloud Solutions')
        # self.other_owner's unpublished submission must NOT appear
        self.assertNotContains(response, 'Secret Startup Labs')
