import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify
from apps.core.models import Locality
from apps.events.models import EventCategory, EventVenue, Event


class Command(BaseCommand):
    help = "Seeds verified upcoming and concluded civic and cultural events in Lahore."

    def handle(self, *args, **options):
        self.stdout.write("Seeding Lahore Events Information...")

        loc_walled = Locality.objects.filter(slug='walled-city').first()
        loc_gulberg = Locality.objects.filter(slug='gulberg-3').first()

        # 1. Event Categories
        cat_lit, _ = EventCategory.objects.get_or_create(
            name="Literature & Cultural Festivals",
            defaults={'slug': 'literature-culture', 'icon_class': 'bi-book-half', 'is_active': True}
        )
        cat_food, _ = EventCategory.objects.get_or_create(
            name="Food & Culinary Expos",
            defaults={'slug': 'food-culinary', 'icon_class': 'bi-cup-hot', 'is_active': True}
        )
        cat_tech, _ = EventCategory.objects.get_or_create(
            name="Conferences & Technology",
            defaults={'slug': 'conferences-tech', 'icon_class': 'bi-laptop', 'is_active': True}
        )
        cat_arts, _ = EventCategory.objects.get_or_create(
            name="Arts & Exhibitions",
            defaults={'slug': 'arts-exhibitions', 'icon_class': 'bi-palette', 'is_active': True}
        )
        cat_sports, _ = EventCategory.objects.get_or_create(
            name="Heritage & Sports",
            defaults={'slug': 'heritage-sports', 'icon_class': 'bi-trophy', 'is_active': True}
        )

        # 2. Event Venues
        venue_alhamra, _ = EventVenue.objects.get_or_create(
            name="Alhamra Arts Council",
            defaults={
                'slug': 'alhamra-arts-council',
                'address': '68 Shahrah-e-Quaid-e-Azam (The Mall), Lahore',
                'locality': loc_walled,
                'capacity': 1800,
                'google_maps_url': 'https://maps.google.com/?q=Alhamra+Arts+Council+Lahore'
            }
        )
        venue_expo, _ = EventVenue.objects.get_or_create(
            name="Expo Centre Lahore",
            defaults={
                'slug': 'expo-centre-lahore',
                'address': '1-A Trade Centre Commercial Area, MA Johar Town, Lahore',
                'locality': loc_gulberg,
                'capacity': 10000,
                'google_maps_url': 'https://maps.google.com/?q=Expo+Centre+Lahore'
            }
        )
        venue_fortress, _ = EventVenue.objects.get_or_create(
            name="Fortress Stadium Grounds",
            defaults={
                'slug': 'fortress-stadium-grounds',
                'address': 'Fortress Stadium, Lahore Cantonment, Lahore',
                'locality': loc_gulberg,
                'capacity': 15000,
                'google_maps_url': 'https://maps.google.com/?q=Fortress+Stadium+Lahore'
            }
        )

        now = timezone.now()

        # 3. Events:
        # Event 1: LLF (Upcoming, Featured, Free)
        start_llf = now + datetime.timedelta(days=12)
        end_llf = start_llf + datetime.timedelta(days=3)
        Event.objects.update_or_create(
            slug="lahore-literary-festival-2026",
            defaults={
                'title': "Lahore Literary Festival (LLF) 2026",
                'category': cat_lit,
                'venue': venue_alhamra,
                'start_datetime': start_llf,
                'end_datetime': end_llf,
                'ticket_policy': 'free',
                'organizer_name': "Lahore Literary Festival Foundation",
                'organizer_contact': "info@lahorelitfest.com",
                'description': "Annual international literary gathering celebrating literature, poetry, architecture, and contemporary thought at Alhamra Arts Council.",
                'source_url': "https://lahorelitfest.com",
                'is_featured': True,
                'is_active': True,
                'verification_status': 'verified',
            }
        )

        # Event 2: Faiz Festival (Upcoming)
        start_faiz = now + datetime.timedelta(days=25)
        end_faiz = start_faiz + datetime.timedelta(days=2)
        Event.objects.update_or_create(
            slug="faiz-festival-2026",
            defaults={
                'title': "Faiz Festival 2026",
                'category': cat_lit,
                'venue': venue_alhamra,
                'start_datetime': start_faiz,
                'end_datetime': end_faiz,
                'ticket_policy': 'free',
                'organizer_name': "Faiz Foundation Trust",
                'organizer_contact': "contact@faizfestival.org",
                'description': "Celebrating the life, poetry, and progressive ideals of Faiz Ahmad Faiz through theatrical plays, musical performances, and panel sessions.",
                'source_url': "https://faizfoundationtrust.org",
                'is_featured': False,
                'is_active': True,
                'verification_status': 'verified',
            }
        )

        # Event 3: Lahore Eat Food Festival (Upcoming, Ticketed)
        start_eat = now + datetime.timedelta(days=18)
        end_eat = start_eat + datetime.timedelta(days=2)
        Event.objects.update_or_create(
            slug="lahore-eat-food-festival-2026",
            defaults={
                'title': "Lahore Eat Food Festival 2026",
                'category': cat_food,
                'venue': venue_fortress,
                'start_datetime': start_eat,
                'end_datetime': end_eat,
                'ticket_policy': 'ticketed',
                'ticket_price_pkr': 500.00,
                'ticket_or_registration_url': "https://eatfoodpakistan.com/tickets",
                'organizer_name': "Eat Food Pakistan",
                'organizer_contact': "+92-42-35789900",
                'description': "Lahore's flagship outdoor culinary weekend bringing together traditional street food masters and contemporary home chefs.",
                'source_url': "https://eatfoodpakistan.com",
                'is_featured': True,
                'is_active': True,
                'verification_status': 'verified',
            }
        )

        # Event 4: National IT Summit (Upcoming, Registration Required)
        start_tech = now + datetime.timedelta(days=7)
        end_tech = start_tech + datetime.timedelta(days=1)
        Event.objects.update_or_create(
            slug="national-it-summit-lahore-2026",
            defaults={
                'title': "National IT & Tech Summit Lahore 2026",
                'category': cat_tech,
                'venue': venue_expo,
                'start_datetime': start_tech,
                'end_datetime': end_tech,
                'ticket_policy': 'registration',
                'ticket_or_registration_url': "https://pitb.gov.pk/registration",
                'organizer_name': "Punjab Information Technology Board (PITB)",
                'organizer_contact': "summit@pitb.gov.pk",
                'description': "Showcase of Pakistan's software exports, venture capital panels, AI workshops, and university startup exhibits.",
                'source_url': "https://pitb.gov.pk",
                'is_featured': False,
                'is_active': True,
                'verification_status': 'verified',
            }
        )

        # Event 5: Past / Expired Event (For testing past event handling)
        start_past = now - datetime.timedelta(days=30)
        end_past = start_past + datetime.timedelta(days=3)
        Event.objects.update_or_create(
            slug="lahore-biennale-03-retrospective",
            defaults={
                'title': "Lahore Biennale (LB03) Retrospective",
                'category': cat_arts,
                'venue': venue_alhamra,
                'start_datetime': start_past,
                'end_datetime': end_past,
                'ticket_policy': 'free',
                'organizer_name': "Lahore Biennale Foundation",
                'organizer_contact': "biennale@lbf.org.pk",
                'description': "Public contemporary art exhibitions and site-specific architectural installations in historical spaces.",
                'source_url': "https://lahorebiennale.org",
                'is_featured': False,
                'is_active': True,
                'verification_status': 'verified',
            }
        )

        self.stdout.write(self.style.SUCCESS("Successfully seeded Lahore events data!"))
