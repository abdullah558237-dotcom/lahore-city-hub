import io
from PIL import Image
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.core.models import LocalityZone, Locality
from apps.businesses.models import (
    BusinessCategory,
    Business,
    BusinessClaim,
    BusinessEditRequest,
    BusinessReport,
    validate_image_extension,
)
from apps.businesses.admin import (
    BusinessAdmin,
    BusinessEditRequestAdmin,
    BusinessReportAdmin,
    BusinessClaimAdmin,
)
from apps.businesses.forms import (
    BusinessSubmissionForm,
    BusinessEditForm,
    BusinessEditRequestForm,
    BusinessReportForm,
)

User = get_user_model()


def generate_test_image(extension='JPEG'):
    """Helper to generate a valid in-memory image for upload tests."""
    file = io.BytesIO()
    image = Image.new('RGB', (100, 100), color='blue')
    image.save(file, extension)
    file.seek(0)
    ext_str = 'jpg' if extension.upper() == 'JPEG' else extension.lower()
    return SimpleUploadedFile(f"test_storefront.{ext_str}", file.read(), content_type=f"image/{ext_str}")


class BusinessDirectorySecurityAndFeatureTests(TestCase):
    """
    Exhaustive test suite for the Lahore City Hub Local Business Directory:
    - Ownership restrictions: Users can only manage their own listings
    - Unauthorized access prevention: 403 PermissionDenied on unauthorized edit/delete
    - Submission workflow: New submissions remain unpublished (is_active=False, verification_status='pending')
    - Privilege escalation prevention: Users cannot self-grant active, featured, or verified status
    - Validation of URLs, form fields, and uploaded image files
    - Directory visibility: Public list/detail only exposes active businesses (inactive returns 404 to non-owners)
    - Faceted filters: category, area, verified-only, keyword search, sorting
    - Edit requests: Modifications to published businesses create moderated audit requests
    - Admin approval actions: Approve & Publish, Merge edits, Resolve reports, Approve claims
    - Incorrect listing reports: Submission and admin resolution
    """

    def setUp(self):
        self.client = Client()

        # Users: Owner A, Owner B, Admin/Staff
        self.owner_a = User.objects.create_user(
            username='ownera',
            email='owner.a@example.pk',
            password='Password123!'
        )
        self.owner_b = User.objects.create_user(
            username='ownerb',
            email='owner.b@example.pk',
            password='Password123!'
        )
        self.staff_admin = User.objects.create_superuser(
            username='lahore_admin',
            email='admin@lahorecityhub.pk',
            password='AdminPassword123!'
        )

        # Spatial Hierarchy
        self.zone_gulberg = LocalityZone.objects.create(name="Gulberg & Central", slug="gulberg-central")
        self.zone_walled = LocalityZone.objects.create(name="Walled City & Northern", slug="walled-city-northern")

        self.loc_gulberg = Locality.objects.create(
            zone=self.zone_gulberg, name="Gulberg II", slug="gulberg-2", postal_code="54660"
        )
        self.loc_anarkali = Locality.objects.create(
            zone=self.zone_walled, name="Old Anarkali Bazaar", slug="old-anarkali", postal_code="54000"
        )

        # Categories
        self.cat_artisan = BusinessCategory.objects.create(
            name="Handicrafts & Artisans", slug="handicrafts", icon_class="bi-gem"
        )
        self.cat_solar = BusinessCategory.objects.create(
            name="Renewable & Solar Energy", slug="solar-energy", icon_class="bi-sun"
        )
        self.cat_legal = BusinessCategory.objects.create(
            name="Legal & Corporate Services", slug="legal-services", icon_class="bi-briefcase"
        )

        # 1. Published Business owned by Owner A (active=True, verified)
        self.biz_active_a = Business.objects.create(
            title="Anarkali Royal Khussa Emporium",
            title_ur="انارکلی رائل کھسہ ایمپوریم",
            slug="anarkali-royal-khussa-emporium",
            category=self.cat_artisan,
            locality=self.loc_anarkali,
            address="Bano Bazaar, Old Anarkali, Lahore",
            landmark="Opposite Bano Market Gate",
            phone_number="+92-42-37351122",
            email="contact@royalkhussa.pk",
            website="https://www.royalkhussa.pk",
            whatsapp_number="+923004455667",
            operating_hours="Mon-Sat: 11:00 AM - 10:00 PM",
            registration_number="LCCI-KH-1958",
            source_url="https://lcci.com.pk/members/khussa",
            summary="Specialists in handcrafted genuine leather tilla-embroidered Khussas since 1958.",
            description="Established over six decades ago in the historic heart of Old Anarkali...",
            is_active=True,
            is_featured=True,
            verification_status='verified',
            claimed_by=self.owner_a,
            submitted_by=self.owner_a,
        )

        # 2. Published Business owned by Owner B (active=True, claimed)
        self.biz_active_b = Business.objects.create(
            title="Gulberg Solar & Clean Energy",
            title_ur="گلبرگ سولر اینڈ کلین انرجی",
            slug="gulberg-solar-clean-energy",
            category=self.cat_solar,
            locality=self.loc_gulberg,
            address="Plaza 44, Main Market, Gulberg II, Lahore",
            phone_number="+92-42-35789901",
            email="info@gulbergsolar.pk",
            website="https://gulbergsolar.pk",
            whatsapp_number="+923215566778",
            operating_hours="Mon-Fri: 9:00 AM - 6:00 PM",
            summary="AEDB certified Tier-1 hybrid solar net-metering installations.",
            description="Providing commercial and residential solar installation across Lahore...",
            is_active=True,
            is_featured=False,
            verification_status='claimed',
            claimed_by=self.owner_b,
            submitted_by=self.owner_b,
        )

        # 3. Unpublished / Pending Draft submitted by Owner A (active=False, pending)
        self.biz_pending_a = Business.objects.create(
            title="Pak Law Corporate Chambers",
            slug="pak-law-corporate-chambers",
            category=self.cat_legal,
            locality=self.loc_gulberg,
            address="Legal Wing, 3rd Floor, Siddique Trade Centre, Gulberg",
            phone_number="+92-42-35780011",
            summary="Corporate governance, SECP registration, and taxation litigation.",
            description="Draft listing submitted for editorial audit...",
            is_active=False,
            is_featured=False,
            verification_status='pending',
            submitted_by=self.owner_a,
        )

    # =========================================================================
    # 1. PUBLIC LISTING & FILTER TESTS
    # =========================================================================

    def test_business_list_public_only_shows_active_listings(self):
        """Active businesses must appear in the directory; unpublished drafts must never appear."""
        url = reverse('businesses:list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.biz_active_a.title)
        self.assertContains(response, "Gulberg Solar &amp; Clean Energy")
        # Unpublished draft must NOT be present
        self.assertNotContains(response, self.biz_pending_a.title)

    def test_business_list_category_filter(self):
        """Filtering by category slug returns matching items only."""
        url = reverse('businesses:list') + f"?category={self.cat_artisan.slug}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.biz_active_a.title)
        self.assertNotContains(response, "Gulberg Solar &amp; Clean Energy")

    def test_business_list_area_filter(self):
        """Filtering by locality slug returns items in that locality."""
        url = reverse('businesses:list') + f"?area={self.loc_gulberg.slug}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gulberg Solar &amp; Clean Energy")
        self.assertNotContains(response, self.biz_active_a.title)

    def test_business_list_keyword_search(self):
        """Keyword search 'Khussa' locates relevant businesses."""
        url = reverse('businesses:list') + "?q=Khussa"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Anarkali Royal Khussa Emporium")
        self.assertNotContains(response, "Gulberg Solar")

    def test_business_list_verified_filter(self):
        """Verified filter returns only verified and claimed entries."""
        url = reverse('businesses:list') + "?verified_only=1"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.biz_active_a.title)
        self.assertContains(response, "Gulberg Solar &amp; Clean Energy")

    def test_business_list_empty_state(self):
        """Unmatched search query renders user-friendly empty state."""
        url = reverse('businesses:list') + "?q=NonExistentEnterprise12345"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No Matching Businesses Found")

    # =========================================================================
    # 2. DETAIL PAGE & VISIBILITY TESTS
    # =========================================================================

    def test_business_detail_active_public_access(self):
        """Public visitors can view active business profiles; increments view_count."""
        initial_views = self.biz_active_a.view_count
        url = reverse('businesses:detail', kwargs={'slug': self.biz_active_a.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.biz_active_a.title)
        self.assertContains(response, "Schema.org LocalBusiness")

        self.biz_active_a.refresh_from_db()
        self.assertEqual(self.biz_active_a.view_count, initial_views + 1)

    def test_business_detail_inactive_hidden_from_public(self):
        """Unpublished business returns HTTP 404 to anonymous and non-owner users."""
        url = reverse('businesses:detail', kwargs={'slug': self.biz_pending_a.slug})
        # 1. Anonymous visitor
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # 2. Non-owner authenticated user
        self.client.login(username='ownerb', password='Password123!')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_business_detail_inactive_visible_to_author_and_staff(self):
        """Author (submitted_by) or staff can preview inactive listings."""
        url = reverse('businesses:detail', kwargs={'slug': self.biz_pending_a.slug})

        # Author preview
        self.client.login(username='ownera', password='Password123!')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Listing Pending Moderation (Unpublished Preview)")

        # Staff preview
        self.client.login(username='lahore_admin', password='AdminPassword123!')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    # =========================================================================
    # 3. SUBMISSION WORKFLOW & PRIVILEGE HARDENING
    # =========================================================================

    def test_submission_requires_authentication(self):
        """Unauthenticated submission attempts redirect to login, while GET is accessible to visitors."""
        url = reverse('businesses:submit')
        res_get = self.client.get(url)
        self.assertEqual(res_get.status_code, 200)
        self.assertContains(res_get, "Submit or Claim a Business Listing")

        # POST without authentication must redirect to login
        response = self.client.post(url, {'title': 'Anonymous Attempt'})
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_submission_remains_unpublished_until_approved(self):
        """New submissions must be saved with is_active=False and verification_status='pending'."""
        self.client.login(username='ownera', password='Password123!')
        url = reverse('businesses:submit')

        post_data = {
            'title': 'DHA Solar Diagnostics & Audits',
            'category': self.cat_solar.pk,
            'locality': self.loc_gulberg.pk,
            'address': 'Phase 5 Commercial Hub, DHA Lahore',
            'phone_number': '+92-42-35891100',
            'summary': 'Solar performance testing and thermographic drone audits.',
            'description': 'Certified energy auditors offering comprehensive PV panel testing...',
            'website': 'https://dhasolar.pk',
        }

        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('businesses:dashboard'))

        # Verify business in database
        new_biz = Business.objects.get(title='DHA Solar Diagnostics & Audits')
        self.assertFalse(new_biz.is_active, "New business submission MUST NOT be active!")
        self.assertEqual(new_biz.verification_status, 'pending')
        self.assertFalse(new_biz.is_featured)
        self.assertEqual(new_biz.submitted_by, self.owner_a)

    def test_submission_prevents_privilege_escalation(self):
        """Form must ignore malicious attempts to grant active, featured, or verified status."""
        self.client.login(username='ownerb', password='Password123!')
        url = reverse('businesses:submit')

        malicious_post_data = {
            'title': 'Exploit Security Business Attempt',
            'category': self.cat_legal.pk,
            'locality': self.loc_anarkali.pk,
            'address': 'Katchery Road, Lahore',
            'phone_number': '+92-42-37112233',
            'summary': 'Attempting privilege injection attack.',
            'description': 'Description content for exploit attempt...',
            # Injected privileged fields:
            'is_active': True,
            'is_featured': True,
            'verification_status': 'verified',
            'claimed_by': self.owner_b.pk,
        }

        response = self.client.post(url, malicious_post_data)
        self.assertEqual(response.status_code, 302)

        created_biz = Business.objects.get(title='Exploit Security Business Attempt')
        # All privileged fields must remain denied
        self.assertFalse(created_biz.is_active)
        self.assertFalse(created_biz.is_featured)
        self.assertEqual(created_biz.verification_status, 'pending')
        self.assertIsNone(created_biz.claimed_by)

    def test_submission_validates_urls_and_images(self):
        """Invalid URLs and non-image files must be rejected by form."""
        self.client.login(username='ownera', password='Password123!')
        url = reverse('businesses:submit')

        # Invalid website URL
        invalid_post = {
            'title': 'Test Invalid URL Enterprise',
            'category': self.cat_artisan.pk,
            'locality': self.loc_anarkali.pk,
            'address': 'Test Address, Lahore',
            'phone_number': '+92-300-1112233',
            'summary': 'Test summary',
            'description': 'Test description',
            'website': 'not-a-valid-url-protocol',
        }
        response = self.client.post(url, invalid_post)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'website', 'Please enter a valid website URL starting with http:// or https://.')

        # Invalid non-image file upload
        fake_exe = SimpleUploadedFile("malicious.exe", b"binarycontent", content_type="application/octet-stream")
        file_post = invalid_post.copy()
        file_post['website'] = 'https://valid-url.com'
        file_post['primary_image'] = fake_exe

        response = self.client.post(url, file_post)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'primary_image', 'Upload a valid image. The file you uploaded was either not an image or a corrupted image.')

        # Unsupported image format (.bmp)
        bmp_file = io.BytesIO()
        bmp_img = Image.new('RGB', (50, 50), color='red')
        bmp_img.save(bmp_file, 'BMP')
        bmp_file.seek(0)
        unsupported_img = SimpleUploadedFile("storefront.bmp", bmp_file.read(), content_type="image/bmp")

        file_post_bmp = invalid_post.copy()
        file_post_bmp['website'] = 'https://valid-url.com'
        file_post_bmp['primary_image'] = unsupported_img

        response_bmp = self.client.post(url, file_post_bmp)
        self.assertEqual(response_bmp.status_code, 200)
        self.assertFormError(response_bmp, 'form', 'primary_image', 'Unsupported image format ".bmp". Allowed formats: JPG, PNG, WEBP, SVG.')

    # =========================================================================
    # 4. OWNER DASHBOARD & RECORD ISOLATION
    # =========================================================================

    def test_owner_dashboard_requires_login(self):
        """Anonymous access to owner dashboard redirects to login."""
        url = reverse('businesses:dashboard')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_owner_dashboard_isolation(self):
        """Owners can only view their own listings and claims on the dashboard."""
        self.client.login(username='ownera', password='Password123!')
        url = reverse('businesses:dashboard')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Owner A must see their own businesses
        self.assertContains(response, self.biz_active_a.title)
        self.assertContains(response, self.biz_pending_a.title)

        # Owner A must NOT see Owner B's businesses
        self.assertNotContains(response, self.biz_active_b.title)

    # =========================================================================
    # 5. EDIT & DELETE AUTHORIZATION (403 PERMISSION DENIED)
    # =========================================================================

    def test_unauthorized_user_cannot_edit_business(self):
        """User B attempting to edit User A's business receives HTTP 403 Forbidden."""
        self.client.login(username='ownerb', password='Password123!')
        url = reverse('businesses:edit', kwargs={'slug': self.biz_active_a.slug})

        # GET request
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

        # POST request
        response = self.client.post(url, {'title': 'Hacked Title'})
        self.assertEqual(response.status_code, 403)

    def test_unauthorized_user_cannot_delete_business(self):
        """User B attempting to delete User A's business receives HTTP 403 Forbidden."""
        self.client.login(username='ownerb', password='Password123!')
        url = reverse('businesses:delete', kwargs={'slug': self.biz_active_a.slug})

        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Business.objects.filter(pk=self.biz_active_a.pk).exists())

    def test_owner_can_delete_their_business(self):
        """Owner can successfully delete their listing."""
        self.client.login(username='ownera', password='Password123!')
        url = reverse('businesses:delete', kwargs={'slug': self.biz_pending_a.slug})

        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Business.objects.filter(pk=self.biz_pending_a.pk).exists())

    # =========================================================================
    # 6. EDIT REQUEST MODERATION WORKFLOW
    # =========================================================================

    def test_editing_published_business_creates_edit_request(self):
        """
        Modifying an active, published business must not alter live data immediately;
        it creates a BusinessEditRequest pending admin approval.
        """
        self.client.login(username='ownera', password='Password123!')
        url = reverse('businesses:edit', kwargs={'slug': self.biz_active_a.slug})

        post_data = {
            'title': 'Anarkali Royal Khussa Emporium (Renovated)',
            'summary': 'Updated short summary with expanded bridal couture range.',
            'description': 'Updated description with expanded inventory...',
            'address': 'Bano Bazaar, Shop 14-16, Old Anarkali, Lahore',
            'phone_number': '+92-42-37359999',
            'website': 'https://www.royalkhussa.pk',
            'operating_hours': 'Mon-Sun: 10:00 AM - 11:00 PM',
        }

        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('businesses:dashboard'))

        # Live business title must remain UNCHANGED
        self.biz_active_a.refresh_from_db()
        self.assertEqual(self.biz_active_a.title, "Anarkali Royal Khussa Emporium")

        # Edit request created
        edit_req = BusinessEditRequest.objects.get(business=self.biz_active_a)
        self.assertEqual(edit_req.title, 'Anarkali Royal Khussa Emporium (Renovated)')
        self.assertEqual(edit_req.status, 'pending')
        self.assertEqual(edit_req.requested_by, self.owner_a)

    def test_editing_unpublished_draft_updates_in_place(self):
        """
        Modifying an unpublished draft directly updates the draft while remaining pending.
        """
        self.client.login(username='ownera', password='Password123!')
        url = reverse('businesses:edit', kwargs={'slug': self.biz_pending_a.slug})

        post_data = {
            'title': 'Pak Law Corporate & Taxation Chambers',
            'category': self.cat_legal.pk,
            'locality': self.loc_gulberg.pk,
            'address': 'Legal Wing, 4th Floor, Siddique Trade Centre, Gulberg',
            'phone_number': '+92-42-35780099',
            'summary': 'Updated summary description.',
            'description': 'Updated detailed description for legal chambers...',
        }

        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302)

        self.biz_pending_a.refresh_from_db()
        self.assertEqual(self.biz_pending_a.title, 'Pak Law Corporate & Taxation Chambers')
        self.assertFalse(self.biz_pending_a.is_active)
        self.assertEqual(self.biz_pending_a.verification_status, 'pending')

    # =========================================================================
    # 7. INCORRECT LISTING REPORTS
    # =========================================================================

    def test_report_listing_public_submission(self):
        """Any citizen can submit an inaccuracy report on an active listing."""
        url = reverse('businesses:report', kwargs={'slug': self.biz_active_a.slug})

        report_data = {
            'reporter_name': 'Ali Raza',
            'reporter_email': 'ali.raza@example.pk',
            'reason': 'wrong_hours',
            'details': 'Operating hours on Sunday are closed; shop does not open on weekends.',
        }

        response = self.client.post(url, report_data)
        self.assertEqual(response.status_code, 302)

        report = BusinessReport.objects.get(business=self.biz_active_a)
        self.assertEqual(report.reporter_name, 'Ali Raza')
        self.assertEqual(report.reason, 'wrong_hours')
        self.assertEqual(report.status, 'pending')

    # =========================================================================
    # 8. ADMIN APPROVAL WORKFLOWS & ACTIONS
    # =========================================================================

    def test_admin_approve_and_publish_action(self):
        """Admin action approve_and_publish marks business active and verified."""
        admin_instance = BusinessAdmin(Business, None)
        request = self.client.request().wsgi_request
        request.user = self.staff_admin

        queryset = Business.objects.filter(pk=self.biz_pending_a.pk)
        admin_instance.approve_and_publish(request, queryset)

        self.biz_pending_a.refresh_from_db()
        self.assertTrue(self.biz_pending_a.is_active)
        self.assertEqual(self.biz_pending_a.verification_status, 'verified')
        self.assertEqual(self.biz_pending_a.verified_by, self.staff_admin)

    def test_admin_approve_and_merge_edit_request(self):
        """Admin action approve_and_merge applies requested edits to live business."""
        edit_req = BusinessEditRequest.objects.create(
            business=self.biz_active_a,
            requested_by=self.owner_a,
            title="Anarkali Royal Khussa Emporium & Bridal",
            summary="New approved summary.",
            description="New approved description.",
            address="Bano Bazaar, New Shop 20, Old Anarkali",
            phone_number="+92-42-37359999",
            status="pending"
        )

        admin_instance = BusinessEditRequestAdmin(BusinessEditRequest, None)
        request = self.client.request().wsgi_request
        request.user = self.staff_admin

        queryset = BusinessEditRequest.objects.filter(pk=edit_req.pk)
        admin_instance.approve_and_merge(request, queryset)

        # Business must be updated with merged values
        self.biz_active_a.refresh_from_db()
        self.assertEqual(self.biz_active_a.title, "Anarkali Royal Khussa Emporium & Bridal")
        self.assertEqual(self.biz_active_a.phone_number, "+92-42-37359999")

        # Edit request marked approved
        edit_req.refresh_from_db()
        self.assertEqual(edit_req.status, 'approved')
        self.assertEqual(edit_req.reviewed_by, self.staff_admin)

    def test_admin_approve_business_claim(self):
        """Admin action approve_claim assigns ownership of business to claimant."""
        claim = BusinessClaim.objects.create(
            business=self.biz_active_b,
            claimant=self.owner_a,
            claimant_role="Chief Executive Officer",
            official_email="ceo@gulbergsolar.pk",
            contact_phone="+92-300-9998877",
            status="pending"
        )

        admin_instance = BusinessClaimAdmin(BusinessClaim, None)
        request = self.client.request().wsgi_request
        request.user = self.staff_admin

        queryset = BusinessClaim.objects.filter(pk=claim.pk)
        admin_instance.approve_claim(request, queryset)

        self.biz_active_b.refresh_from_db()
        self.assertEqual(self.biz_active_b.claimed_by, self.owner_a)
        self.assertEqual(self.biz_active_b.verification_status, 'claimed')

        claim.refresh_from_db()
        self.assertEqual(claim.status, 'approved')
        self.assertEqual(claim.reviewed_by, self.staff_admin)

    def test_admin_resolve_business_report(self):
        """Admin action mark_resolved resolves an inaccuracy report."""
        report = BusinessReport.objects.create(
            business=self.biz_active_a,
            reporter_name="Civic Auditor",
            reporter_email="auditor@example.pk",
            reason="wrong_phone",
            details="Phone number had an incorrect area code.",
            status="pending"
        )

        admin_instance = BusinessReportAdmin(BusinessReport, None)
        request = self.client.request().wsgi_request
        request.user = self.staff_admin

        queryset = BusinessReport.objects.filter(pk=report.pk)
        admin_instance.mark_resolved(request, queryset)

        report.refresh_from_db()
        self.assertEqual(report.status, 'resolved')
        self.assertEqual(report.resolved_by, self.staff_admin)
