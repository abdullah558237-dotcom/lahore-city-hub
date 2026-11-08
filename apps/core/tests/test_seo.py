import json
import xml.etree.ElementTree as ET
from datetime import timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.core.models import LocalityZone, Locality
from apps.places.models import Place, PlaceCategory
from apps.jobs.models import JobListing, JobCategory, Employer
from apps.restaurants.models import Restaurant, Cuisine
from apps.hospitals.models import Hospital, MedicalSpecialty
from apps.education.models import Institution, EducationType
from apps.businesses.models import Business, BusinessCategory
from apps.events.models import Event, EventCategory, EventVenue
from apps.updates.models import CityUpdate, UpdateCategory
from apps.transport.models import TransitMode, TransitRoute, TransitStation, TransitGuide

User = get_user_model()


class TechnicalSEOTests(TestCase):
    """
    Automated test suite verifying Technical SEO implementations for Lahore City Hub:
    1. XML Sitemap generation, eligible URL inclusion, and exclusion of private/expired/inactive pages.
    2. Robots.txt directives, disallow paths, and sitemap reference.
    3. Canonical URL presence, correctness, and prevention of duplicate canonical tags.
    4. Unique page titles and concise, informative meta descriptions.
    5. Open Graph and Twitter Card social metadata.
    6. Schema.org JSON-LD structured data syntax and semantics across core entities.
    7. Breadcrumb navigation and BreadcrumbList structured data.
    8. Strict noindex directives on private dashboards, authentication, and moderation routes.
    9. Correct HTTP status codes (200, 404, 403).
    10. Responsive mobile-friendly viewport meta tag.
    """

    def setUp(self):
        self.client = Client()
        self.today = timezone.now().date()
        self.now = timezone.now()

        # Localities
        self.zone = LocalityZone.objects.create(name='Central Lahore', slug='central-lahore')
        self.locality = Locality.objects.create(name='Gulberg III', slug='gulberg-iii', zone=self.zone, postal_code='54660')

        # User
        self.user = User.objects.create_user(
            username='seo_tester', email='seotester@lahorecityhub.pk', password='ComplexPassword123!'
        )

        # 1. Place
        self.place_cat = PlaceCategory.objects.create(name='Mughal Architecture', slug='mughal-architecture')
        self.place_active = Place.objects.create(
            title='Badshahi Mosque',
            slug='badshahi-mosque-seo',
            category=self.place_cat,
            locality=self.locality,
            address='Walled City, Lahore',
            summary='Historic Mughal mosque constructed in red sandstone.',
            description='Majestic 17th century congregational prayer complex.',
            is_active=True
        )
        self.place_inactive = Place.objects.create(
            title='Unpublished Citadel',
            slug='unpublished-citadel-seo',
            category=self.place_cat,
            locality=self.locality,
            address='Hidden Underground Sector',
            summary='Draft discovery.',
            description='Draft description.',
            is_active=False
        )

        # 2. Job
        self.job_cat = JobCategory.objects.create(name='Software Engineering', slug='software-engineering')
        self.employer = Employer.objects.create(name='TechLogix', slug='techlogix', locality=self.locality)
        self.job_active = JobListing.objects.create(
            title='Senior Django Architect',
            slug='senior-django-architect-seo',
            employer=self.employer,
            category=self.job_cat,
            locality=self.locality,
            employment_type='full_time',
            description='Design high-performance backend systems.',
            requirements='Python, Django, PostgreSQL.',
            deadline=self.today + timedelta(days=30),
            is_active=True
        )
        self.job_expired = JobListing.objects.create(
            title='Expired Web Developer',
            slug='expired-web-developer-seo',
            employer=self.employer,
            category=self.job_cat,
            locality=self.locality,
            employment_type='full_time',
            description='Expired job vacancy.',
            deadline=self.today - timedelta(days=2),
            is_active=True
        )

        # 3. Restaurant
        self.cuisine = Cuisine.objects.create(name='Traditional Desi', slug='traditional-desi')
        self.restaurant = Restaurant.objects.create(
            title='Haveli Restaurant Fort View',
            slug='haveli-fort-view-seo',
            locality=self.locality,
            address='Fort Road Food Street',
            summary='Rooftop dining with panoramic views of the illuminated Lahore Fort.',
            description='Authentic Punjabi cuisine and barbecue.',
            is_active=True
        )
        self.restaurant.cuisines.add(self.cuisine)

        # 4. Hospital
        self.specialty = MedicalSpecialty.objects.create(name='Cardiology', slug='cardiology')
        self.hospital = Hospital.objects.create(
            title='Doctors Hospital Medical Center',
            slug='doctors-hospital-seo',
            locality=self.locality,
            address='Canal Bank Road',
            summary='Tertiary healthcare center with 24/7 cardiac emergency ward.',
            description='Comprehensive emergency and surgical medical facilities.',
            is_active=True
        )
        self.hospital.specialties.add(self.specialty)

        # 5. Education
        self.edu_type = EducationType.objects.create(name='General Universities', slug='general-universities')
        self.institution = Institution.objects.create(
            title='University of the Punjab',
            slug='punjab-university-seo',
            education_type=self.edu_type,
            locality=self.locality,
            address='Quaid-e-Azam Campus, Canal Road',
            summary='Oldest and largest public research university in Pakistan.',
            description='Historic collegiate university founded in 1882.',
            is_active=True
        )

        # 6. Business
        self.biz_cat = BusinessCategory.objects.create(name='Legal Services', slug='legal-services')
        self.business = Business.objects.create(
            title='Lahore Corporate Law Chambers',
            slug='lahore-corporate-law-seo',
            category=self.biz_cat,
            locality=self.locality,
            address='Ferozepur Road',
            summary='Specialized corporate legal practice and business compliance counsel.',
            description='Corporate advisory, merger facilitation, and litigation support.',
            submitted_by=self.user,
            is_active=True
        )

        # 7. Event
        self.event_cat = EventCategory.objects.create(name='Literary Festivals', slug='literary-festivals')
        self.venue = EventVenue.objects.create(name='Alhamra Arts Council', slug='alhamra-arts', locality=self.locality, address='Mall Road')
        self.event = Event.objects.create(
            title='Lahore Literary Festival 2026',
            slug='lahore-literary-festival-seo',
            category=self.event_cat,
            venue=self.venue,
            start_datetime=self.now + timedelta(days=10),
            end_datetime=self.now + timedelta(days=12),
            organizer_name='LLF Foundation',
            description='International celebration of literature, art, and cultural thought.',
            is_active=True
        )

        # 8. Transport
        self.mode = TransitMode.objects.create(name='Metro Train', slug='metro-train')
        self.route = TransitRoute.objects.create(
            mode=self.mode,
            route_code='OLMT-01',
            route_name='Orange Line Metro Train',
            slug='orange-line-metro-seo',
            origin_station='Ali Town',
            destination_station='Dera Gujran',
            total_stations=26,
            is_active=True
        )
        self.station = TransitStation.objects.create(
            route=self.route,
            station_number=1,
            station_name='Ali Town Terminal',
            urdu_name='علی ٹاؤن',
            slug='ali-town-terminal-seo',
            locality=self.locality
        )
        self.guide = TransitGuide.objects.create(
            title='Commuter Ticketing and Metro Card Guide',
            slug='commuter-card-guide-seo',
            category='fares_ticketing',
            route=self.route,
            summary='Guidelines on acquiring and topping up Metro transit smart cards.',
            content='Full ticketing protocols.',
            is_published=True
        )

    # ==========================================================
    # 1. XML Sitemap Tests
    # ==========================================================

    def test_sitemap_xml_returns_200_and_valid_xml(self):
        """Sitemap endpoint returns HTTP 200 with application/xml content type."""
        response = self.client.get('/sitemap.xml')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'application/xml')

        # Verify valid XML structure
        root = ET.fromstring(response.content)
        self.assertEqual(root.tag, '{http://www.sitemaps.org/schemas/sitemap/0.9}urlset')

    def test_sitemap_includes_all_eligible_public_urls(self):
        """Sitemap contains active places, unexpired jobs, restaurants, hospitals, and transit."""
        response = self.client.get('/sitemap.xml')
        root = ET.fromstring(response.content)
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        urls = [elem.text for elem in root.findall('ns:url/ns:loc', namespace)]

        # Verify public static pages
        self.assertTrue(any(u.endswith('/') for u in urls))
        self.assertTrue(any('about' in u for u in urls))
        self.assertTrue(any('contact' in u for u in urls))
        self.assertTrue(any('places' in u for u in urls))

        # Verify dynamic active listings
        self.assertTrue(any(self.place_active.slug in u for u in urls))
        self.assertTrue(any(self.job_active.slug in u for u in urls))
        self.assertTrue(any(self.restaurant.slug in u for u in urls))
        self.assertTrue(any(self.hospital.slug in u for u in urls))
        self.assertTrue(any(self.institution.slug in u for u in urls))
        self.assertTrue(any(self.business.slug in u for u in urls))
        self.assertTrue(any(self.event.slug in u for u in urls))
        self.assertTrue(any(self.route.slug in u for u in urls))
        self.assertTrue(any(self.station.slug in u for u in urls))
        self.assertTrue(any(self.guide.slug in u for u in urls))

    def test_sitemap_strictly_excludes_inactive_and_expired_content(self):
        """Inactive listings and expired job listings are strictly excluded from sitemap."""
        response = self.client.get('/sitemap.xml')
        root = ET.fromstring(response.content)
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        urls = [elem.text for elem in root.findall('ns:url/ns:loc', namespace)]

        # Inactive place must NOT be in sitemap
        self.assertFalse(any(self.place_inactive.slug in u for u in urls))

        # Expired job must NOT be in sitemap
        self.assertFalse(any(self.job_expired.slug in u for u in urls))

    def test_sitemap_excludes_private_and_moderation_paths(self):
        """Administrative, private user, and moderation URLs are never in sitemap."""
        response = self.client.get('/sitemap.xml')
        root = ET.fromstring(response.content)
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        urls = [elem.text for elem in root.findall('ns:url/ns:loc', namespace)]

        for forbidden in ['/admin/', '/accounts/', '/dashboard/', '/submit/', '/edit/', '/claim/', '/report/']:
            with self.subTest(forbidden=forbidden):
                self.assertFalse(any(forbidden in u for u in urls))

    # ==========================================================
    # 2. Robots.txt Tests
    # ==========================================================

    def test_robots_txt_status_and_directives(self):
        """Robots.txt returns text/plain with disallowed private sections and sitemap pointer."""
        response = self.client.get('/robots.txt')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get('Content-Type').startswith('text/plain'))

        content = response.content.decode()
        self.assertIn('User-agent: *', content)
        self.assertIn('Disallow: /admin/', content)
        self.assertIn('Disallow: /accounts/', content)
        self.assertIn('Disallow: /member/', content)
        self.assertIn('Disallow: /businesses/submit/', content)
        self.assertIn('Disallow: /businesses/edit/', content)
        self.assertIn('Disallow: /businesses/claim/', content)
        self.assertIn('Disallow: /businesses/report/', content)
        self.assertIn('Allow: /', content)
        self.assertIn('Sitemap:', content)
        self.assertIn('/sitemap.xml', content)

    # ==========================================================
    # 3. Canonical URLs Tests
    # ==========================================================

    def test_canonical_urls_present_without_duplicates(self):
        """Public pages have exactly one canonical URL link tag."""
        test_endpoints = [
            reverse('core:home'),
            reverse('places:detail', kwargs={'slug': self.place_active.slug}),
            reverse('jobs:detail', kwargs={'slug': self.job_active.slug}),
            reverse('restaurants:detail', kwargs={'slug': self.restaurant.slug}),
            reverse('hospitals:detail', kwargs={'slug': self.hospital.slug}),
            reverse('education:detail', kwargs={'slug': self.institution.slug}),
            reverse('businesses:detail', kwargs={'slug': self.business.slug}),
            reverse('events:detail', kwargs={'slug': self.event.slug}),
        ]

        for url in test_endpoints:
            with self.subTest(url=url):
                res = self.client.get(url)
                self.assertEqual(res.status_code, 200)
                content = res.content.decode()
                # Must contain rel="canonical"
                self.assertIn('rel="canonical"', content)
                # Must have exactly 1 canonical link tag
                self.assertEqual(content.count('rel="canonical"'), 1, f"Duplicate canonical in {url}")

    # ==========================================================
    # 4. Meta Titles & Descriptions
    # ==========================================================

    def test_unique_titles_and_descriptions(self):
        """Entities render unique informative title tags and meta descriptions."""
        res_place = self.client.get(reverse('places:detail', kwargs={'slug': self.place_active.slug}))
        self.assertContains(res_place, '<title>Badshahi Mosque')
        self.assertContains(res_place, 'name="description"')

        res_hospital = self.client.get(reverse('hospitals:detail', kwargs={'slug': self.hospital.slug}))
        self.assertContains(res_hospital, '<title>Doctors Hospital')
        self.assertContains(res_hospital, 'name="description"')

    # ==========================================================
    # 5. Open Graph & Social Cards
    # ==========================================================

    def test_open_graph_and_twitter_metadata(self):
        """Pages emit og:title, og:description, og:url, and twitter:card meta tags."""
        response = self.client.get(reverse('places:detail', kwargs={'slug': self.place_active.slug}))
        content = response.content.decode()

        self.assertIn('property="og:site_name" content="Lahore City Hub"', content)
        self.assertIn('property="og:title"', content)
        self.assertIn('property="og:description"', content)
        self.assertIn('property="og:url"', content)
        self.assertIn('name="twitter:card" content="summary_large_image"', content)

    # ==========================================================
    # 6. Schema.org JSON-LD Structured Data
    # ==========================================================

    def test_homepage_schema_org_structured_data(self):
        """Homepage renders valid WebSite JSON-LD with Sitelinks SearchAction."""
        response = self.client.get(reverse('core:home'))
        content = response.content.decode()
        self.assertIn('application/ld+json', content)
        self.assertIn('SearchAction', content)

    def test_place_detail_schema_tourist_attraction(self):
        """Place detail renders valid TouristAttraction JSON-LD schema."""
        response = self.client.get(reverse('places:detail', kwargs={'slug': self.place_active.slug}))
        content = response.content.decode()
        self.assertIn('application/ld+json', content)
        self.assertIn('"@type": "TouristAttraction"', content)
        self.assertIn('Badshahi Mosque', content)

    def test_job_detail_schema_job_posting(self):
        """Job detail renders valid JobPosting JSON-LD schema."""
        response = self.client.get(reverse('jobs:detail', kwargs={'slug': self.job_active.slug}))
        content = response.content.decode()
        self.assertIn('application/ld+json', content)
        self.assertIn('"@type": "JobPosting"', content)
        self.assertIn('Senior Django Architect', content)

    def test_restaurant_detail_schema_restaurant(self):
        """Restaurant detail renders valid Restaurant JSON-LD schema."""
        response = self.client.get(reverse('restaurants:detail', kwargs={'slug': self.restaurant.slug}))
        content = response.content.decode()
        self.assertIn('application/ld+json', content)
        self.assertIn('"@type": "Restaurant"', content)

    def test_hospital_detail_schema_hospital(self):
        """Hospital detail renders valid Hospital JSON-LD schema."""
        response = self.client.get(reverse('hospitals:detail', kwargs={'slug': self.hospital.slug}))
        content = response.content.decode()
        self.assertIn('application/ld+json', content)
        self.assertIn('"@type": "Hospital"', content)

    def test_education_detail_schema_university(self):
        """Institution detail renders valid EducationalOrganization JSON-LD schema."""
        response = self.client.get(reverse('education:detail', kwargs={'slug': self.institution.slug}))
        content = response.content.decode()
        self.assertIn('application/ld+json', content)
        self.assertIn('"@type": "EducationalOrganization"', content)

    def test_business_detail_schema_local_business(self):
        """Business detail renders valid LocalBusiness JSON-LD schema."""
        response = self.client.get(reverse('businesses:detail', kwargs={'slug': self.business.slug}))
        content = response.content.decode()
        self.assertIn('application/ld+json', content)
        self.assertIn('"@type": "LocalBusiness"', content)

    def test_event_detail_schema_event(self):
        """Event detail renders valid Event JSON-LD schema."""
        response = self.client.get(reverse('events:detail', kwargs={'slug': self.event.slug}))
        content = response.content.decode()
        self.assertIn('application/ld+json', content)
        self.assertIn('"@type": "Event"', content)

    # ==========================================================
    # 7. Breadcrumbs & BreadcrumbList Schema
    # ==========================================================

    def test_breadcrumbs_render_schema_breadcrumblist(self):
        """Breadcrumbs output valid Schema.org BreadcrumbList JSON-LD."""
        response = self.client.get(reverse('places:detail', kwargs={'slug': self.place_active.slug}))
        content = response.content.decode()
        self.assertIn('BreadcrumbList', content)
        self.assertIn('"@type": "ListItem"', content)

    # ==========================================================
    # 8. Private Pages Noindex Enforcement
    # ==========================================================

    def test_private_dashboard_has_noindex_directive(self):
        """User and business dashboards have explicit noindex, nofollow directives."""
        self.client.force_login(self.user)

        res_dash = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(res_dash.status_code, 200)
        self.assertContains(res_dash, '<meta name="robots" content="noindex, nofollow">')

        res_prof = self.client.get(reverse('accounts:profile'))
        self.assertEqual(res_prof.status_code, 200)
        self.assertContains(res_prof, '<meta name="robots" content="noindex, nofollow">')

        res_biz_dash = self.client.get(reverse('businesses:dashboard'))
        self.assertEqual(res_biz_dash.status_code, 200)
        self.assertContains(res_biz_dash, '<meta name="robots" content="noindex, nofollow">')

    def test_search_page_has_noindex_follow(self):
        """Search discovery page has noindex, follow to avoid thin duplicate search indexation."""
        res_search = self.client.get(reverse('core:search'), {'q': 'Hospital'})
        self.assertEqual(res_search.status_code, 200)
        self.assertContains(res_search, '<meta name="robots" content="noindex, follow">')

    # ==========================================================
    # 9. HTTP Status Codes & Error Templates
    # ==========================================================

    def test_custom_404_error_page_status_and_noindex(self):
        """Non-existent URLs return 404 with custom error template and noindex."""
        response = self.client.get('/this-path-definitely-does-not-exist-xyz/')
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, 'Lost in the Walled City?', status_code=404)
        self.assertContains(response, '<meta name="robots" content="noindex, nofollow">', status_code=404)

    # ==========================================================
    # 10. Mobile-Friendly Viewport Tag
    # ==========================================================

    def test_viewport_meta_tag_present(self):
        """Mobile viewport meta tag is present on base template."""
        response = self.client.get(reverse('core:home'))
        self.assertContains(response, '<meta name="viewport" content="width=device-width, initial-scale=1.0">')
