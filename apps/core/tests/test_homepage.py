from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
import datetime

from apps.core.models import LocalityZone, Locality
from apps.places.models import PlaceCategory, Place
from apps.jobs.models import JobCategory, Employer, JobListing
from apps.restaurants.models import Cuisine, RestaurantFeature, Restaurant
from apps.hospitals.models import MedicalSpecialty, Hospital
from apps.education.models import EducationType, Institution
from apps.businesses.models import BusinessCategory, Business
from apps.events.models import EventCategory, EventVenue, Event
from apps.updates.models import UpdateCategory, CityUpdate


class HomepageFullStackComprehensiveTests(TestCase):
    """
    Automated test suite verifying the full-stack implementation of Lahore City Hub homepage:
    - HTTP response code & SEO metadata (canonical, structured data)
    - Template inheritance & all 12 core sections
    - Navigation links & search form attributes
    - Database query filtering (only published & active records)
    - Empty database states rendering
    - Unpublished / inactive content isolation
    - Expired deadlines and events exclusion
    """

    def setUp(self):
        self.client = Client()
        self.home_url = reverse('core:home')

        # Create basic taxonomy
        self.zone = LocalityZone.objects.create(name="Gulberg Zone", slug="gulberg-zone")
        self.locality = Locality.objects.create(zone=self.zone, name="Gulberg III", slug="gulberg-3")

    def test_homepage_http_200_and_seo_metadata(self):
        """Verifies HTTP 200, SEO title, meta description, canonical URL, and JSON-LD."""
        response = self.client.get(self.home_url)
        self.assertEqual(response.status_code, 200)

        # SEO Title & Description
        self.assertContains(response, "Your Complete Guide to Lahore, Pakistan")
        self.assertContains(response, "Discover verified tourist places, dining spots, hospitals, jobs, and civic updates across Lahore.")

        # Canonical Link
        self.assertContains(response, 'rel="canonical"')

        # Schema.org JSON-LD Structured Data
        self.assertContains(response, 'application/ld+json')
        self.assertContains(response, '"@type": "WebSite"')
        self.assertContains(response, '"@type": "City"')
        self.assertContains(response, '"name": "Lahore"')

    def test_homepage_template_inheritance(self):
        """Verifies base template inheritance, navigation header, and footer."""
        response = self.client.get(self.home_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pages/home.html')
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'navbar.html')
        self.assertTemplateUsed(response, 'footer.html')

    def test_homepage_all_12_required_sections_present(self):
        """Verifies that all 12 required sections exist in the rendered output."""
        response = self.client.get(self.home_url)
        self.assertEqual(response.status_code, 200)

        # 1. Hero section
        self.assertContains(response, "THE OFFICIAL CIVIC & CULTURAL DIRECTORY OF LAHORE")
        self.assertContains(response, "Your Complete Guide to Lahore")

        # 2. Main search form
        self.assertContains(response, 'role="search"')
        self.assertContains(response, 'id="hero-search-input"')
        self.assertContains(response, 'name="locality"')

        # 3. Category navigation
        self.assertContains(response, "Discover Lahore by Category")
        self.assertContains(response, "View All Directories")

        # 4. Featured places
        self.assertContains(response, "Iconic Lahore Landmarks & Heritage Sites")

        # 5. Latest published jobs
        self.assertContains(response, "Latest Job Openings in Lahore")

        # 6. Popular restaurants
        self.assertContains(response, "Trending Restaurants & Food Streets")

        # 7. Healthcare directory highlights
        self.assertContains(response, "Hospitals & 24/7 Emergency Medical Centers")

        # 8. Education listings
        self.assertContains(response, "Universities & Degree Colleges in Lahore")

        # 9. Featured businesses
        self.assertContains(response, "Verified Local Businesses & Services")

        # 10. Upcoming events
        self.assertContains(response, "Upcoming Events & Festivals in Lahore")

        # 11. Latest city updates
        self.assertContains(response, "Latest City Notices, Smog & Traffic Advisories")

        # 12. Footer
        self.assertContains(response, "City Directories")
        self.assertContains(response, "is the definitive civic, cultural, and commercial guide to Lahore")

    def test_homepage_empty_database_states_render_gracefully(self):
        """Verifies that when database has no records, informative empty states are displayed without errors."""
        response = self.client.get(self.home_url)
        self.assertEqual(response.status_code, 200)

        # Empty states checks
        self.assertContains(response, "No Tourist Places Published Yet")
        self.assertContains(response, "No Active Job Openings Currently")
        self.assertContains(response, "No Dining Spots Listed Yet")
        self.assertContains(response, "No Hospitals Listed Yet")
        self.assertContains(response, "No Educational Institutions Listed Yet")
        self.assertContains(response, "No Local Businesses Listed Yet")
        self.assertContains(response, "No Upcoming Events Scheduled")
        self.assertContains(response, "No Active Civic Advisories")

    def test_homepage_published_records_display(self):
        """Verifies that published active records populate the appropriate sections."""
        # 1. Place
        p_cat = PlaceCategory.objects.create(name="Shrines & Heritage", slug="shrines")
        place = Place.objects.create(
            category=p_cat,
            locality=self.locality,
            title="Data Darbar Complex",
            summary="Historic Sufi shrine complex in central Lahore.",
            description="Famous spiritual destination.",
            is_active=True,
            is_featured=True
        )

        # 2. Job
        j_cat = JobCategory.objects.create(name="Marketing & Media", slug="marketing")
        emp = Employer.objects.create(name="Lahore Media House", slug="media-house", locality=self.locality, address="Mall Rd")
        job = JobListing.objects.create(
            title="Creative Content Strategist",
            employer=emp,
            category=j_cat,
            locality=self.locality,
            deadline=timezone.now().date() + datetime.timedelta(days=20),
            description="Leading editorial and video storytelling.",
            is_active=True
        )

        # 3. Restaurant
        rest = Restaurant.objects.create(
            title="Monal Lahore Rooftop",
            locality=self.locality,
            address="Park and Ride Plaza, Liberty, Gulberg III",
            summary="Fine dining with Liberty Roundabout views.",
            description="Serving authentic barbecue and continental dishes.",
            price_tier="$$$",
            is_active=True
        )

        # 4. Hospital
        hosp = Hospital.objects.create(
            title="Services Hospital Lahore",
            locality=self.locality,
            address="Ghaus-ul-Azam Road, Jail Road",
            summary="Teaching tertiary hospital with 24/7 casualty department.",
            description="Specialized surgical and medical departments.",
            is_24_7_emergency=True,
            is_active=True
        )

        # 5. Education
        edu_type = EducationType.objects.create(name="Medical University", slug="med-uni")
        inst = Institution.objects.create(
            title="King Edward Medical University",
            education_type=edu_type,
            locality=self.locality,
            address="Nila Gumbad, Anarkali",
            summary="Premier medical university founded in 1860.",
            description="Historic institution of medical excellence in South Asia.",
            is_active=True
        )

        # 6. Business
        b_cat = BusinessCategory.objects.create(name="Publishers & Booksellers", slug="books")
        biz = Business.objects.create(
            category=b_cat,
            locality=self.locality,
            title="Ferozsons Historic Bookshop",
            address="60 Shahrah-e-Quaid-e-Azam, Mall Road",
            summary="Pioneer publishing house and bookstore in Lahore.",
            description="Heritage bookshop active since late 19th century.",
            is_active=True
        )

        # 7. Event
        e_cat = EventCategory.objects.create(name="Art & Exhibitions", slug="art")
        venue = EventVenue.objects.create(name="Shakir Ali Museum", slug="shakir-ali", locality=self.locality, address="Garden Town")
        event = Event.objects.create(
            category=e_cat,
            venue=venue,
            title="Modern Pakistani Calligraphy Biennial",
            start_datetime=timezone.now() + datetime.timedelta(days=5),
            end_datetime=timezone.now() + datetime.timedelta(days=10),
            organizer_name="Pakistan National Council of Arts",
            description="Exhibition showcasing contemporary Islamic calligraphy.",
            is_active=True
        )

        # 8. City Update
        u_cat = UpdateCategory.objects.create(name="Traffic Advisory", slug="traffic")
        update = CityUpdate.objects.create(
            category=u_cat,
            title="Kalma Chowk Underpass Maintenance Advisory",
            summary="Nightly maintenance closures between 12:00 AM and 05:00 AM.",
            content="Commuters advised to utilize Ferozepur surface service lanes.",
            issuing_authority="City Traffic Police Lahore",
            official_source_url="https://ctpl.punjab.gov.pk",
            valid_from=timezone.now(),
            is_active=True
        )

        response = self.client.get(self.home_url)
        self.assertEqual(response.status_code, 200)

        # Verify all records appear
        self.assertContains(response, "Data Darbar Complex")
        self.assertContains(response, "Creative Content Strategist")
        self.assertContains(response, "Monal Lahore Rooftop")
        self.assertContains(response, "Services Hospital Lahore")
        self.assertContains(response, "King Edward Medical University")
        self.assertContains(response, "Ferozsons Historic Bookshop")
        self.assertContains(response, "Modern Pakistani Calligraphy Biennial")
        self.assertContains(response, "Kalma Chowk Underpass Maintenance Advisory")

    def test_homepage_unpublished_content_hidden(self):
        """Verifies that records with is_active=False are strictly excluded from the homepage."""
        p_cat = PlaceCategory.objects.create(name="Draft Category", slug="draft-cat")
        hidden_place = Place.objects.create(
            category=p_cat,
            locality=self.locality,
            title="Secret Underground Chamber",
            summary="Unpublished draft record.",
            description="Must not be visible publicly.",
            is_active=False
        )

        j_cat = JobCategory.objects.create(name="Draft Jobs", slug="draft-jobs")
        emp = Employer.objects.create(name="Stealth Employer", slug="stealth", locality=self.locality, address="DHA")
        hidden_job = JobListing.objects.create(
            title="Secret Agent Position",
            employer=emp,
            category=j_cat,
            locality=self.locality,
            deadline=timezone.now().date() + datetime.timedelta(days=20),
            description="Unpublished job.",
            is_active=False
        )

        hidden_rest = Restaurant.objects.create(
            title="Unapproved Ghost Kitchen",
            locality=self.locality,
            address="Gulberg",
            summary="Unpublished.",
            description="Draft.",
            is_active=False
        )

        response = self.client.get(self.home_url)
        self.assertEqual(response.status_code, 200)

        self.assertNotContains(response, "Secret Underground Chamber")
        self.assertNotContains(response, "Secret Agent Position")
        self.assertNotContains(response, "Unapproved Ghost Kitchen")

    def test_homepage_expired_records_hidden(self):
        """Verifies that expired jobs and concluded events do not appear on the homepage."""
        # Expired Job (deadline in the past)
        j_cat = JobCategory.objects.create(name="Expired Category", slug="expired-jobs")
        emp = Employer.objects.create(name="Past Employer", slug="past-emp", locality=self.locality, address="Gulberg")
        expired_job = JobListing.objects.create(
            title="Expired Project Manager Opening",
            employer=emp,
            category=j_cat,
            locality=self.locality,
            deadline=timezone.now().date() - datetime.timedelta(days=10),
            description="This vacancy expired 10 days ago.",
            is_active=True
        )

        # Concluded Event (end_datetime in the past)
        e_cat = EventCategory.objects.create(name="Past Events", slug="past-events")
        venue = EventVenue.objects.create(name="Old Venue", slug="old-venue", locality=self.locality, address="Mall Rd")
        expired_event = Event.objects.create(
            category=e_cat,
            venue=venue,
            title="Past Food Festival 2024",
            start_datetime=timezone.now() - datetime.timedelta(days=40),
            end_datetime=timezone.now() - datetime.timedelta(days=35),
            organizer_name="Past Org",
            description="This festival already concluded.",
            is_active=True
        )

        response = self.client.get(self.home_url)
        self.assertEqual(response.status_code, 200)

        self.assertNotContains(response, "Expired Project Manager Opening")
        self.assertNotContains(response, "Past Food Festival 2024")

    def test_homepage_navigation_links(self):
        """Verifies that all primary category and civic links resolve correctly."""
        response = self.client.get(self.home_url)
        self.assertEqual(response.status_code, 200)

        # Check links exist in DOM
        self.assertContains(response, reverse('core:directory_index'))
        self.assertContains(response, reverse('core:category_list', kwargs={'category_slug': 'places'}))
        self.assertContains(response, reverse('core:category_list', kwargs={'category_slug': 'jobs'}))
        self.assertContains(response, reverse('core:category_list', kwargs={'category_slug': 'restaurants'}))
        self.assertContains(response, reverse('core:category_list', kwargs={'category_slug': 'hospitals'}))
        self.assertContains(response, reverse('core:category_list', kwargs={'category_slug': 'education'}))
        self.assertContains(response, reverse('core:category_list', kwargs={'category_slug': 'businesses'}))
        self.assertContains(response, reverse('core:business_submission'))
        self.assertContains(response, reverse('core:about'))
        self.assertContains(response, reverse('core:contact'))

    def test_homepage_query_efficiency_and_no_n_plus_one(self):
        """
        Verifies that querying the homepage does not execute N+1 database queries.
        Pre-creates multiple records per model and ensures query count stays bounded.
        """
        p_cat = PlaceCategory.objects.create(name="Heritage", slug="heritage")
        for i in range(5):
            Place.objects.create(
                category=p_cat, locality=self.locality,
                title=f"Historic Place {i}", summary=f"Summary {i}",
                description=f"Desc {i}", is_active=True
            )

        j_cat = JobCategory.objects.create(name="Tech", slug="tech")
        emp = Employer.objects.create(name="Tech Co", slug="tech-co", locality=self.locality, address="DHA")
        for i in range(5):
            JobListing.objects.create(
                title=f"Engineer {i}", employer=emp, category=j_cat, locality=self.locality,
                deadline=timezone.now().date() + datetime.timedelta(days=10),
                description=f"Description {i}", is_active=True
            )

        with self.assertNumQueries(16):
            response = self.client.get(self.home_url)
            self.assertEqual(response.status_code, 200)
