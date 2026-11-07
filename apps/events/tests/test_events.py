import datetime
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.core.models import LocalityZone, Locality
from apps.events.models import EventCategory, EventVenue, Event
from apps.events.admin import EventCategoryAdmin, EventVenueAdmin, EventAdmin

User = get_user_model()


class EventsModuleTests(TestCase):
    """
    Comprehensive test suite for the Lahore Events, Expos & Festivals Calendar:
    1. Directory listing (upcoming, today, this weekend, this week, past archive)
    2. Category and ticketing policy filtering
    3. Keyword search (title, description, venue, organizer)
    4. Pagination handling (9 per page, out of bounds fallbacks)
    5. Event detail page (metadata, hero, venue directions, organizer, breadcrumbs)
    6. Expired event handling (warning alert, disabled booking, schema EventCompleted)
    7. Ongoing event handling (happening now alert)
    8. Publication permissions (inactive event returns 404 to public, 200 to staff)
    9. Data integrity & validation (end date < start date, negative prices, invalid URLs, file types)
    10. Schema.org/Event JSON-LD structured data inclusion only for qualifying events
    11. Admin moderation actions (publish, unpublish, mark featured, mark verified)
    """

    def setUp(self):
        self.client = Client()

        # Users
        self.regular_user = User.objects.create_user(
            username='lahore_resident',
            email='resident@lahorecityhub.pk',
            password='TestPassword123!'
        )
        self.staff_admin = User.objects.create_superuser(
            username='event_moderator',
            email='moderator@lahorecityhub.pk',
            password='AdminPassword123!'
        )

        # Geographic locality
        self.zone = LocalityZone.objects.create(name='Central Lahore', slug='central-lahore')
        self.locality = Locality.objects.create(
            name='The Mall / Shahrah-e-Quaid-e-Azam',
            slug='the-mall',
            zone=self.zone,
            postal_code='54000'
        )
        self.gulberg_locality = Locality.objects.create(
            name='Gulberg III',
            slug='gulberg-iii',
            zone=self.zone,
            postal_code='54660'
        )

        # Categories
        self.cat_literature = EventCategory.objects.create(
            name='Literature & Cultural Festivals',
            slug='literature-cultural-festivals',
            icon_class='bi-book'
        )
        self.cat_tech = EventCategory.objects.create(
            name='Conferences & Technology',
            slug='conferences-technology',
            icon_class='bi-cpu'
        )
        self.cat_food = EventCategory.objects.create(
            name='Food & Culinary Expos',
            slug='food-culinary-expos',
            icon_class='bi-egg-fried'
        )

        # Venues
        self.venue_alhamra = EventVenue.objects.create(
            name='Alhamra Arts Council',
            slug='alhamra-arts-council',
            address='68 Shahrah-e-Quaid-e-Azam, Mall Road, Lahore',
            locality=self.locality,
            capacity=1200,
            google_maps_url='https://maps.google.com/?q=Alhamra+Arts+Council+Lahore'
        )
        self.venue_expo = EventVenue.objects.create(
            name='Expo Centre Lahore',
            slug='expo-centre-lahore',
            address='1-A Abdul Haque Rd, Trade Centre Commercial Area Phase 2 Johar Town, Lahore',
            locality=self.locality,
            capacity=5000,
            google_maps_url='https://maps.google.com/?q=Expo+Centre+Lahore'
        )

        # Base times in Asia/Karachi
        self.now = timezone.now()
        local_today = timezone.localdate()

        # 1. Upcoming Event (Future: 3 days ahead)
        self.event_upcoming = Event.objects.create(
            title='Faiz International Festival 2026',
            slug='faiz-international-festival-2026',
            category=self.cat_literature,
            venue=self.venue_alhamra,
            start_datetime=self.now + datetime.timedelta(days=3),
            end_datetime=self.now + datetime.timedelta(days=3, hours=8),
            ticket_policy='free',
            ticket_price_pkr=0,
            organizer_name='Faiz Foundation Trust',
            organizer_contact='info@faizfestival.org',
            description='Celebration of Faiz Ahmed Faiz poetry, theater, music, and art performances at Alhamra halls.',
            is_featured=True,
            is_active=True,
            verification_status='verified',
            last_verified_at=self.now,
            source_url='https://faizfestival.org'
        )

        # 2. Ongoing Event (Started 1 hour ago, ends in 3 hours)
        self.event_ongoing = Event.objects.create(
            title='Lahore Eat Food Festival 2026',
            slug='lahore-eat-food-festival-2026',
            category=self.cat_food,
            venue=self.venue_alhamra,
            start_datetime=self.now - datetime.timedelta(hours=1),
            end_datetime=self.now + datetime.timedelta(hours=3),
            ticket_policy='ticketed',
            ticket_price_pkr=750.00,
            ticket_or_registration_url='https://tickets.lahoreeat.pk',
            organizer_name='CKO Event Architecture',
            organizer_contact='contact@lahoreeat.pk',
            description='Premier outdoor culinary festival showcasing traditional Lahori tastes and modern artisan food concepts.',
            is_featured=False,
            is_active=True,
            verification_status='verified',
            last_verified_at=self.now,
            source_url='https://lahoreeat.pk'
        )

        # 3. Expired / Past Event (Ended 10 days ago)
        self.event_expired = Event.objects.create(
            title='Lahore Biennale LB03 Retrospective',
            slug='lahore-biennale-lb03-retrospective',
            category=self.cat_literature,
            venue=self.venue_alhamra,
            start_datetime=self.now - datetime.timedelta(days=12),
            end_datetime=self.now - datetime.timedelta(days=10),
            ticket_policy='free',
            ticket_price_pkr=0,
            organizer_name='Lahore Biennale Foundation',
            description='Contemporary public art installations and artist talks reflecting on urban sustainability and heritage.',
            is_featured=False,
            is_active=True,
            verification_status='verified',
            last_verified_at=self.now - datetime.timedelta(days=15),
            source_url='https://lbf.org.pk'
        )

        # 4. Unpublished / Inactive Event
        self.event_inactive = Event.objects.create(
            title='Draft Tech Unconference 2026',
            slug='draft-tech-unconference-2026',
            category=self.cat_tech,
            venue=self.venue_expo,
            start_datetime=self.now + datetime.timedelta(days=10),
            end_datetime=self.now + datetime.timedelta(days=11),
            ticket_policy='registration',
            organizer_name='Tech Community Group',
            description='Unverified draft submission for tech meetups.',
            is_featured=False,
            is_active=False,
            verification_status='unverified'
        )

        # 5. Weekend Event (Scheduled for upcoming Saturday & Sunday)
        if local_today.weekday() == 6:  # Sunday
            sat_date = local_today - datetime.timedelta(days=1)
            sun_date = local_today
        else:
            days_to_sat = (5 - local_today.weekday()) % 7
            sat_date = local_today + datetime.timedelta(days=days_to_sat)
            sun_date = sat_date + datetime.timedelta(days=1)
        sat_start = timezone.make_aware(datetime.datetime.combine(sat_date, datetime.time(10, 0)))
        sat_end = timezone.make_aware(datetime.datetime.combine(sun_date, datetime.time(18, 0)))
        self.event_weekend = Event.objects.create(
            title='Lahore Weekend Craft and Artisan Bazaar',
            slug='lahore-weekend-craft-bazaar',
            category=self.cat_literature,
            venue=self.venue_alhamra,
            start_datetime=sat_start,
            end_datetime=sat_end,
            ticket_policy='free',
            organizer_name='Alhamra Arts Council',
            description='Weekend exhibition of traditional pottery, calligraphic crafts, and handwoven textiles.',
            is_featured=False,
            is_active=True,
            verification_status='verified'
        )

    # ==========================================
    # 1. Directory Listing & Visibility Tests
    # ==========================================

    def test_event_list_view_public_access(self):
        """Public listing returns 200 and displays upcoming active events by default."""
        url = reverse('events:list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'events/event_list.html')
        self.assertContains(response, 'Faiz International Festival 2026')
        self.assertContains(response, 'Lahore Eat Food Festival 2026')
        # Unpublished event must NEVER appear on public listing
        self.assertNotContains(response, 'Draft Tech Unconference 2026')
        # Expired event should not appear in default 'upcoming' list
        self.assertNotContains(response, 'Lahore Biennale LB03 Retrospective')

    def test_event_date_filter_upcoming_default(self):
        """Default date=upcoming only shows ongoing and future events."""
        url = reverse('events:list') + '?date=upcoming'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.event_upcoming.title)
        self.assertContains(response, self.event_ongoing.title)
        self.assertNotContains(response, self.event_expired.title)

    def test_event_date_filter_today(self):
        """date=today captures ongoing event active today."""
        url = reverse('events:list') + '?date=today'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.event_ongoing.title)
        # 3-day future event should not show on today
        self.assertNotContains(response, self.event_upcoming.title)
        self.assertNotContains(response, self.event_expired.title)

    def test_event_date_filter_this_weekend(self):
        """date=this_weekend captures events scheduled for Saturday or Sunday."""
        url = reverse('events:list') + '?date=this_weekend'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.event_weekend.title)
        self.assertNotContains(response, self.event_expired.title)

    def test_event_date_filter_past(self):
        """date=past displays concluded events archive."""
        url = reverse('events:list') + '?date=past'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.event_expired.title)
        # Future events should not be in past archive
        self.assertNotContains(response, self.event_upcoming.title)

    def test_event_date_filter_all(self):
        """date=all lists all active events across timeline."""
        url = reverse('events:list') + '?date=all'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.event_upcoming.title)
        self.assertContains(response, self.event_expired.title)
        self.assertContains(response, self.event_ongoing.title)
        # Inactive events still forbidden
        self.assertNotContains(response, self.event_inactive.title)

    # ==========================================
    # 2. Taxonomy & Filter Tests
    # ==========================================

    def test_category_filter(self):
        """Filtering by category returns only events within that domain."""
        url = reverse('events:list') + f'?category={self.cat_food.slug}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.event_ongoing.title)
        self.assertNotContains(response, self.event_upcoming.title)

    def test_ticket_policy_filter(self):
        """Filtering by ticket policy correctly segregates free and ticketed events."""
        # Free only
        url = reverse('events:list') + '?ticket=free'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.event_upcoming.title)
        self.assertNotContains(response, self.event_ongoing.title)

        # Ticketed only
        url_ticketed = reverse('events:list') + '?ticket=ticketed'
        resp_ticketed = self.client.get(url_ticketed)
        self.assertContains(resp_ticketed, self.event_ongoing.title)
        self.assertNotContains(resp_ticketed, self.event_upcoming.title)

    def test_keyword_search(self):
        """Search query matches event title, description, venue, or organizer."""
        # 1. Search by title keyword
        url = reverse('events:list') + '?q=Faiz'
        response = self.client.get(url)
        self.assertContains(response, self.event_upcoming.title)
        self.assertNotContains(response, self.event_ongoing.title)

        # 2. Search by venue name
        url_venue = reverse('events:list') + '?q=Alhamra'
        resp_venue = self.client.get(url_venue)
        self.assertContains(resp_venue, self.event_upcoming.title)

        # 3. Search by organizer
        url_org = reverse('events:list') + '?q=CKO'
        resp_org = self.client.get(url_org)
        self.assertContains(resp_org, self.event_ongoing.title)

        # 4. Non-matching search produces empty state
        url_none = reverse('events:list') + '?q=NonExistentFestivalXyz'
        resp_none = self.client.get(url_none)
        self.assertEqual(resp_none.status_code, 200)
        self.assertContains(resp_none, 'No Matching Events Found')

    # ==========================================
    # 3. Pagination Tests
    # ==========================================

    def test_event_pagination(self):
        """List view correctly paginates 9 events per page."""
        # Create additional events to exceed 9 items
        for i in range(10):
            Event.objects.create(
                title=f'Pagination Test Event {i}',
                slug=f'pagination-test-event-{i}',
                category=self.cat_literature,
                venue=self.venue_alhamra,
                start_datetime=self.now + datetime.timedelta(days=i + 5),
                end_datetime=self.now + datetime.timedelta(days=i + 5, hours=2),
                ticket_policy='free',
                organizer_name='Test Organizer',
                description=f'Test pagination description {i}',
                is_active=True
            )

        url = reverse('events:list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_paginated'])
        self.assertEqual(len(response.context['events']), 9)

        # Page 2
        resp_p2 = self.client.get(url + '?page=2')
        self.assertEqual(resp_p2.status_code, 200)
        self.assertGreaterEqual(len(resp_p2.context['events']), 1)

        # Out-of-bounds page falls back to page 1
        resp_invalid = self.client.get(url + '?page=9999')
        self.assertEqual(resp_invalid.status_code, 200)

    # ==========================================
    # 4. Detail View & Expired Handling
    # ==========================================

    def test_event_detail_active_upcoming(self):
        """Active upcoming event displays full details, venue, dates, and Schema.org LD-JSON."""
        url = reverse('events:detail', kwargs={'slug': self.event_upcoming.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'events/event_detail.html')
        self.assertContains(response, 'Faiz International Festival 2026')
        self.assertContains(response, 'Alhamra Arts Council')
        self.assertContains(response, 'Faiz Foundation Trust')
        self.assertContains(response, '68 Shahrah-e-Quaid-e-Azam')
        # Schema.org structured data check
        self.assertContains(response, '"@type": "Event"')
        self.assertContains(response, '"@type": "Place"')
        self.assertContains(response, 'https://schema.org/EventScheduled')

    def test_event_detail_ongoing_banner(self):
        """Ongoing event displays the 'Happening Right Now!' alert."""
        url = reverse('events:detail', kwargs={'slug': self.event_ongoing.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Happening Right Now!')
        self.assertContains(response, 'https://tickets.lahoreeat.pk')

    def test_event_detail_expired_handling(self):
        """Expired event displays concluded alert, disables bookings, and updates schema status."""
        url = reverse('events:detail', kwargs={'slug': self.event_expired.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This Event Has Concluded')
        self.assertContains(response, 'Registration Concluded')
        self.assertContains(response, 'https://schema.org/EventCompleted')

    # ==========================================
    # 5. Publication Status & Security Permissions
    # ==========================================

    def test_inactive_event_hidden_from_public(self):
        """Unpublished/inactive event returns 404 to anonymous visitors."""
        url = reverse('events:detail', kwargs={'slug': self.event_inactive.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_inactive_event_hidden_from_regular_users(self):
        """Unpublished/inactive event returns 404 to regular authenticated users."""
        self.client.force_login(self.regular_user)
        url = reverse('events:detail', kwargs={'slug': self.event_inactive.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_inactive_event_accessible_to_staff(self):
        """Staff members can preview unpublished/inactive events for editorial review."""
        self.client.force_login(self.staff_admin)
        url = reverse('events:detail', kwargs={'slug': self.event_inactive.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Draft Tech Unconference 2026')

    # ==========================================
    # 6. Data Integrity & Validation Tests
    # ==========================================

    def test_end_datetime_before_start_datetime_raises_validation_error(self):
        """Event end datetime cannot precede start datetime."""
        invalid_event = Event(
            title='Invalid Timeline Event',
            category=self.cat_literature,
            venue=self.venue_alhamra,
            start_datetime=self.now + datetime.timedelta(days=2),
            end_datetime=self.now + datetime.timedelta(days=1),  # earlier than start
            ticket_policy='free',
            organizer_name='Error Organizer',
            description='Test event with invalid temporal sequence.'
        )
        with self.assertRaises(ValidationError) as ctx:
            invalid_event.full_clean()
        self.assertIn('end_datetime', ctx.exception.message_dict)

    def test_negative_ticket_price_raises_validation_error(self):
        """Ticket price cannot be negative."""
        invalid_price = Event(
            title='Invalid Price Event',
            category=self.cat_literature,
            venue=self.venue_alhamra,
            start_datetime=self.now + datetime.timedelta(days=1),
            end_datetime=self.now + datetime.timedelta(days=1, hours=2),
            ticket_policy='ticketed',
            ticket_price_pkr=-150.00,
            organizer_name='Error Organizer',
            description='Test invalid price.'
        )
        with self.assertRaises(ValidationError) as ctx:
            invalid_price.full_clean()
        self.assertIn('ticket_price_pkr', ctx.exception.message_dict)

    def test_invalid_urls_raise_validation_error(self):
        """Invalid booking or source URL schemes raise ValidationError."""
        invalid_url_event = Event(
            title='Invalid URL Event',
            category=self.cat_literature,
            venue=self.venue_alhamra,
            start_datetime=self.now + datetime.timedelta(days=1),
            end_datetime=self.now + datetime.timedelta(days=1, hours=2),
            ticket_policy='free',
            ticket_or_registration_url='ftp://not-allowed-scheme.com',
            source_url='javascript:alert(1)',
            organizer_name='Error Organizer',
            description='Test invalid URLs.'
        )
        with self.assertRaises(ValidationError) as ctx:
            invalid_url_event.full_clean()
        self.assertTrue('ticket_or_registration_url' in ctx.exception.message_dict or 'source_url' in ctx.exception.message_dict)

    def test_invalid_image_extension_raises_validation_error(self):
        """Unsupported image file extension raises ValidationError."""
        fake_executable = SimpleUploadedFile("malicious.exe", b"binary_content", content_type="application/x-msdownload")
        invalid_img_event = Event(
            title='Invalid Image Event',
            category=self.cat_literature,
            venue=self.venue_alhamra,
            start_datetime=self.now + datetime.timedelta(days=1),
            end_datetime=self.now + datetime.timedelta(days=1, hours=2),
            ticket_policy='free',
            organizer_name='Error Organizer',
            banner_image=fake_executable,
            description='Test invalid image file.'
        )
        with self.assertRaises(ValidationError) as ctx:
            invalid_img_event.full_clean()
        self.assertIn('banner_image', ctx.exception.message_dict)

    # ==========================================
    # 7. Model Properties & Timezone Formatting
    # ==========================================

    def test_model_properties_and_slug_generation(self):
        """Verify model properties: address, aliases, status flags, and unique slug generation."""
        # Test custom address override
        custom_event = Event.objects.create(
            title='Hall 2 Exclusive Reading',
            category=self.cat_literature,
            venue=self.venue_alhamra,
            custom_address='Hall No. 2, Alhamra Cultural Complex, Gaddafi Stadium, Ferozepur Rd',
            start_datetime=self.now + datetime.timedelta(days=4),
            end_datetime=self.now + datetime.timedelta(days=4, hours=3),
            ticket_policy='free',
            organizer_name='Lahore Arts Forum',
            description='Special poetry session.'
        )
        self.assertEqual(custom_event.address, 'Hall No. 2, Alhamra Cultural Complex, Gaddafi Stadium, Ferozepur Rd')
        # Venue fallback
        self.assertEqual(self.event_upcoming.address, self.venue_alhamra.address)

        # Aliases
        self.assertEqual(self.event_upcoming.organizer, self.event_upcoming.organizer_name)
        self.assertEqual(self.event_upcoming.booking_url, self.event_upcoming.ticket_or_registration_url)

        # Status properties
        self.assertTrue(self.event_expired.is_expired)
        self.assertFalse(self.event_expired.is_upcoming)
        self.assertTrue(self.event_upcoming.is_upcoming)
        self.assertFalse(self.event_upcoming.is_expired)

        # Date & Time formatted string in local Asia/Karachi time
        self.assertTrue(len(self.event_upcoming.date_str) > 0)
        self.assertTrue(len(self.event_upcoming.time_str) > 0)

        # Auto slug increment on collision
        duplicate_event = Event.objects.create(
            title='Faiz International Festival 2026',
            category=self.cat_literature,
            venue=self.venue_alhamra,
            start_datetime=self.now + datetime.timedelta(days=5),
            end_datetime=self.now + datetime.timedelta(days=5, hours=2),
            ticket_policy='free',
            organizer_name='Faiz Trust',
            description='Duplicate title test.'
        )
        self.assertNotEqual(duplicate_event.slug, self.event_upcoming.slug)
        self.assertTrue(duplicate_event.slug.startswith('faiz-international-festival-2026-'))

    # ==========================================
    # 8. Admin Moderation Actions
    # ==========================================

    def test_admin_moderation_actions(self):
        """Admin actions correctly toggle publication, featured status, and verification."""
        model_admin = EventAdmin(Event, None)
        qs = Event.objects.filter(pk=self.event_inactive.pk)

        # 1. Publish
        model_admin.publish_events(None, qs)
        self.event_inactive.refresh_from_db()
        self.assertTrue(self.event_inactive.is_active)

        # 2. Mark Featured
        model_admin.mark_as_featured(None, qs)
        self.event_inactive.refresh_from_db()
        self.assertTrue(self.event_inactive.is_featured)

        # 3. Unmark Featured
        model_admin.unmark_featured(None, qs)
        self.event_inactive.refresh_from_db()
        self.assertFalse(self.event_inactive.is_featured)

        # 4. Mark Verified
        model_admin.mark_as_verified(None, qs)
        self.event_inactive.refresh_from_db()
        self.assertEqual(self.event_inactive.verification_status, 'verified')
        self.assertIsNotNone(self.event_inactive.last_verified_at)

        # 5. Unpublish
        model_admin.unpublish_events(None, qs)
        self.event_inactive.refresh_from_db()
        self.assertFalse(self.event_inactive.is_active)
