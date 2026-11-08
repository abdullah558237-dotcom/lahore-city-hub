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

User = get_user_model()


class GlobalSearchEngineTests(TestCase):
    """
    Comprehensive automated test suite for Lahore City Hub Global Search.
    Verifies:
    1. Search accuracy across all 8 eligible content domains (Places, Jobs, Restaurants, Hospitals,
       Education, Businesses, Events, City Updates).
    2. Case-insensitivity across titles, summaries, descriptions, and categories.
    3. Strict exclusion of unpublished, inactive, and expired records.
    4. Privacy protection against leakage of user emails and internal verification notes.
    5. Category-specific filtering and hit counts.
    6. Area / locality filtering.
    7. Query validation, sanitization, and invalid input safety.
    8. User-friendly no-results empty state.
    9. Multi-page pagination and filter query string preservation.
    """

    def setUp(self):
        self.client = Client()
        self.today = timezone.now().date()
        self.now = timezone.now()

        # Localities
        self.zone_central = LocalityZone.objects.create(name='Central Lahore', slug='central-lahore')
        self.zone_east = LocalityZone.objects.create(name='East Lahore', slug='east-lahore')

        self.loc_gulberg = Locality.objects.create(
            name='Gulberg III', slug='gulberg-iii', zone=self.zone_central, postal_code='54660'
        )
        self.loc_walled_city = Locality.objects.create(
            name='Walled City', slug='walled-city', zone=self.zone_central, postal_code='54000'
        )
        self.loc_dha = Locality.objects.create(
            name='DHA Phase 5', slug='dha-phase-5', zone=self.zone_east, postal_code='54792'
        )

        # Users
        self.owner_user = User.objects.create_user(
            username='corporate_owner',
            email='confidential_owner_789@packagesgroup.pk',
            password='ComplexSecretPassword2026!'
        )

        # 1. Place
        self.place_cat = PlaceCategory.objects.create(name='Mughal Heritage Sites', slug='mughal-heritage')
        self.place_active = Place.objects.create(
            title='Badshahi Mosque Complex',
            slug='badshahi-mosque-complex',
            category=self.place_cat,
            locality=self.loc_walled_city,
            address='Walled City of Lahore',
            summary='Magnificent red sandstone congregational mosque.',
            description='Built in 1673 by Mughal Emperor Aurangzeb.',
            verification_status='verified',
            verification_notes='INTERNAL_AUDIT_CONFIDENTIAL_NOTES_ALPHA',
            is_active=True
        )
        self.place_inactive = Place.objects.create(
            title='Secret Underground Citadel',
            slug='secret-underground-citadel',
            category=self.place_cat,
            locality=self.loc_walled_city,
            address='Restricted Access Zone',
            summary='Unpublished subterranean chamber.',
            description='Draft historical findings.',
            is_active=False
        )

        # 2. Job
        self.job_cat = JobCategory.objects.create(name='Engineering & Architecture', slug='engineering-architecture')
        self.employer = Employer.objects.create(name='Arbisoft Lahore', slug='arbisoft-lahore', locality=self.loc_gulberg)
        self.job_active = JobListing.objects.create(
            title='Lead Python Architect',
            slug='lead-python-architect',
            employer=self.employer,
            category=self.job_cat,
            locality=self.loc_gulberg,
            employment_type='full_time',
            description='Design scalable web platforms and search APIs.',
            requirements='Python, Django, PostgreSQL, caching.',
            deadline=self.today + timedelta(days=25),
            is_active=True
        )
        self.job_expired = JobListing.objects.create(
            title='Expired DevOps Specialist',
            slug='expired-devops-specialist',
            employer=self.employer,
            category=self.job_cat,
            locality=self.loc_gulberg,
            employment_type='contract',
            description='Infrastructure role with closed deadline.',
            requirements='Docker, Kubernetes.',
            deadline=self.today - timedelta(days=5),
            is_active=True
        )
        self.job_inactive = JobListing.objects.create(
            title='Confidential Security Auditor',
            slug='confidential-security-auditor',
            employer=self.employer,
            category=self.job_cat,
            locality=self.loc_gulberg,
            employment_type='full_time',
            description='Internal draft listing.',
            deadline=self.today + timedelta(days=20),
            is_active=False
        )

        # 3. Restaurant
        self.cuisine_bbq = Cuisine.objects.create(name='Traditional Mughlai BBQ', slug='traditional-mughlai-bbq')
        self.restaurant_active = Restaurant.objects.create(
            title='Haveli Restaurant Fort View',
            slug='haveli-restaurant-fort-view',
            locality=self.loc_walled_city,
            address='Fort Road Food Street',
            summary='Rooftop dining with panoramic vistas of the illuminated Lahore Fort.',
            description='Authentic Punjabi cuisine and grilled kebabs.',
            is_active=True
        )
        self.restaurant_active.cuisines.add(self.cuisine_bbq)

        self.restaurant_inactive = Restaurant.objects.create(
            title='Hidden Speakeasy Diner',
            slug='hidden-speakeasy-diner',
            locality=self.loc_gulberg,
            address='Secret Basement Suite',
            summary='Unlicensed private club.',
            description='Private tasting club.',
            is_active=False
        )

        # 4. Hospital
        self.specialty_cardio = MedicalSpecialty.objects.create(name='Interventional Cardiology', slug='cardiology')
        self.hospital_active = Hospital.objects.create(
            title='Doctors Hospital Medical Center',
            slug='doctors-hospital-medical-center',
            locality=self.loc_gulberg,
            address='Canal Bank Road',
            summary='Tertiary healthcare center with 24/7 cardiac emergency ward.',
            description='Comprehensive surgical and diagnostic facilities.',
            is_active=True
        )
        self.hospital_active.specialties.add(self.specialty_cardio)

        self.hospital_inactive = Hospital.objects.create(
            title='Proposed Medicity Hospital',
            slug='proposed-medicity-hospital',
            locality=self.loc_dha,
            address='Proposed Boulevard',
            summary='Under-construction facility.',
            description='Not yet operational.',
            is_active=False
        )

        # 5. Education
        self.edu_type = EducationType.objects.create(name='Chartered Universities', slug='chartered-universities')
        self.institution_active = Institution.objects.create(
            title='Forman Christian College University',
            slug='forman-christian-college',
            education_type=self.edu_type,
            locality=self.loc_gulberg,
            address='Zahir Pir Road, Gulberg',
            summary='Historic collegiate university offering baccalaureate programs.',
            description='Renowned faculty and expansive lush campus.',
            is_active=True
        )
        self.institution_inactive = Institution.objects.create(
            title='Unregistered Coaching Academy',
            slug='unregistered-coaching-academy',
            education_type=self.edu_type,
            locality=self.loc_gulberg,
            address='Commercial Alley',
            summary='Unaccredited center.',
            description='Draft institution.',
            is_active=False
        )

        # 6. Business
        self.biz_cat = BusinessCategory.objects.create(name='Manufacturing & Printing', slug='manufacturing-printing')
        self.business_active = Business.objects.create(
            title='Packages Limited Industrial Complex',
            slug='packages-limited-complex',
            category=self.biz_cat,
            locality=self.loc_gulberg,
            address='Shahrah-e-Roomi, Gulberg',
            summary='Premier packaging and consumer goods manufacturing plant.',
            description='Pioneering corporate packaging solutions across Pakistan.',
            submitted_by=self.owner_user,
            is_active=True
        )
        self.business_inactive = Business.objects.create(
            title='Unlicensed Pawn Shop',
            slug='unlicensed-pawn-shop',
            category=self.biz_cat,
            locality=self.loc_gulberg,
            address='Shady Corner',
            summary='Pending registration business.',
            description='Awaiting approval.',
            is_active=False
        )

        # 7. Event
        self.event_cat = EventCategory.objects.create(name='Literary & Cultural Festivals', slug='literary-cultural')
        self.venue = EventVenue.objects.create(
            name='Alhamra Arts Council', slug='alhamra-arts-council', locality=self.loc_gulberg, address='Mall Road'
        )
        self.event_active = Event.objects.create(
            title='Lahore Literary Festival 2026',
            slug='lahore-literary-festival-2026',
            category=self.event_cat,
            venue=self.venue,
            start_datetime=self.now + timedelta(days=10),
            end_datetime=self.now + timedelta(days=12),
            organizer_name='LLF Foundation Secretariat',
            description='International authors, book launches, and cultural dialogues.',
            is_active=True
        )
        self.event_inactive = Event.objects.create(
            title='Cancelled Midnight Rave',
            slug='cancelled-midnight-rave',
            category=self.event_cat,
            venue=self.venue,
            start_datetime=self.now + timedelta(days=2),
            end_datetime=self.now + timedelta(days=3),
            organizer_name='Private Club',
            description='Unlicensed party cancelled by authorities.',
            is_active=False
        )

        # 8. City Update
        self.update_cat = UpdateCategory.objects.create(name='Environmental & Air Quality', slug='environmental-air-quality')
        self.update_active = CityUpdate.objects.create(
            title='EPA Winter Smog Traffic Advisory',
            slug='epa-winter-smog-traffic-advisory',
            category=self.update_cat,
            severity='caution',
            summary='Air quality index warning urging vehicular restrictions along Ring Road.',
            content='Punjab Environment Protection Agency protocols for school timings and commercial closures.',
            issuing_authority='Punjab EPA Directorate',
            official_source_url='https://epa.punjab.gov.pk/circular-2026-smog',
            is_pinned=True,
            is_active=True
        )
        self.update_inactive = CityUpdate.objects.create(
            title='Internal Draft City Notice',
            slug='internal-draft-city-notice',
            category=self.update_cat,
            severity='info',
            summary='Draft notice under editorial review.',
            content='Confidential municipal circular.',
            issuing_authority='City District Government',
            is_active=False
        )

    # ==========================================================
    # 1. Search Accuracy Across All 8 Models
    # ==========================================================

    def test_search_locates_places_accurately(self):
        """Places are searchable by title, historical keywords, or category."""
        res = self.client.get(reverse('core:search'), {'q': 'Badshahi'})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Badshahi Mosque Complex')
        self.assertEqual(res.context['places_count'], 1)

    def test_search_locates_jobs_accurately(self):
        """Active jobs are searchable by title, employer, or requirements."""
        res = self.client.get(reverse('core:search'), {'q': 'Arbisoft'})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Lead Python Architect')
        self.assertContains(res, 'Arbisoft Lahore')

    def test_search_locates_restaurants_accurately(self):
        """Restaurants are searchable by title, location, or cuisine."""
        res = self.client.get(reverse('core:search'), {'q': 'Haveli'})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Haveli Restaurant Fort View')

    def test_search_locates_hospitals_accurately(self):
        """Hospitals are searchable by name, address, or medical specialties."""
        res = self.client.get(reverse('core:search'), {'q': 'Cardiology'})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Doctors Hospital Medical Center')

    def test_search_locates_education_accurately(self):
        """Educational institutions are searchable by title or degree type."""
        res = self.client.get(reverse('core:search'), {'q': 'Forman'})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Forman Christian College University')

    def test_search_locates_businesses_accurately(self):
        """Local businesses are searchable by commercial title or category."""
        res = self.client.get(reverse('core:search'), {'q': 'Packages Limited'})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Packages Limited Industrial Complex')

    def test_search_locates_events_accurately(self):
        """Events are searchable by event title, organizer, or venue."""
        res = self.client.get(reverse('core:search'), {'q': 'Literary Festival'})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Lahore Literary Festival 2026')

    def test_search_locates_city_updates_accurately(self):
        """City updates are searchable by advisory title or authority."""
        res = self.client.get(reverse('core:search'), {'q': 'Smog Traffic'})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'EPA Winter Smog Traffic Advisory')

    # ==========================================================
    # 2. Case-Insensitive Matching
    # ==========================================================

    def test_search_is_case_insensitive(self):
        """Query terms match case-insensitively across upper, lower, and mixed case."""
        # Lowercase
        res_lower = self.client.get(reverse('core:search'), {'q': 'badshahi'})
        self.assertContains(res_lower, 'Badshahi Mosque Complex')

        # Uppercase
        res_upper = self.client.get(reverse('core:search'), {'q': 'DOCTORS'})
        self.assertContains(res_upper, 'Doctors Hospital Medical Center')

        # Mixed Case
        res_mixed = self.client.get(reverse('core:search'), {'q': 'aRbIsOfT'})
        self.assertContains(res_mixed, 'Lead Python Architect')

    # ==========================================================
    # 3. Exclusion of Unpublished, Inactive, and Expired Records
    # ==========================================================

    def test_inactive_and_unpublished_records_strictly_excluded(self):
        """Unpublished/inactive records are strictly filtered out of search results."""
        # Inactive Place
        res_place = self.client.get(reverse('core:search'), {'q': 'Citadel'})
        self.assertEqual(res_place.context['total_hits'], 0)
        self.assertNotIn(self.place_inactive, res_place.context['page_obj'])

        # Inactive Restaurant
        res_rest = self.client.get(reverse('core:search'), {'q': 'Speakeasy'})
        self.assertEqual(res_rest.context['total_hits'], 0)
        self.assertNotIn(self.restaurant_inactive, res_rest.context['page_obj'])

        # Inactive Hospital
        res_hosp = self.client.get(reverse('core:search'), {'q': 'Medicity'})
        self.assertEqual(res_hosp.context['total_hits'], 0)
        self.assertNotIn(self.hospital_inactive, res_hosp.context['page_obj'])

        # Inactive Education
        res_edu = self.client.get(reverse('core:search'), {'q': 'Unregistered Coaching'})
        self.assertEqual(res_edu.context['total_hits'], 0)
        self.assertNotIn(self.institution_inactive, res_edu.context['page_obj'])

        # Inactive Business
        res_biz = self.client.get(reverse('core:search'), {'q': 'Pawn Shop'})
        self.assertEqual(res_biz.context['total_hits'], 0)
        self.assertNotIn(self.business_inactive, res_biz.context['page_obj'])

        # Inactive Event
        res_event = self.client.get(reverse('core:search'), {'q': 'Midnight Rave'})
        self.assertEqual(res_event.context['total_hits'], 0)
        self.assertNotIn(self.event_inactive, res_event.context['page_obj'])

        # Inactive City Update
        res_update = self.client.get(reverse('core:search'), {'q': 'Internal Draft'})
        self.assertEqual(res_update.context['total_hits'], 0)
        self.assertNotIn(self.update_inactive, res_update.context['page_obj'])

    def test_expired_and_inactive_jobs_excluded(self):
        """Jobs past deadline or marked inactive are not returned in global search."""
        res_expired = self.client.get(reverse('core:search'), {'q': 'DevOps Specialist'})
        self.assertEqual(res_expired.context['total_hits'], 0)
        self.assertNotIn(self.job_expired, res_expired.context['page_obj'])

        res_inactive = self.client.get(reverse('core:search'), {'q': 'Security Auditor'})
        self.assertEqual(res_inactive.context['total_hits'], 0)
        self.assertNotIn(self.job_inactive, res_inactive.context['page_obj'])

    # ==========================================================
    # 4. Protection of User Privacy and Internal Audit Data
    # ==========================================================

    def test_private_user_emails_never_searchable_or_exposed(self):
        """Private business submitter email addresses are never searchable or leaked."""
        res_email = self.client.get(reverse('core:search'), {'q': 'confidential_owner_789'})
        self.assertEqual(res_email.context['total_hits'], 0)
        self.assertNotContains(res_email, 'confidential_owner_789@packagesgroup.pk')

        res_domain = self.client.get(reverse('core:search'), {'q': 'packagesgroup.pk'})
        self.assertEqual(res_domain.context['total_hits'], 0)

    def test_internal_verification_audit_notes_never_searchable(self):
        """Internal editorial audit notes are protected from public search queries."""
        res_notes = self.client.get(reverse('core:search'), {'q': 'INTERNAL_AUDIT_CONFIDENTIAL'})
        self.assertEqual(res_notes.context['total_hits'], 0)
        self.assertNotContains(res_notes, 'INTERNAL_AUDIT_CONFIDENTIAL_NOTES_ALPHA')

    # ==========================================================
    # 5. Category-Specific Filters
    # ==========================================================

    def test_category_filter_limits_results_to_specified_domain(self):
        """Category parameter restricts paginated hits to the chosen content type."""
        # Common query matching multiple domains in Lahore
        res_all = self.client.get(reverse('core:search'), {'q': 'Lahore', 'category': 'all'})
        self.assertTrue(res_all.context['total_hits'] >= 3)

        # Filter: Places Only
        res_places = self.client.get(reverse('core:search'), {'q': 'Lahore', 'category': 'places'})
        self.assertEqual(res_places.context['active_category'], 'places')
        for item in res_places.context['page_obj']:
            self.assertEqual(item.item_type, 'place')

        # Filter: Jobs Only
        res_jobs = self.client.get(reverse('core:search'), {'q': 'Lahore', 'category': 'jobs'})
        self.assertEqual(res_jobs.context['active_category'], 'jobs')
        for item in res_jobs.context['page_obj']:
            self.assertEqual(item.item_type, 'job')

        # Filter: Events Only
        res_events = self.client.get(reverse('core:search'), {'q': 'Lahore', 'category': 'events'})
        self.assertEqual(res_events.context['active_category'], 'events')
        for item in res_events.context['page_obj']:
            self.assertEqual(item.item_type, 'event')

        # Filter: Updates Only
        res_updates = self.client.get(reverse('core:search'), {'q': 'Advisory', 'category': 'updates'})
        self.assertEqual(res_updates.context['active_category'], 'updates')
        for item in res_updates.context['page_obj']:
            self.assertEqual(item.item_type, 'update')

    # ==========================================================
    # 6. Area / Locality Filtering
    # ==========================================================

    def test_locality_filter_restricts_geographic_matches(self):
        """Area filter isolates items in the selected locality and excludes others."""
        # Walled City query
        res_walled = self.client.get(reverse('core:search'), {'locality': 'walled-city'})
        self.assertContains(res_walled, 'Badshahi Mosque Complex')
        self.assertContains(res_walled, 'Haveli Restaurant Fort View')
        self.assertNotContains(res_walled, 'Arbisoft Lahore')
        self.assertNotContains(res_walled, 'Doctors Hospital Medical Center')

        # Gulberg query
        res_gulberg = self.client.get(reverse('core:search'), {'locality': 'gulberg-iii'})
        self.assertContains(res_gulberg, 'Lead Python Architect')
        self.assertContains(res_gulberg, 'Doctors Hospital Medical Center')
        self.assertContains(res_gulberg, 'Forman Christian College University')
        self.assertNotContains(res_gulberg, 'Badshahi Mosque Complex')

    def test_city_updates_excluded_when_area_filter_is_active(self):
        """Citywide civic updates without locality are omitted when an area filter is specified."""
        res_loc = self.client.get(reverse('core:search'), {'q': 'Smog', 'locality': 'gulberg-iii'})
        self.assertEqual(res_loc.context['updates_count'], 0)
        self.assertNotContains(res_loc, 'EPA Winter Smog Traffic Advisory')

    # ==========================================================
    # 7. Invalid Input Handling & Sanitization
    # ==========================================================

    def test_excessive_length_query_truncated_safely(self):
        """Huge search queries (over 120 chars) are safely truncated without crashing."""
        long_query = "Hospital" + "A" * 400
        res = self.client.get(reverse('core:search'), {'q': long_query})
        self.assertEqual(res.status_code, 200)
        self.assertTrue(len(res.context['query']) <= 120)

    def test_null_bytes_and_control_characters_stripped(self):
        """Control characters and null bytes are sanitized safely."""
        dirty_query = "Badshahi\x00Mosque\x1f"
        res = self.client.get(reverse('core:search'), {'q': dirty_query})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context['query'], 'BadshahiMosque')

    def test_sql_injection_patterns_handled_safely(self):
        """SQL injection attempts execute safely as plain string literals."""
        malicious_input = "' OR 1=1 --"
        res = self.client.get(reverse('core:search'), {'q': malicious_input})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context['total_hits'], 0)

    def test_invalid_category_falls_back_to_all(self):
        """Unknown or malicious category parameter safely defaults to 'all'."""
        res = self.client.get(reverse('core:search'), {'category': 'hacker_exploit_table'})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context['active_category'], 'all')

    def test_invalid_and_out_of_bounds_pagination(self):
        """Invalid page numbers (strings, negative, high bounds) return valid pages."""
        # Non-integer page -> returns page 1
        res_str = self.client.get(reverse('core:search'), {'page': 'non_integer_page'})
        self.assertEqual(res_str.status_code, 200)
        self.assertEqual(res_str.context['page_obj'].number, 1)

        # Negative page -> returns page 1
        res_neg = self.client.get(reverse('core:search'), {'page': '-99'})
        self.assertEqual(res_neg.status_code, 200)
        self.assertEqual(res_neg.context['page_obj'].number, 1)

        # Out-of-bounds high page -> returns last page
        res_high = self.client.get(reverse('core:search'), {'page': '999999'})
        self.assertEqual(res_high.status_code, 200)
        self.assertTrue(res_high.context['page_obj'].number >= 1)

    # ==========================================================
    # 8. Clear No-Results Message
    # ==========================================================

    def test_clear_no_results_empty_state_rendered(self):
        """Unmatched searches display clear empty state message with filter reset link."""
        res = self.client.get(reverse('core:search'), {'q': 'Z99NonExistentEntityX007'})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context['total_hits'], 0)
        self.assertContains(res, 'No results found')
        self.assertContains(res, 'Reset All Filters')

    # ==========================================================
    # 9. Multi-Page Pagination and Query String Preservation
    # ==========================================================

    def test_pagination_and_query_preservation(self):
        """Pagination breaks large result sets into pages and preserves active search filters."""
        # Create 14 additional places to trigger pagination (15 total, 12 per page)
        for i in range(1, 15):
            Place.objects.create(
                title=f'Lahore Heritage Site {i}',
                slug=f'lahore-heritage-site-{i}',
                category=self.place_cat,
                locality=self.loc_walled_city,
                address=f'{i} Heritage Boulevard',
                summary=f'Historical heritage monument number {i}.',
                description='Protected monument.',
                is_active=True
            )

        # Page 1
        res_p1 = self.client.get(reverse('core:search'), {'q': 'Heritage', 'category': 'places', 'page': '1'})
        self.assertEqual(res_p1.status_code, 200)
        self.assertTrue(res_p1.context['is_paginated'])
        self.assertEqual(len(res_p1.context['page_obj']), 12)
        self.assertTrue(res_p1.context['page_obj'].has_next())
        self.assertFalse(res_p1.context['page_obj'].has_previous())
        # Check querystring preservation
        self.assertIn('q=Heritage', res_p1.context['pagination_querystring'])
        self.assertIn('category=places', res_p1.context['pagination_querystring'])
        self.assertNotIn('page=', res_p1.context['pagination_querystring'])

        # Page 2
        res_p2 = self.client.get(reverse('core:search'), {'q': 'Heritage', 'category': 'places', 'page': '2'})
        self.assertEqual(res_p2.status_code, 200)
        self.assertTrue(res_p2.context['page_obj'].has_previous())
        self.assertFalse(res_p2.context['page_obj'].has_next())
        self.assertEqual(len(res_p2.context['page_obj']), 3)
