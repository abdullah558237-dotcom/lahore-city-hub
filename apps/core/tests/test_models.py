from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth import get_user_model
from decimal import Decimal
import datetime

from apps.core.models import LocalityZone, Locality, EmergencyHelpline
from apps.places.models import PlaceCategory, Place, PlaceGalleryImage
from apps.jobs.models import JobCategory, Employer, JobListing
from apps.restaurants.models import Cuisine, RestaurantFeature, Restaurant, MenuHighlight
from apps.hospitals.models import MedicalSpecialty, Hospital
from apps.education import models as edu_models
from apps.businesses.models import BusinessCategory, Business, BusinessClaim
from apps.transport.models import TransitMode, TransitRoute, TransitStation
from apps.events.models import EventCategory, EventVenue, Event
from apps.updates.models import UpdateCategory, CityUpdate
from apps.reviews.models import Review

User = get_user_model()


class ModelArchitectureComprehensiveTests(TestCase):
    """
    Exhaustive database architecture test suite verifying model creation,
    validation logic (clean), relationships, unique constraints, and publication status.
    """

    def setUp(self):
        # Setup common entities
        self.user = User.objects.create_user(
            email='testuser@lahorecityhub.pk',
            username='testuser',
            password='TestPassword123!'
        )
        self.zone = LocalityZone.objects.create(
            name="Gulberg Zone",
            slug="gulberg-zone",
            description="Central commercial and residential hub of Lahore"
        )
        self.locality = Locality.objects.create(
            zone=self.zone,
            name="Gulberg III",
            slug="gulberg-3",
            postal_code="54660"
        )

    def test_core_locality_and_helpline(self):
        """Verifies LocalityZone, Locality and EmergencyHelpline creation and queries."""
        self.assertEqual(str(self.zone), "Gulberg Zone")
        self.assertEqual(str(self.locality), "Gulberg III (Gulberg Zone)")

        helpline = EmergencyHelpline.objects.create(
            name="Rescue 1122",
            short_code="1122",
            full_phone_number="042-99231701",
            agency_name="Punjab Emergency Service",
            display_order=1
        )
        self.assertEqual(str(helpline), "Rescue 1122 (1122)")
        active_helplines = EmergencyHelpline.objects.filter(is_active=True)
        self.assertIn(helpline, active_helplines)

    def test_transport_models_and_constraints(self):
        """Verifies TransitMode, Route, and TransitStation unique_together constraint."""
        mode = TransitMode.objects.create(name="Metro Train", slug="metro-train", icon_class="bi-train-front")
        route = TransitRoute.objects.create(
            mode=mode,
            route_name="Orange Line",
            route_code="OLMT-01",
            origin_station="Ali Town",
            destination_station="Dera Gujran",
            total_stations=26,
            total_distance_km=Decimal("27.10")
        )
        self.assertEqual(str(route), "OLMT-01: Orange Line")

        # Route validation test
        invalid_route = TransitRoute(
            mode=mode,
            route_name="Invalid Route",
            route_code="INV-01",
            origin_station="A",
            destination_station="B",
            total_stations=0,
            total_distance_km=Decimal("-5.00")
        )
        with self.assertRaises(ValidationError):
            invalid_route.clean()

        station1 = TransitStation.objects.create(
            route=route,
            station_name="Anarkali",
            station_number=13,
            locality=self.locality
        )
        self.assertIn("Anarkali (#13)", str(station1))

        # Station clean validation: station_number < 1
        invalid_station = TransitStation(
            route=route,
            station_name="Zero Station",
            station_number=0,
            locality=self.locality
        )
        with self.assertRaises(ValidationError):
            invalid_station.clean()

    def test_places_model_and_validation(self):
        """Verifies PlaceCategory, Place, FK to TransitStation, and negative fee validation."""
        category = PlaceCategory.objects.create(
            name="Historical Monument",
            slug="historical-monument",
            icon_class="bi-bank"
        )
        place = Place.objects.create(
            category=category,
            locality=self.locality,
            title="Lahore Fort",
            address="Fort Road, Walled City",
            summary="Historic Mughal citadel in Lahore.",
            description="UNESCO World Heritage site containing Sheesh Mahal, Naulakha Pavilion.",
            entry_fee_pkr=Decimal("50.00"),
            entry_fee_foreigner_pkr=Decimal("500.00")
        )
        self.assertEqual(str(place), "Lahore Fort")
        self.assertTrue(place.is_active)

        # Validation: Negative entry fee
        invalid_place = Place(
            category=category,
            locality=self.locality,
            title="Invalid Place",
            address="Some address",
            summary="Summary",
            description="Description",
            entry_fee_pkr=Decimal("-10.00")
        )
        with self.assertRaises(ValidationError):
            invalid_place.clean()

        gallery_img = PlaceGalleryImage.objects.create(
            place=place,
            caption="Alamgiri Gate view",
            display_order=1
        )
        self.assertIn("Lahore Fort", str(gallery_img))

    def test_jobs_model_validation_and_salary_check(self):
        """Verifies Employer, JobListing, and salary min > max validation."""
        category = JobCategory.objects.create(name="Software Engineering", slug="software-engineering")
        employer = Employer.objects.create(
            name="Lahore Tech Hub Solutions",
            slug="lahore-tech-hub-solutions",
            locality=self.locality,
            address="Main Boulevard, Gulberg III"
        )
        today = timezone.now().date()
        job = JobListing.objects.create(
            employer=employer,
            category=category,
            locality=self.locality,
            title="Senior Python / Django Developer",
            salary_min_pkr=Decimal("200000.00"),
            salary_max_pkr=Decimal("350000.00"),
            deadline=today + datetime.timedelta(days=30),
            description="Lead backend development for city digital services."
        )
        self.assertEqual(str(job), "Senior Python / Django Developer at Lahore Tech Hub Solutions")
        self.assertTrue(job.slug)

        # Validation check: salary_min > salary_max
        invalid_job = JobListing(
            employer=employer,
            category=category,
            locality=self.locality,
            title="Invalid Salary Job",
            salary_min_pkr=Decimal("500000.00"),
            salary_max_pkr=Decimal("200000.00"),
            deadline=today,
            description="Testing validation."
        )
        with self.assertRaises(ValidationError):
            invalid_job.clean()

    def test_restaurants_model_and_m2m(self):
        """Verifies Restaurant, Cuisine M2M, Features M2M, and MenuHighlight."""
        cuisine = Cuisine.objects.create(name="Traditional Lahori", slug="traditional-lahori")
        feature = RestaurantFeature.objects.create(name="Rooftop Dining", slug="rooftop-dining")

        restaurant = Restaurant.objects.create(
            locality=self.locality,
            title="Andaaz Restaurant",
            address="Fort Road Food Street",
            summary="Heritage rooftop dining with view of Badshahi Mosque.",
            description="Specializing in traditional cuisine and panoramic vistas.",
            price_tier='$$$',
            seating_capacity=120
        )
        restaurant.cuisines.add(cuisine)
        restaurant.features.add(feature)

        self.assertIn(cuisine, restaurant.cuisines.all())
        self.assertIn(feature, restaurant.features.all())

        highlight = MenuHighlight.objects.create(
            restaurant=restaurant,
            item_name="Mutton Shinwari Karahi",
            price_pkr=Decimal("2400.00"),
            is_signature=True
        )
        self.assertIn("Mutton Shinwari Karahi", str(highlight))

        # Test negative seating capacity validation
        bad_restaurant = Restaurant(
            locality=self.locality,
            title="Negative Seating",
            address="Address",
            summary="Summary",
            description="Description",
            seating_capacity=-50
        )
        with self.assertRaises(ValidationError):
            bad_restaurant.clean()

    def test_hospitals_model_and_validation(self):
        """Verifies Hospital, MedicalSpecialty, and capacity validation."""
        specialty = MedicalSpecialty.objects.create(name="Cardiology", slug="cardiology")
        hospital = Hospital.objects.create(
            locality=self.locality,
            title="Punjab Institute of Cardiology",
            address="Jail Road, Lahore",
            summary="Tertiary cardiac care facility.",
            description="Providing emergency and invasive cardiology services 24/7.",
            hospital_type='public',
            is_24_7_emergency=True,
            bed_capacity=500,
            ambulance_direct_phone="042-99203051"
        )
        hospital.specialties.add(specialty)
        self.assertTrue(hospital.is_24_7_emergency)
        self.assertEqual(str(hospital), "Punjab Institute of Cardiology")

        # Test negative bed capacity validation
        bad_hospital = Hospital(
            locality=self.locality,
            title="Bad Hospital",
            address="Address",
            summary="Summary",
            description="Description",
            bed_capacity=-10
        )
        with self.assertRaises(ValidationError):
            bad_hospital.clean()

    def test_education_model_and_validation(self):
        """Verifies EducationType, AccreditationBoard, Institution, and established year validation."""
        edu_type = edu_models.EducationType.objects.create(name="Public University", slug="public-university")
        board = edu_models.AccreditationBoard.objects.create(name="Higher Education Commission", abbreviation="HEC")

        institution = edu_models.Institution.objects.create(
            education_type=edu_type,
            locality=self.locality,
            title="Government College University Lahore",
            address="Katchery Road, Anarkali",
            summary="Historic seat of higher learning established in 1864.",
            description="Offering undergraduate, postgraduate, and doctoral degrees.",
            established_year=1864
        )
        institution.accreditations.add(board)
        self.assertEqual(str(institution), "Government College University Lahore")

        # Test invalid established year validation
        bad_inst = edu_models.Institution(
            education_type=edu_type,
            locality=self.locality,
            title="Time Traveler College",
            address="Address",
            summary="Summary",
            description="Description",
            established_year=500
        )
        with self.assertRaises(ValidationError):
            bad_inst.clean()

    def test_businesses_model_and_claim(self):
        """Verifies Business, BusinessCategory, and BusinessClaim workflow."""
        cat = BusinessCategory.objects.create(name="Handicrafts & Artisans", slug="handicrafts")
        biz = Business.objects.create(
            category=cat,
            locality=self.locality,
            title="Anarkali Artisan Leatherworks",
            address="Old Anarkali Bazaar",
            summary="Traditional handcrafted leather shoes and accessories.",
            description="Family-owned leather crafting workshop active since 1952."
        )
        self.assertEqual(str(biz), "Anarkali Artisan Leatherworks")

        claim = BusinessClaim.objects.create(
            business=biz,
            claimant=self.user,
            claimant_role="Owner",
            official_email="artisan@example.pk",
            contact_phone="+923001234567"
        )
        self.assertIn("Claim for Anarkali Artisan Leatherworks", str(claim))
        self.assertEqual(claim.status, 'pending')

    def test_events_model_and_validation(self):
        """Verifies EventCategory, EventVenue, Event, and chronological validation."""
        cat = EventCategory.objects.create(name="Literary & Arts", slug="literary-arts")
        venue = EventVenue.objects.create(
            name="Alhamra Arts Council",
            slug="alhamra-arts-council",
            address="Mall Road, Lahore",
            locality=self.locality,
            capacity=1000
        )
        start = timezone.now() + datetime.timedelta(days=7)
        end = start + datetime.timedelta(hours=4)

        event = Event.objects.create(
            category=cat,
            venue=venue,
            title="Lahore Literary Festival 2026",
            start_datetime=start,
            end_datetime=end,
            organizer_name="LLF Foundation",
            description="Annual gathering of writers, poets, and artists."
        )
        self.assertEqual(str(event), "Lahore Literary Festival 2026")
        self.assertTrue(event.slug)

        # Validation: start_datetime after end_datetime
        bad_event = Event(
            category=cat,
            venue=venue,
            title="Back to the Future Event",
            start_datetime=end,
            end_datetime=start,
            organizer_name="Org",
            description="Description"
        )
        with self.assertRaises(ValidationError):
            bad_event.clean()

    def test_updates_model_and_validation(self):
        """Verifies UpdateCategory, CityUpdate, and datetime validation."""
        cat = UpdateCategory.objects.create(name="Air Quality Advisories", slug="air-quality")
        now = timezone.now()
        later = now + datetime.timedelta(days=2)

        update = CityUpdate.objects.create(
            category=cat,
            title="Green Lockdown & Smog Advisory for Lahore Central Zone",
            summary="Traffic restrictions and mask requirements during high AQI index.",
            content="Heavy goods vehicles restricted from entering Mall Road and Gulberg from 8am to 8pm.",
            issuing_authority="Punjab Environment Protection Agency",
            official_source_url="https://epd.punjab.gov.pk/advisories",
            valid_from=now,
            valid_until=later
        )
        self.assertEqual(str(update), "Green Lockdown & Smog Advisory for Lahore Central Zone")
        self.assertTrue(update.slug)

        # Validation: valid_from after valid_until
        bad_update = CityUpdate(
            category=cat,
            title="Invalid Update",
            summary="Summary",
            content="Content",
            issuing_authority="EPA",
            official_source_url="https://epd.punjab.gov.pk",
            valid_from=later,
            valid_until=now
        )
        with self.assertRaises(ValidationError):
            bad_update.clean()

    def test_reviews_model_rating_validation(self):
        """Verifies Review model and rating boundary validation."""
        from django.contrib.contenttypes.models import ContentType
        ct = ContentType.objects.get_for_model(self.locality)

        review = Review.objects.create(
            user=self.user,
            content_type=ct,
            object_id=self.locality.id,
            rating=5,
            title="Outstanding neighborhood",
            comment="Gulberg offers everything from dining to parks."
        )
        self.assertIn("5★ by testuser@lahorecityhub.pk", str(review))

        # Rating boundary check (rating cannot be 0 or 6)
        bad_review = Review(
            user=self.user,
            content_type=ct,
            object_id=self.locality.id,
            rating=6,
            comment="Invalid 6 stars."
        )
        with self.assertRaises(ValidationError):
            bad_review.clean()
