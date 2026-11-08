from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.admin.sites import AdminSite
from django.utils import timezone

from apps.core.models import LocalityZone, Locality, EmergencyHelpline
from apps.places.models import PlaceCategory, Place
from apps.places.admin import PlaceAdmin
from apps.restaurants.models import Cuisine, Restaurant
from apps.restaurants.admin import RestaurantAdmin
from apps.hospitals.models import MedicalSpecialty, Hospital
from apps.hospitals.admin import HospitalAdmin
from apps.education.models import EducationType, Institution
from apps.education.admin import InstitutionAdmin
from apps.jobs.models import JobCategory, Employer, JobListing
from apps.jobs.admin import JobListingAdmin
from apps.businesses.models import BusinessCategory, Business, BusinessClaim, BusinessEditRequest, BusinessReport
from apps.businesses.admin import BusinessAdmin
from apps.transport.models import TransitMode, TransitRoute, TransitStation, TransitGuide
from apps.events.models import EventCategory, EventVenue, Event
from apps.events.admin import EventAdmin
from apps.updates.models import UpdateCategory, CityUpdate
from apps.updates.admin import CityUpdateAdmin
from apps.reviews.models import Review

User = get_user_model()


class MockSuperUser:
    is_active = True
    is_staff = True
    is_superuser = True
    role = 'admin'


class MockStaffEditor:
    is_active = True
    is_staff = True
    is_superuser = False
    role = 'moderator'


class DjangoAdminSecurityAndExperienceTests(TestCase):
    """
    Comprehensive test suite for Django Admin content management experience:
    - Admin access boundaries (anonymous, member, business owner, staff editor, superuser)
    - Changelist views for all 10 modules, categories, and user submissions
    - Search, filters, and date hierarchy execution
    - Administrative actions (publish, unpublish, mark verified, stamp timestamps)
    - Deletion permission enforcement (restricted to superusers/admins)
    """

    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
        self.site = AdminSite()

        # Regular Member User (is_staff=False)
        self.member = User.objects.create_user(
            email='member@lahorecityhub.pk',
            username='lahore_member',
            password='Password123!',
            role='member'
        )

        # Business Owner User (is_staff=False)
        self.owner = User.objects.create_user(
            email='owner@lahorecityhub.pk',
            username='lahore_owner',
            password='Password123!',
            role='business_owner'
        )

        # Staff Editor / Moderator (is_staff=True, is_superuser=False)
        self.editor = User.objects.create_user(
            email='editor@lahorecityhub.pk',
            username='staff_editor',
            password='Password123!',
            is_staff=True,
            is_superuser=False,
            role='moderator'
        )

        # Administrator / Superuser (is_staff=True, is_superuser=True)
        self.admin = User.objects.create_superuser(
            email='admin@lahorecityhub.pk',
            username='super_admin',
            password='Password123!'
        )

        # Sample Locality & Zone
        self.zone = LocalityZone.objects.create(name='Gulberg Zone', slug='gulberg-zone')
        self.locality = Locality.objects.create(name='Gulberg III', slug='gulberg-iii', zone=self.zone)

        # Place
        self.place_cat = PlaceCategory.objects.create(name='Historical Mosques', slug='historical-mosques')
        self.place = Place.objects.create(
            title='Badshahi Mosque',
            slug='badshahi-mosque',
            category=self.place_cat,
            locality=self.locality,
            address='Walled City of Lahore',
            summary='Mughal-era landmark mosque.',
            description='Historic landmark.',
            is_active=True,
            verification_status='verified'
        )

        # Restaurant
        self.cuisine = Cuisine.objects.create(name='Traditional Lahori', slug='traditional-lahori')
        self.restaurant = Restaurant.objects.create(
            title='Haveli Restaurant',
            slug='haveli-restaurant',
            locality=self.locality,
            address='Fort Road Food Street',
            summary='Rooftop dining with mosque views.',
            description='Famous rooftop eatery.',
            is_active=True,
            verification_status='verified'
        )

        # Hospital
        self.specialty = MedicalSpecialty.objects.create(name='Oncology', slug='oncology')
        self.hospital = Hospital.objects.create(
            title='Shaukat Khanum Memorial Cancer Hospital',
            slug='shaukat-khanum-hospital',
            locality=self.locality,
            address='7A Block R3, Johar Town',
            summary='Specialized cancer hospital.',
            description='Premier cancer care center.',
            is_active=True,
            verification_status='verified'
        )

        # Education
        self.edu_type = EducationType.objects.create(name='General Universities', slug='general-universities')
        self.institution = Institution.objects.create(
            title='University of the Punjab',
            slug='punjab-university',
            education_type=self.edu_type,
            locality=self.locality,
            address='Quaid-e-Azam Campus, Canal Road',
            summary='Oldest public university in Pakistan.',
            description='Historic academic institution.',
            is_active=True,
            verification_status='verified'
        )

        # Job
        self.job_cat = JobCategory.objects.create(name='Software Engineering', slug='software-engineering')
        self.employer = Employer.objects.create(name='TechLogix Pakistan', slug='techlogix', locality=self.locality)
        self.job = JobListing.objects.create(
            title='Senior Django Engineer',
            slug='senior-django-engineer',
            employer=self.employer,
            category=self.job_cat,
            locality=self.locality,
            employment_type='full_time',
            description='Backend architecture role.',
            requirements='Python, Django, PostgreSQL.',
            deadline=timezone.now().date() + timezone.timedelta(days=30),
            is_active=True,
            verification_status='verified'
        )

        # Business
        self.biz_cat = BusinessCategory.objects.create(name='Legal Services', slug='legal-services')
        self.business = Business.objects.create(
            title='Lahore Corporate Law Chambers',
            slug='lahore-corporate-law',
            category=self.biz_cat,
            locality=self.locality,
            address='Ferozepur Road',
            summary='Corporate legal counsel.',
            description='Legal practice specializing in corporate governance.',
            submitted_by=self.owner,
            is_active=True,
            verification_status='verified'
        )

        # Business User Submissions
        self.edit_request = BusinessEditRequest.objects.create(
            business=self.business,
            requested_by=self.owner,
            title='Lahore Corporate Law Chambers Updated',
            description='Updated suite numbers.',
            address='Ferozepur Road Suite 302',
            status='pending'
        )
        self.claim = BusinessClaim.objects.create(
            business=self.business,
            claimant=self.owner,
            claimant_role='Managing Partner',
            official_email='managing@lawchambers.pk',
            contact_phone='+92 300 1234567',
            status='pending'
        )
        self.report = BusinessReport.objects.create(
            business=self.business,
            reason='wrong_phone',
            reporter_name='Concerned Citizen',
            reporter_email='citizen@example.pk',
            details='Phone number is missing area code.',
            status='pending'
        )

        # Transport
        self.mode = TransitMode.objects.create(name='Metro Train', slug='metro-train')
        self.route = TransitRoute.objects.create(
            mode=self.mode,
            route_code='OLMT-01',
            route_name='Orange Line Metro Train',
            slug='orange-line-metro',
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
            slug='ali-town-terminal',
            locality=self.locality
        )
        self.guide = TransitGuide.objects.create(
            title='Commuter Card Ticketing Guide',
            slug='commuter-card-guide',
            category='fares_ticketing',
            route=self.route,
            summary='How to buy and recharge cards.',
            content='Full guide text.',
            is_published=True
        )

        # Events
        self.event_cat = EventCategory.objects.create(name='Literary Festivals', slug='literary-festivals')
        self.venue = EventVenue.objects.create(name='Alhamra Arts Council', slug='alhamra-arts', locality=self.locality, address='Mall Road')
        self.event = Event.objects.create(
            title='Faiz Festival 2026',
            slug='faiz-festival-2026',
            category=self.event_cat,
            venue=self.venue,
            start_datetime=timezone.now() + timezone.timedelta(days=5),
            end_datetime=timezone.now() + timezone.timedelta(days=7),
            organizer_name='Faiz Foundation',
            description='Celebration of literature.',
            is_active=True,
            verification_status='verified'
        )

        # Updates
        self.update_cat = UpdateCategory.objects.create(name='Smog Advisories', slug='smog-advisories')
        self.update = CityUpdate.objects.create(
            title='EPA Winter Smog Guidelines Enacted',
            slug='epa-winter-smog-guidelines',
            category=self.update_cat,
            severity='caution',
            summary='Air quality warning.',
            content='Advisory protocols.',
            issuing_authority='Punjab EPA',
            official_source_url='https://epa.punjab.gov.pk',
            is_active=True
        )

    # ==========================================================
    # 1. Admin Access & Authentication Boundaries
    # ==========================================================

    def test_anonymous_access_redirected_to_admin_login(self):
        """Anonymous access to /admin/ redirects to login with next parameter."""
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 302)
        self.assertTrue('/admin/login/' in response.url)

    def test_regular_member_denied_admin_access(self):
        """Regular users with is_staff=False cannot access /admin/."""
        self.client.force_login(self.member)
        response = self.client.get('/admin/')
        # Django admin redirects non-staff users back to /admin/login/
        self.assertEqual(response.status_code, 302)
        self.assertTrue('/admin/login/' in response.url)

    def test_business_owner_denied_admin_access(self):
        """Business owners with is_staff=False cannot access /admin/."""
        self.client.force_login(self.owner)
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 302)
        self.assertTrue('/admin/login/' in response.url)

    def test_staff_editor_can_access_admin_dashboard(self):
        """Staff editors with is_staff=True can access the admin dashboard."""
        self.client.force_login(self.editor)
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 200)

    def test_superuser_sees_custom_branding(self):
        """Superuser access renders customized administration portal branding."""
        self.client.force_login(self.admin)
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Lahore City Hub Administration')

    # ==========================================================
    # 2. Directory Model Changelist Views
    # ==========================================================

    def test_admin_changelists_for_all_directories(self):
        """Verifies HTTP 200 on changelists across all directory models."""
        self.client.force_login(self.admin)
        endpoints = [
            '/admin/places/place/',
            '/admin/places/placecategory/',
            '/admin/restaurants/restaurant/',
            '/admin/restaurants/cuisine/',
            '/admin/hospitals/hospital/',
            '/admin/hospitals/medicalspecialty/',
            '/admin/education/institution/',
            '/admin/education/educationtype/',
            '/admin/jobs/joblisting/',
            '/admin/jobs/jobcategory/',
            '/admin/jobs/employer/',
            '/admin/businesses/business/',
            '/admin/businesses/businesscategory/',
            '/admin/transport/transitroute/',
            '/admin/transport/transitstation/',
            '/admin/transport/transitguide/',
            '/admin/transport/transitmode/',
            '/admin/events/event/',
            '/admin/events/eventcategory/',
            '/admin/events/eventvenue/',
            '/admin/updates/cityupdate/',
            '/admin/updates/updatecategory/',
            '/admin/core/locality/',
            '/admin/core/localityzone/',
            '/admin/core/emergencyhelpline/',
            '/admin/accounts/customuser/',
            '/admin/accounts/userprofile/',
            '/admin/accounts/userbookmark/',
            '/admin/reviews/review/',
        ]
        for url in endpoints:
            with self.subTest(url=url):
                res = self.client.get(url)
                self.assertEqual(res.status_code, 200, f"Failed on admin URL: {url}")

    # ==========================================================
    # 3. User Submissions & Moderation Changelists
    # ==========================================================

    def test_admin_changelists_for_user_submissions(self):
        """Verifies moderation changelists for user submissions."""
        self.client.force_login(self.admin)
        submission_urls = [
            '/admin/businesses/businessclaim/',
            '/admin/businesses/businesseditrequest/',
            '/admin/businesses/businessreport/',
            '/admin/reviews/review/',
        ]
        for url in submission_urls:
            with self.subTest(url=url):
                res = self.client.get(url)
                self.assertEqual(res.status_code, 200)

    # ==========================================================
    # 4. Search & Date Hierarchy Execution
    # ==========================================================

    def test_admin_search_and_date_hierarchy(self):
        """Search and date hierarchy queries execute cleanly without SQL/syntax errors."""
        self.client.force_login(self.admin)

        # Search Places
        res_place = self.client.get('/admin/places/place/?q=Badshahi')
        self.assertEqual(res_place.status_code, 200)
        self.assertContains(res_place, 'Badshahi Mosque')

        # Search Businesses
        res_biz = self.client.get('/admin/businesses/business/?q=Corporate')
        self.assertEqual(res_biz.status_code, 200)
        self.assertContains(res_biz, 'Lahore Corporate Law Chambers')

        # Search Events with date hierarchy
        year = timezone.now().year
        res_event = self.client.get(f'/admin/events/event/?start_datetime__year={year}')
        self.assertEqual(res_event.status_code, 200)
        self.assertContains(res_event, 'Faiz Festival 2026')

        # Search City Updates with date hierarchy
        res_update = self.client.get(f'/admin/updates/cityupdate/?valid_from__year={year}')
        self.assertEqual(res_update.status_code, 200)
        self.assertContains(res_update, 'EPA Winter Smog Guidelines Enacted')

    # ==========================================================
    # 5. Administrative Actions & Publication Controls
    # ==========================================================

    def test_admin_actions_publication_and_verification(self):
        """Admin actions correctly toggle publication and stamp verification timestamps."""
        from django.contrib.sessions.backends.db import SessionStore
        from django.contrib.messages.storage.fallback import FallbackStorage
        request = self.factory.get('/admin/')
        request.user = self.admin
        request.session = SessionStore()
        setattr(request, '_messages', FallbackStorage(request))

        # 1. Test PlaceAdmin actions
        place_admin = PlaceAdmin(Place, self.site)
        qs_place = Place.objects.filter(pk=self.place.pk)

        # Unpublish
        place_admin.unpublish(request, qs_place)
        self.place.refresh_from_db()
        self.assertFalse(self.place.is_active)

        # Publish
        place_admin.publish(request, qs_place)
        self.place.refresh_from_db()
        self.assertTrue(self.place.is_active)

        # Make Verified (stamps last_verified_at)
        place_admin.make_verified(request, qs_place)
        self.place.refresh_from_db()
        self.assertEqual(self.place.verification_status, 'verified')
        self.assertIsNotNone(self.place.last_verified_at)

        # 2. Test BusinessAdmin actions
        biz_admin = BusinessAdmin(Business, self.site)
        qs_biz = Business.objects.filter(pk=self.business.pk)
        biz_admin.unpublish(request, qs_biz)
        self.business.refresh_from_db()
        self.assertFalse(self.business.is_active)

        biz_admin.approve_and_publish(request, qs_biz)
        self.business.refresh_from_db()
        self.assertTrue(self.business.is_active)
        self.assertEqual(self.business.verification_status, 'verified')

        # 3. Test CityUpdateAdmin actions
        update_admin = CityUpdateAdmin(CityUpdate, self.site)
        qs_update = CityUpdate.objects.filter(pk=self.update.pk)
        update_admin.pin_updates(request, qs_update)
        self.update.refresh_from_db()
        self.assertTrue(self.update.is_pinned)

        update_admin.unpin_updates(request, qs_update)
        self.update.refresh_from_db()
        self.assertFalse(self.update.is_pinned)

    # ==========================================================
    # 6. Deletion Permissions Boundary
    # ==========================================================

    def test_deletion_permission_boundary_enforced(self):
        """Non-admin editors cannot delete directory listings; only superusers can."""
        place_admin = PlaceAdmin(Place, self.site)
        biz_admin = BusinessAdmin(Business, self.site)
        hosp_admin = HospitalAdmin(Hospital, self.site)

        # Create request objects for staff editor and superuser
        editor_req = self.factory.get('/admin/places/place/')
        editor_req.user = self.editor

        admin_req = self.factory.get('/admin/places/place/')
        admin_req.user = self.admin

        # Staff Editor must NOT have delete permission
        self.assertFalse(place_admin.has_delete_permission(editor_req, self.place))
        self.assertFalse(biz_admin.has_delete_permission(editor_req, self.business))
        self.assertFalse(hosp_admin.has_delete_permission(editor_req, self.hospital))

        # Superuser MUST have delete permission
        self.assertTrue(place_admin.has_delete_permission(admin_req, self.place))
        self.assertTrue(biz_admin.has_delete_permission(admin_req, self.business))
        self.assertTrue(hosp_admin.has_delete_permission(admin_req, self.hospital))
