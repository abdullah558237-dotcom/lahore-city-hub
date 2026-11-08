import os
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from apps.core.models import LocalityZone, Locality
from apps.places.models import Place, PlaceCategory
from apps.restaurants.models import Restaurant, Cuisine
from apps.hospitals.models import Hospital
from apps.education.models import Institution, EducationType
from apps.jobs.models import JobListing, JobCategory, Employer
from apps.businesses.models import Business, BusinessCategory, BusinessPromotionRequest
from apps.events.models import Event, EventCategory, EventVenue
from apps.transport.models import TransitMode, TransitRoute, TransitStation, TransitGuide
from apps.updates.models import UpdateCategory, CityUpdate

User = get_user_model()


class FullPlatformQAMatrixTests(TestCase):
    """
    Comprehensive QA Matrix Test Suite covering all platform endpoints,
    detail pages, search taxonomy, pagination edge cases, permissions,
    admin workflows, forms, business submissions, mobile responsiveness,
    and SEO metadata.
    """
    @classmethod
    def setUpTestData(cls):
        # 1. Users
        cls.admin_user = User.objects.create_superuser(
            email='qa_admin@lahorehub.pk',
            username='qa_admin',
            password='QAPassword123!'
        )
        cls.owner_user = User.objects.create_user(
            email='qa_owner@lahorehub.pk',
            username='qa_owner',
            password='QAOwnerPassword123!',
            role='business_owner'
        )
        cls.member_user = User.objects.create_user(
            email='qa_member@lahorehub.pk',
            username='qa_member',
            password='QAMemberPassword123!',
            role='member'
        )

        # 2. Localities
        cls.zone = LocalityZone.objects.create(name='Gulberg QA Zone', slug='gulberg-qa-zone')
        cls.locality = Locality.objects.create(name='Gulberg Main', slug='gulberg-main', zone=cls.zone)

        # 3. Content Records across all domains
        cls.place_cat = PlaceCategory.objects.create(name='Monuments', slug='monuments')
        cls.place = Place.objects.create(
            title='Shahi Qila Lahore',
            slug='shahi-qila-lahore',
            category=cls.place_cat,
            locality=cls.locality,
            address='Fort Road, Walled City',
            summary='Historic Mughal citadel in Lahore.',
            description='Detailed Mughal architectural masterpiece.',
            is_active=True
        )

        cls.cuisine = Cuisine.objects.create(name='Traditional Mughlai', slug='traditional-mughlai')
        cls.restaurant = Restaurant.objects.create(
            title='Walled City Heritage Dera',
            slug='walled-city-heritage-dera',
            locality=cls.locality,
            address='Food Street Fort Road',
            summary='Authentic Lahori BBQ and Karahi.',
            description='Fine rooftop dining overlooking historic monuments.',
            price_tier='$$$',
            is_active=True
        )
        cls.restaurant.cuisines.add(cls.cuisine)

        cls.hospital = Hospital.objects.create(
            title='Gulberg Medical City Hospital',
            slug='gulberg-medical-city-hospital',
            locality=cls.locality,
            address='Main Boulevard, Gulberg III',
            summary='24/7 Tertiary care hospital.',
            description='Equipped with emergency trauma center and diagnostic lab.',
            is_active=True,
            is_24_7_emergency=True
        )

        cls.edu_type = EducationType.objects.create(name='Public University', slug='public-university')
        cls.institution = Institution.objects.create(
            title='Lahore Metropolitan Institute of Technology',
            slug='lahore-metropolitan-institute-of-technology',
            education_type=cls.edu_type,
            locality=cls.locality,
            address='Canal Road Campus',
            summary='Premier engineering and computing institute.',
            description='Offering undergraduate and postgraduate technical degrees.',
            is_active=True
        )

        cls.employer = Employer.objects.create(
            name='Lahore Tech Ventures',
            slug='lahore-tech-ventures',
            locality=cls.locality
        )
        cls.job_cat = JobCategory.objects.create(name='Software Engineering', slug='software-engineering')
        cls.job = JobListing.objects.create(
            title='Senior Django Cloud Architect',
            slug='senior-django-cloud-architect',
            employer=cls.employer,
            category=cls.job_cat,
            locality=cls.locality,
            employment_type='full_time',
            deadline=timezone.now().date() + timedelta(days=30),
            description='Full stack Python, Django, PostgreSQL, and Linux experience required.',
            is_active=True
        )

        cls.biz_cat = BusinessCategory.objects.create(name='Solar Clean Energy', slug='solar-clean-energy')
        cls.business = Business.objects.create(
            title='Punjab Green Solar Systems',
            slug='punjab-green-solar-systems',
            category=cls.biz_cat,
            locality=cls.locality,
            address='Plaza 10, Main Market Gulberg',
            summary='Tier-1 solar panel installation and net metering services.',
            description='Industrial and residential rooftop solar solutions.',
            is_active=True,
            is_featured=True,
            promotion_tier='featured_spotlight',
            submitted_by=cls.owner_user,
            claimed_by=cls.owner_user
        )

        cls.venue = EventVenue.objects.create(
            name='Alhamra Arts Council',
            slug='alhamra-arts-council',
            locality=cls.locality,
            address='68 Mall Road, Lahore'
        )
        cls.event_cat = EventCategory.objects.create(name='Cultural Festivals', slug='cultural-festivals')
        cls.event = Event.objects.create(
            title='Lahore Literature and Heritage Festival 2026',
            slug='lahore-literature-and-heritage-festival-2026',
            category=cls.event_cat,
            venue=cls.venue,
            organizer_name='Lahore Arts Council',
            start_datetime=timezone.now() + timedelta(days=10),
            end_datetime=timezone.now() + timedelta(days=12),
            description='Sessions on Urdu poetry, Lahori folklore, and architecture.',
            is_active=True
        )

        cls.transit_mode = TransitMode.objects.create(
            name='Metro Train',
            slug='metro-train'
        )
        cls.route = TransitRoute.objects.create(
            mode=cls.transit_mode,
            route_name='Orange Line Metro Train',
            route_code='OLMT-01',
            origin_station='Ali Town',
            destination_station='Dera Gujran',
            is_active=True
        )
        cls.station = TransitStation.objects.create(
            route=cls.route,
            station_name='Anarkali Station',
            station_number=12,
            slug='anarkali-station',
            locality=cls.locality
        )

        cls.guide = TransitGuide.objects.create(
            title='How to Ride the Orange Line Metro Train',
            slug='how-to-ride-the-orange-line-metro-train',
            summary='Complete step-by-step ticketing and transit guide.',
            content='Purchase token at ticket vending machines or use metro card.',
            is_published=True
        )

        cls.update_cat = UpdateCategory.objects.create(name='Civic Advisory', slug='civic-advisory')
        cls.update = CityUpdate.objects.create(
            title='Winter Smog Precautionary Advisory for Lahore',
            slug='winter-smog-precautionary-advisory-for-lahore',
            category=cls.update_cat,
            severity='caution',
            summary='Air quality index alert and health guidelines for residents.',
            content='Citizens are advised to wear N95 masks and avoid unnecessary morning travel.',
            issuing_authority='Environment Protection Department Punjab',
            official_source_url='https://epd.punjab.gov.pk',
            is_active=True
        )

    def setUp(self):
        self.client = Client()

    # =========================================================================
    # 1. PUBLIC DIRECTORY & CORE PAGES HTTP 200 MATRIX
    # =========================================================================

    def test_all_public_directory_listings_and_core_pages_return_200(self):
        """Verify that every public index, directory, and legal page loads with HTTP 200."""
        public_urls = [
            reverse('core:home'),
            reverse('core:about'),
            reverse('core:contact'),
            reverse('core:privacy'),
            reverse('core:terms'),
            reverse('core:pricing'),
            reverse('core:directory_index'),
            reverse('core:search'),
            reverse('places:list'),
            reverse('restaurants:list'),
            reverse('hospitals:list'),
            reverse('education:list'),
            reverse('jobs:list'),
            reverse('businesses:list'),
            reverse('events:list'),
            reverse('transport:overview'),
            reverse('transport:route_list'),
            reverse('transport:station_list'),
            reverse('transport:guide_list'),
            reverse('accounts:login'),
            reverse('accounts:register'),
        ]
        for url in public_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200, f"Page {url} returned {response.status_code}")

        # Updates route redirects to core:home #city-updates section
        updates_resp = self.client.get(reverse('updates:list'))
        self.assertRedirects(updates_resp, reverse('core:home'))

    # =========================================================================
    # 2. DETAIL PAGES MATRIX
    # =========================================================================

    def test_all_domain_detail_pages_return_200(self):
        """Verify that detail views across all domains render with HTTP 200 and valid titles."""
        detail_urls = [
            (reverse('places:detail', kwargs={'slug': self.place.slug}), 'Shahi Qila Lahore'),
            (reverse('restaurants:detail', kwargs={'slug': self.restaurant.slug}), 'Walled City Heritage Dera'),
            (reverse('hospitals:detail', kwargs={'slug': self.hospital.slug}), 'Gulberg Medical City Hospital'),
            (reverse('education:detail', kwargs={'slug': self.institution.slug}), 'Lahore Metropolitan Institute of Technology'),
            (reverse('jobs:detail', kwargs={'slug': self.job.slug}), 'Senior Django Cloud Architect'),
            (reverse('businesses:detail', kwargs={'slug': self.business.slug}), 'Punjab Green Solar Systems'),
            (reverse('events:detail', kwargs={'slug': self.event.slug}), 'Lahore Literature and Heritage Festival 2026'),
            (reverse('transport:route_detail', kwargs={'slug': self.route.slug}), 'Orange Line Metro Train'),
            (reverse('transport:station_detail', kwargs={'slug': self.station.slug}), 'Anarkali Station'),
            (reverse('transport:guide_detail', kwargs={'slug': self.guide.slug}), 'How to Ride the Orange Line Metro Train'),
        ]
        for url, expected_text in detail_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200, f"Detail page {url} failed with {response.status_code}")
                self.assertContains(response, expected_text)

    # =========================================================================
    # 3. SEARCH & FILTER INTEGRITY
    # =========================================================================

    def test_search_and_filter_taxonomy(self):
        """Verify search query filtering, locality filtering, and category selection."""
        # 1. Global keyword search
        search_resp = self.client.get(reverse('core:search'), {'q': 'Solar'})
        self.assertEqual(search_resp.status_code, 200)
        self.assertContains(search_resp, 'Punjab Green Solar Systems')

        # 2. Domain-filtered search
        domain_resp = self.client.get(reverse('core:search'), {'category': 'places', 'q': 'Shahi'})
        self.assertEqual(domain_resp.status_code, 200)
        self.assertContains(domain_resp, 'Shahi Qila Lahore')

        # 3. Business list category filter
        biz_cat_resp = self.client.get(reverse('businesses:list'), {'category': self.biz_cat.slug})
        self.assertEqual(biz_cat_resp.status_code, 200)
        self.assertContains(biz_cat_resp, 'Punjab Green Solar Systems')

        # 4. Verified-only filter
        biz_verif_resp = self.client.get(reverse('businesses:list'), {'verified_only': '1'})
        self.assertEqual(biz_verif_resp.status_code, 200)

    # =========================================================================
    # 4. PAGINATION EDGE CASES
    # =========================================================================

    def test_pagination_edge_cases_handled_gracefully(self):
        """Verify that out-of-range and non-integer page requests fall back gracefully without 500 error."""
        # Page out of range returns last or first page cleanly
        resp_high = self.client.get(reverse('businesses:list'), {'page': 9999})
        self.assertEqual(resp_high.status_code, 200)

        # Non-integer page returns first page cleanly
        resp_str = self.client.get(reverse('businesses:list'), {'page': 'invalid_string'})
        self.assertEqual(resp_str.status_code, 200)

    # =========================================================================
    # 5. AUTHENTICATION & PERMISSION BOUNDARIES
    # =========================================================================

    def test_authentication_workflow_and_protected_dashboards(self):
        """Verify login, session persistence, and protected owner/member dashboards."""
        # 1. Unauthenticated redirect to login
        dash_resp = self.client.get(reverse('businesses:dashboard'))
        self.assertEqual(dash_resp.status_code, 302)
        self.assertIn(reverse('accounts:login'), dash_resp.url)

        # 2. Authenticated business owner can access owner dashboard
        self.client.force_login(self.owner_user)
        owner_dash = self.client.get(reverse('businesses:dashboard'))
        self.assertEqual(owner_dash.status_code, 200)
        self.assertContains(owner_dash, 'Business Owner & Submitter Dashboard')

        # 3. Member dashboard access
        self.client.force_login(self.member_user)
        member_dash = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(member_dash.status_code, 200)

    # =========================================================================
    # 6. SITEMAP, ROBOTS & SEO METADATA
    # =========================================================================

    def test_sitemap_and_robots_txt_specifications(self):
        """Verify sitemap.xml structure and robots.txt crawling instructions."""
        sitemap_resp = self.client.get('/sitemap.xml')
        self.assertEqual(sitemap_resp.status_code, 200)
        self.assertEqual(sitemap_resp['Content-Type'], 'application/xml')
        sitemap_content = sitemap_resp.content.decode('utf-8')
        self.assertIn('http://testserver/pricing/', sitemap_content)
        self.assertIn('http://testserver/businesses/punjab-green-solar-systems/', sitemap_content)

        robots_resp = self.client.get('/robots.txt')
        self.assertEqual(robots_resp.status_code, 200)
        self.assertEqual(robots_resp['Content-Type'], 'text/plain; charset=utf-8')
        robots_content = robots_resp.content.decode('utf-8')
        self.assertIn('Disallow: /admin/', robots_content)
        self.assertIn('Disallow: /businesses/promote/', robots_content)
        self.assertIn('Sitemap: http://testserver/sitemap.xml', robots_content)

    # =========================================================================
    # 7. BUSINESS SUBMISSION WORKFLOW & FORMS
    # =========================================================================

    def test_business_submission_workflow(self):
        """Verify business onboarding form GET and authenticated submission lifecycle."""
        # 1. Unauthenticated user can view the onboarding form
        form_get = self.client.get(reverse('businesses:submit'))
        self.assertEqual(form_get.status_code, 200)
        self.assertContains(form_get, 'Submit or Claim a Business Listing')

        # 2. Unauthenticated POST redirects to login
        post_unauth = self.client.post(reverse('businesses:submit'), {
            'title': 'New Lahore Cafe',
            'category': self.biz_cat.pk,
            'locality': self.locality.pk,
            'address': 'Main Market Gulberg',
            'summary': 'Cozy coffee and pastry spot.',
            'phone': '03001234567',
        })
        self.assertEqual(post_unauth.status_code, 302)
        self.assertIn(reverse('accounts:login'), post_unauth.url)

        # 3. Authenticated POST creates an inactive (pending) business
        self.client.force_login(self.owner_user)
        post_auth = self.client.post(reverse('businesses:submit'), {
            'title': 'Authentic Lahori Sweets',
            'category': self.biz_cat.pk,
            'locality': self.locality.pk,
            'address': 'Liberty Market Gulberg',
            'summary': 'Traditional Lahori halwa puri and mithai.',
            'description': 'Serving authentic fresh sweets for generations.',
            'phone': '+924235750000',
        })
        self.assertRedirects(post_auth, reverse('businesses:dashboard'))
        created_biz = Business.objects.filter(title='Authentic Lahori Sweets').first()
        self.assertIsNotNone(created_biz)
        self.assertFalse(created_biz.is_active, "New submission must remain unpublished (is_active=False)")
        self.assertEqual(created_biz.verification_status, 'pending')
        self.assertEqual(created_biz.submitted_by, self.owner_user)

    # =========================================================================
    # 8. ADMIN WORKFLOWS
    # =========================================================================

    def test_admin_workflows(self):
        """Verify superuser can log in, view admin index and business changelist."""
        # Non-staff cannot view admin
        self.client.force_login(self.member_user)
        forbidden_admin = self.client.get('/admin/')
        # Django admin redirects non-staff to admin login
        self.assertEqual(forbidden_admin.status_code, 302)

        # Superuser can access admin index
        self.client.force_login(self.admin_user)
        admin_index = self.client.get('/admin/')
        self.assertEqual(admin_index.status_code, 200)

        # Superuser can access Business changelist
        biz_changelist = self.client.get('/admin/businesses/business/')
        self.assertEqual(biz_changelist.status_code, 200)
        self.assertContains(biz_changelist, 'Punjab Green Solar Systems')

    # =========================================================================
    # 9. NAVIGATION, HOMEPAGE & MOBILE RESPONSIVENESS
    # =========================================================================

    def test_navigation_and_mobile_responsiveness(self):
        """Verify mobile viewport meta tag, responsive navigation elements, and layout containers."""
        resp = self.client.get(reverse('core:home'))
        self.assertEqual(resp.status_code, 200)

        html = resp.content.decode('utf-8')
        # Viewport meta tag for mobile devices
        self.assertIn('<meta name="viewport" content="width=device-width', html)

        # Navigation elements
        self.assertIn('navbar-toggler', html)
        self.assertIn('Lahore City Hub', html)

        # Core navigation category links
        self.assertIn(reverse('businesses:list'), html)
        self.assertIn(reverse('places:list'), html)
        self.assertIn(reverse('restaurants:list'), html)
        self.assertIn(reverse('hospitals:list'), html)

    # =========================================================================
    # 10. CUSTOM ERROR HANDLERS (404, 403, 400)
    # =========================================================================

    def test_custom_error_pages_render_cleanly(self):
        """Verify branded custom error pages for 404 and preview routes."""
        # Non-existent page returns 404
        not_found = self.client.get('/definitely-non-existent-page-slug-xyz/')
        self.assertEqual(not_found.status_code, 404)
        self.assertContains(not_found, 'Page Not Found', status_code=404)

        # Preview 404
        preview_404 = self.client.get('/404-preview/')
        self.assertEqual(preview_404.status_code, 404)


class EmptyDatabaseStateTests(TestCase):
    """
    Tests ensuring that all directory listing pages and search endpoints
    handle an empty database gracefully without 500 errors or broken markup.
    """
    def setUp(self):
        self.client = Client()

    def test_empty_database_listings_render_gracefully(self):
        """Ensure all directory endpoints return 200 even when zero records exist."""
        endpoints = [
            reverse('core:home'),
            reverse('core:directory_index'),
            reverse('core:search'),
            reverse('places:list'),
            reverse('restaurants:list'),
            reverse('hospitals:list'),
            reverse('education:list'),
            reverse('jobs:list'),
            reverse('businesses:list'),
            reverse('events:list'),
            reverse('transport:overview'),
            reverse('transport:route_list'),
            reverse('transport:station_list'),
            reverse('transport:guide_list'),
        ]
        for url in endpoints:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200, f"Empty database listing {url} failed with {response.status_code}")

        # Empty database updates endpoint cleanly redirects to homepage
        updates_resp = self.client.get(reverse('updates:list'))
        self.assertRedirects(updates_resp, reverse('core:home'))
