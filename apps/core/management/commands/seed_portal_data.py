from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
import datetime

from apps.core.models import LocalityZone, Locality, EmergencyHelpline
from apps.places.models import PlaceCategory, Place
from apps.jobs.models import JobCategory, Employer, JobListing
from apps.restaurants.models import Cuisine, RestaurantFeature, Restaurant
from apps.hospitals.models import MedicalSpecialty, Hospital
from apps.education.models import EducationType, AccreditationBoard, Institution
from apps.businesses.models import BusinessCategory, Business
from apps.events.models import EventCategory, EventVenue, Event
from apps.updates.models import UpdateCategory, CityUpdate
from apps.transport.models import TransitMode, TransitRoute


class Command(BaseCommand):
    help = "Populate verified directory records across all 10 modules for Lahore City Hub development."

    def handle(self, *args, **options):
        self.stdout.write("Seeding verified data for Lahore City Hub...")

        # 1. Localities & Zones
        central_zone, _ = LocalityZone.objects.get_or_create(
            name="Gulberg & Central",
            defaults={"slug": "gulberg-central", "description": "Commercial heart, shopping corridors and corporate avenues."}
        )
        walled_zone, _ = LocalityZone.objects.get_or_create(
            name="Walled City & Northern",
            defaults={"slug": "walled-city-northern", "description": "Historic Lahore, Mughal monuments and traditional food streets."}
        )

        gulberg, _ = Locality.objects.get_or_create(
            slug="gulberg-3",
            defaults={"zone": central_zone, "name": "Gulberg III", "postal_code": "54660"}
        )
        walled_city, _ = Locality.objects.get_or_create(
            slug="walled-city",
            defaults={"zone": walled_zone, "name": "Walled City (Androon Lahore)", "postal_code": "54000"}
        )

        # 2. Helplines
        EmergencyHelpline.objects.get_or_create(
            short_code="1122",
            defaults={"name": "Rescue 1122", "agency_name": "Punjab Emergency Service", "display_order": 1, "is_active": True}
        )
        EmergencyHelpline.objects.get_or_create(
            short_code="1915",
            defaults={"name": "Lahore Traffic Police", "agency_name": "City Traffic Police Lahore", "display_order": 2, "is_active": True}
        )

        # 3. Places
        hist_cat, _ = PlaceCategory.objects.get_or_create(
            slug="historical-monuments",
            defaults={"name": "Historical Monuments", "icon_class": "bi-bank"}
        )
        Place.objects.get_or_create(
            slug="badshahi-mosque",
            defaults={
                "category": hist_cat,
                "locality": walled_city,
                "title": "Badshahi Mosque",
                "title_ur": "بادشاہی مسجد",
                "summary": "Mughal imperial red sandstone mosque built in 1673 AD opposite Lahore Fort.",
                "description": "Constructed under the reign of the sixth Mughal Emperor Aurangzeb Alamgir. One of the largest historic mosques in the world.",
                "address": "Opposite Alamgiri Gate, Walled City, Lahore",
                "is_featured": True,
                "is_active": True,
                "verification_status": "verified",
            }
        )
        Place.objects.get_or_create(
            slug="lahore-fort-shahi-qila",
            defaults={
                "category": hist_cat,
                "locality": walled_city,
                "title": "Lahore Fort (Shahi Qila)",
                "title_ur": "شاہی قلعہ",
                "summary": "UNESCO World Heritage citadel with Sheesh Mahal, Naulakha Pavilion, and Elephant Stairs.",
                "description": "A magnificent fortification standing at the northern end of the Walled City.",
                "address": "Fort Road, Walled City, Lahore",
                "is_featured": True,
                "is_active": True,
                "verification_status": "verified",
            }
        )

        # 4. Jobs
        tech_cat, _ = JobCategory.objects.get_or_create(slug="software-it", defaults={"name": "Software & IT"})
        employer, _ = Employer.objects.get_or_create(
            slug="lahore-digital-labs",
            defaults={"name": "Lahore Digital Labs", "locality": gulberg, "address": "Main Boulevard, Gulberg III", "is_verified": True}
        )
        JobListing.objects.get_or_create(
            slug="senior-django-backend-engineer",
            defaults={
                "title": "Senior Django Backend Engineer",
                "employer": employer,
                "category": tech_cat,
                "locality": gulberg,
                "employment_type": "full_time",
                "experience_level": "senior",
                "salary_min_pkr": Decimal("250000.00"),
                "salary_max_pkr": Decimal("400000.00"),
                "description": "Lead the core backend architecture and high-throughput APIs for digital civic systems.",
                "deadline": timezone.now().date() + datetime.timedelta(days=45),
                "is_featured": True,
                "is_active": True,
                "verification_status": "verified",
            }
        )

        # 5. Restaurants
        desi_cuisine, _ = Cuisine.objects.get_or_create(slug="traditional-karahi", defaults={"name": "Traditional Karahi"})
        rooftop_feat, _ = RestaurantFeature.objects.get_or_create(slug="rooftop-view", defaults={"name": "Heritage Rooftop"})
        rest, _ = Restaurant.objects.get_or_create(
            slug="haveli-restaurant-fort-road",
            defaults={
                "title": "Haveli Restaurant - Fort Road",
                "locality": walled_city,
                "address": "Fort Road Food Street, Walled City, Lahore",
                "summary": "Rooftop heritage dining with breathtaking panoramic views of Badshahi Mosque and minarets.",
                "description": "Renowned for handi, mutton karahi, and traditional barbecue under floodlit monuments.",
                "price_tier": "$$$",
                "is_featured": True,
                "is_active": True,
                "verification_status": "verified",
            }
        )
        rest.cuisines.add(desi_cuisine)
        rest.features.add(rooftop_feat)

        # 6. Hospitals
        oncology, _ = MedicalSpecialty.objects.get_or_create(slug="oncology-cancer", defaults={"name": "Oncology"})
        cardiology, _ = MedicalSpecialty.objects.get_or_create(slug="cardiology", defaults={"name": "Cardiology"})
        hosp, _ = Hospital.objects.get_or_create(
            slug="shaukat-khanum-memorial-cancer-hospital",
            defaults={
                "title": "Shaukat Khanum Memorial Cancer Hospital",
                "locality": gulberg,
                "address": "7A Block R-3, Johar Town, Lahore",
                "summary": "World-class tertiary cancer center and charitable research hospital.",
                "description": "Comprehensive diagnostics, chemotherapy, and surgical oncology with 24/7 emergency response.",
                "hospital_type": "trust",
                "is_24_7_emergency": True,
                "ambulance_direct_phone": "042-35905000",
                "is_featured": True,
                "is_active": True,
                "verification_status": "verified",
            }
        )
        hosp.specialties.add(oncology, cardiology)

        # 7. Education
        uni_type, _ = EducationType.objects.get_or_create(slug="university", defaults={"name": "University"})
        hec, _ = AccreditationBoard.objects.get_or_create(name="Higher Education Commission", defaults={"abbreviation": "HEC"})
        inst, _ = Institution.objects.get_or_create(
            slug="government-college-university-lahore",
            defaults={
                "title": "Government College University (GCU) Lahore",
                "education_type": uni_type,
                "locality": walled_city,
                "address": "Katchery Road, Anarkali, Lahore",
                "summary": "Historic collegiate university established in 1864, celebrated for iconic Gothic architecture.",
                "description": "Alma mater of national leaders, poets, and Nobel laureates.",
                "established_year": 1864,
                "is_featured": True,
                "is_active": True,
                "verification_status": "verified",
            }
        )
        inst.accreditations.add(hec)

        # 8. Businesses
        craft_cat, _ = BusinessCategory.objects.get_or_create(slug="handicrafts", defaults={"name": "Handicrafts & Artisans"})
        Business.objects.get_or_create(
            slug="anarkali-royal-khussa-emporium",
            defaults={
                "title": "Anarkali Royal Khussa Emporium",
                "category": craft_cat,
                "locality": walled_city,
                "address": "Bano Bazaar, Old Anarkali, Lahore",
                "summary": "Handmade leather khussas, embroidered mojaris, and bridal footwear crafted by master artisans.",
                "description": "Established 1968, preserving royal Mughal leatherwork and velvet tilla embroidery.",
                "is_featured": True,
                "is_active": True,
                "verification_status": "verified",
            }
        )

        # 9. Events
        lit_cat, _ = EventCategory.objects.get_or_create(slug="literature-arts", defaults={"name": "Literature & Arts"})
        venue, _ = EventVenue.objects.get_or_create(
            slug="alhamra-arts-council",
            defaults={"name": "Alhamra Arts Council", "locality": gulberg, "address": "68 Mall Road, Lahore", "capacity": 1200}
        )
        event_start = timezone.now() + datetime.timedelta(days=14)
        Event.objects.get_or_create(
            slug="lahore-literary-festival-2026",
            defaults={
                "title": "Lahore Literary Festival (LLF) 2026",
                "category": lit_cat,
                "venue": venue,
                "start_datetime": event_start,
                "end_datetime": event_start + datetime.timedelta(days=3),
                "ticket_policy": "free",
                "organizer_name": "LLF Foundation",
                "description": "Pakistan's premier cultural gathering featuring global authors, poets, journalists, and historians.",
                "is_featured": True,
                "is_active": True,
            }
        )

        # 10. City Updates
        alert_cat, _ = UpdateCategory.objects.get_or_create(slug="air-quality", defaults={"name": "Air Quality & Environment"})
        CityUpdate.objects.get_or_create(
            slug="green-lockdown-air-quality-advisory",
            defaults={
                "title": "Green Lockdown & Air Quality Advisory for Central Lahore",
                "category": alert_cat,
                "severity": "caution",
                "summary": "Punjab EPA enforces emission controls, smog mitigation, and commercial hour regulations across Gulberg and Mall Road.",
                "content": "Heavy transport vehicles restricted during peak daytime hours. Air purifiers recommended for schools.",
                "issuing_authority": "Punjab Environment Protection Department",
                "official_source_url": "https://epd.punjab.gov.pk/advisories",
                "valid_from": timezone.now(),
                "is_pinned": True,
                "is_active": True,
            }
        )

        self.stdout.write(self.style.SUCCESS("Verified seed data successfully populated!"))
