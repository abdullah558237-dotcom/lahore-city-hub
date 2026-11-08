from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from apps.core.models import LocalityZone, Locality
from apps.businesses.models import Business, BusinessCategory, BusinessPromotionRequest

User = get_user_model()


class MonetizationAndFeaturedListingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create users
        cls.owner = User.objects.create_user(
            email='owner@testbusiness.pk',
            password='Password123!',
            username='test_owner'
        )
        cls.other_user = User.objects.create_user(
            email='other@testuser.pk',
            password='Password123!',
            username='test_other'
        )
        cls.admin_user = User.objects.create_superuser(
            email='admin@lahorehub.pk',
            password='AdminPassword123!',
            username='test_admin'
        )

        # Create taxonomy
        cls.zone = LocalityZone.objects.create(name='Gulberg Zone', slug='gulberg-zone')
        cls.locality = Locality.objects.create(name='Gulberg III', slug='gulberg-iii', zone=cls.zone)
        cls.category = BusinessCategory.objects.create(name='Solar Technology', slug='solar-technology')

        now = timezone.now()

        # Standard business (organic)
        cls.standard_biz = Business.objects.create(
            title='Alpha Standard Solar',
            slug='alpha-standard-solar',
            category=cls.category,
            locality=cls.locality,
            address='Shop 12, Main Boulevard, Gulberg III',
            summary='Standard local solar provider.',
            description='Detailed solar installation services.',
            phone_number='+92-42-35711111',
            is_active=True,
            is_featured=False,
            promotion_tier=Business.PROMOTION_TIER_STANDARD,
            submitted_by=cls.owner,
            claimed_by=cls.owner,
        )

        # Featured business (sponsored spotlight)
        cls.featured_biz = Business.objects.create(
            title='Zeta Premium Solar Power',
            slug='zeta-premium-solar-power',
            category=cls.category,
            locality=cls.locality,
            address='Plaza 45, MM Alam Road, Gulberg III',
            summary='Premium commercial solar power engineering.',
            description='Certified tier-1 solar panel distributor and installer.',
            phone_number='+92-42-35799999',
            is_active=True,
            is_featured=True,
            promotion_tier=Business.PROMOTION_TIER_FEATURED,
            featured_until=now + timedelta(days=60),
            submitted_by=cls.owner,
            claimed_by=cls.owner,
        )

    def setUp(self):
        self.client = Client()

    def test_featured_listing_priority_ordering(self):
        """
        Verify that in default/recommended sorting, featured listings appear
        prioritized at the top of directory listings above standard organic listings.
        """
        url = reverse('businesses:list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        businesses = list(response.context['businesses'])
        self.assertGreaterEqual(len(businesses), 2)
        # Featured listing (Zeta) should appear before Standard listing (Alpha) despite 'Z' vs 'A'
        zeta_idx = next(i for i, b in enumerate(businesses) if b.pk == self.featured_biz.pk)
        alpha_idx = next(i for i, b in enumerate(businesses) if b.pk == self.standard_biz.pk)
        self.assertLess(zeta_idx, alpha_idx, "Featured business must appear above standard business.")

    def test_sponsored_label_visibility_in_directory_and_detail(self):
        """
        Verify high-contrast 'Sponsored' badge is rendered on featured listings
        and NOT displayed on organic standard listings.
        """
        # Directory list
        response = self.client.get(reverse('businesses:list'))
        content = response.content.decode('utf-8')
        self.assertIn('Sponsored', content)
        self.assertIn('Sponsored Spotlight', content)

        # Detail view for featured listing
        featured_detail = self.client.get(reverse('businesses:detail', kwargs={'slug': self.featured_biz.slug}))
        self.assertEqual(featured_detail.status_code, 200)
        featured_content = featured_detail.content.decode('utf-8')
        self.assertIn('Sponsored Partner', featured_content)
        self.assertIn('Promotional placement enhances visibility within our city guide and does not influence external search engine rankings', featured_content)

        # Detail view for standard listing
        standard_detail = self.client.get(reverse('businesses:detail', kwargs={'slug': self.standard_biz.slug}))
        self.assertEqual(standard_detail.status_code, 200)
        standard_content = standard_detail.content.decode('utf-8')
        self.assertNotIn('Sponsored Partner', standard_content)

    def test_owner_dashboard_shows_promotion_tier_and_expiry(self):
        """
        Verify business owner dashboard clearly shows promotion tier and expiration date.
        """
        self.client.force_login(self.owner)
        response = self.client.get(reverse('businesses:dashboard'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')

        self.assertIn('Featured Spotlight', content)
        self.assertIn('Standard (Free)', content)
        self.assertIn('Active until', content)

    def test_promotion_request_permissions(self):
        """
        Test permission boundaries for requesting listing promotion:
        - Anonymous user is redirected to login (HTTP 302).
        - Non-owner authenticated user is denied access (HTTP 403 Forbidden).
        - Verified owner can view promotion request form (HTTP 200) and submit request.
        """
        promote_url = reverse('businesses:request_promotion', kwargs={'slug': self.standard_biz.slug})

        # 1. Anonymous user redirect
        anon_resp = self.client.get(promote_url)
        self.assertEqual(anon_resp.status_code, 302)
        self.assertIn(reverse('accounts:login'), anon_resp.url)

        # 2. Non-owner user forbidden
        self.client.force_login(self.other_user)
        non_owner_resp = self.client.get(promote_url)
        self.assertEqual(non_owner_resp.status_code, 403)

        non_owner_post = self.client.post(promote_url, {
            'target_tier': Business.PROMOTION_TIER_FEATURED,
            'duration_days': 30,
            'contact_phone': '+92-300-9999999',
            'contact_email': 'other@testuser.pk',
        })
        self.assertEqual(non_owner_post.status_code, 403)

        # 3. Owner access allowed
        self.client.force_login(self.owner)
        owner_resp = self.client.get(promote_url)
        self.assertEqual(owner_resp.status_code, 200)
        self.assertIn('Promote Your Business Listing', owner_resp.content.decode('utf-8'))

    def test_owner_submit_promotion_request_workflow(self):
        """
        Verify owner can submit promotion request without collecting payment details.
        Creates a BusinessPromotionRequest with status='pending'.
        """
        self.client.force_login(self.owner)
        promote_url = reverse('businesses:request_promotion', kwargs={'slug': self.standard_biz.slug})

        post_data = {
            'target_tier': Business.PROMOTION_TIER_FEATURED,
            'duration_days': 90,
            'contact_phone': '+92-300-1234567',
            'contact_email': 'accounts@testbusiness.pk',
            'campaign_goals': 'Summer solar campaign spotlight.',
        }
        response = self.client.post(promote_url, post_data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('businesses:dashboard'))

        # Check request in database
        promo_req = BusinessPromotionRequest.objects.filter(business=self.standard_biz).first()
        self.assertIsNotNone(promo_req)
        self.assertEqual(promo_req.target_tier, Business.PROMOTION_TIER_FEATURED)
        self.assertEqual(promo_req.duration_days, 90)
        self.assertEqual(promo_req.status, 'pending')
        self.assertEqual(promo_req.contact_phone, '+92-300-1234567')

    def test_public_pricing_page_and_ranking_disclaimer(self):
        """
        Verify public pricing page loads, presents tiers, and prominently
        includes the search engine ranking disclaimer.
        """
        url = reverse('core:pricing')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')

        self.assertIn('Standard Organic', content)
        self.assertIn('Verified Pro', content)
        self.assertIn('Featured Partner', content)
        # Verify explicit disclaimer against claiming Google rankings
        self.assertIn('Paid directory placement does not guarantee, promise, or influence external Google search engine rankings', content)

    def test_robots_txt_disallows_promotion_url(self):
        """
        Verify robots.txt disallows crawler access to /businesses/promote/ endpoints.
        """
        response = self.client.get('/robots.txt')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('Disallow: /businesses/promote/', content)
