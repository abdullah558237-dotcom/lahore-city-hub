import datetime
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from apps.core.models import LocalityZone, Locality
from apps.transport.models import TransitMode, TransitRoute, TransitStation, TransitGuide
from apps.transport.admin import TransitRouteAdmin, TransitGuideAdmin

User = get_user_model()


class TransportInformationModuleTests(TestCase):
    """
    Comprehensive test suite for the Lahore Public Transit Information Module:
    - Overview page rendering with modal cards, search, and emergency helpline
    - Route directory with mode filters, search, and sorting
    - Route detail with station sequence, fares, operating hours, and schema markup
    - Publication and isolation permissions for inactive routes (404 for public)
    - Station directory with interchange and underground filters
    - Station detail with next/previous stop navigation and landmark links
    - Travel advice and commuter guides with category filtering
    - Publication permissions for unpublished guides (404 for public)
    - Data integrity and validation rules (negative distance, invalid URLs)
    - Admin actions for route activation, feature flags, and guide publishing
    """

    def setUp(self):
        self.client = Client()

        # Users
        self.regular_user = User.objects.create_user(
            username='commuter_ali',
            email='ali@example.pk',
            password='Password123!'
        )
        self.staff_admin = User.objects.create_superuser(
            username='transit_admin',
            email='transitadmin@lahorecityhub.pk',
            password='AdminPassword123!'
        )

        # Localities
        self.zone_walled = LocalityZone.objects.create(name="Walled City Zone", slug="walled-city-zone")
        self.zone_central = LocalityZone.objects.create(name="Central Lahore", slug="central-lahore")

        self.loc_anarkali = Locality.objects.create(
            zone=self.zone_walled, name="Old Anarkali", slug="old-anarkali", postal_code="54000"
        )
        self.loc_gulberg = Locality.objects.create(
            zone=self.zone_central, name="Gulberg II", slug="gulberg-2", postal_code="54660"
        )

        # Transit Modes
        self.mode_train = TransitMode.objects.create(
            name="Orange Line Metro Train",
            slug="orange-line-metro-train",
            icon_class="bi-train-front",
            description="Automated rapid transit line",
            is_active=True
        )
        self.mode_brt = TransitMode.objects.create(
            name="Metrobus BRT (Green Line)",
            slug="metrobus-brt",
            icon_class="bi-bus-front",
            description="Bus rapid transit corridor",
            is_active=True
        )

        today = datetime.date(2026, 11, 1)

        # Active Orange Line Route
        self.route_olmt = TransitRoute.objects.create(
            mode=self.mode_train,
            route_name="Orange Line Metro Train",
            route_code="OLMT-01",
            slug="orange-line-metro-train",
            origin_station="Ali Town",
            destination_station="Dera Gujran",
            total_stations=26,
            total_distance_km=27.10,
            operating_schedule="06:00 AM – 10:00 PM Daily",
            frequency="Every 5–8 minutes",
            fare_info="PKR 20 for up to 4 km; PKR 25 (4–8 km); PKR 30 (8–12 km); PKR 35 (12–16 km); PKR 40 (16+ km).",
            description="Connects Ali Town to Dera Gujran across 27.1 km.",
            operator="Punjab Masstransit Authority (PMA)",
            source_url="https://pma.punjab.gov.pk/orange_line_metro_train",
            last_updated_date=today,
            is_active=True,
            is_featured=True
        )

        # Active Metrobus Route
        self.route_mb = TransitRoute.objects.create(
            mode=self.mode_brt,
            route_name="Lahore Metrobus Green Line",
            route_code="MB-01",
            slug="lahore-metrobus-green-line",
            origin_station="Shahdara",
            destination_station="Gajjumata",
            total_stations=27,
            total_distance_km=27.00,
            operating_schedule="06:00 AM – 10:30 PM Daily",
            frequency="Every 3–5 minutes",
            fare_info="Flat PKR 30 per trip via Metro Token or Card.",
            description="Dedicated corridor from Shahdara to Gajjumata.",
            operator="Punjab Masstransit Authority (PMA)",
            source_url="https://pma.punjab.gov.pk/lahore_metrobus_system",
            last_updated_date=today,
            is_active=True,
            is_featured=True
        )

        # Inactive / Proposed Route
        self.route_inactive = TransitRoute.objects.create(
            mode=self.mode_train,
            route_name="Blue Line Metro Train (Proposed)",
            route_code="BLMT-01",
            slug="blue-line-metro-train",
            origin_station="Lahore Airport",
            destination_station="Rawind",
            total_stations=20,
            total_distance_km=24.00,
            operating_schedule="Not in operation",
            fare_info="TBD",
            description="Proposed transit route currently inactive.",
            is_active=False,
            is_featured=False
        )

        # Stations for Orange Line
        self.station_ali = TransitStation.objects.create(
            route=self.route_olmt,
            station_name="Ali Town",
            urdu_name="علی ٹاؤن",
            slug="olmt-ali-town",
            station_number=1,
            locality=self.loc_gulberg,
            is_terminal=True,
            is_interchange=False,
            is_underground=False,
            nearby_landmarks="Raiwind Road bypass"
        )
        self.station_anarkali = TransitStation.objects.create(
            route=self.route_olmt,
            station_name="Anarkali",
            urdu_name="انارکلی",
            slug="olmt-anarkali",
            station_number=14,
            locality=self.loc_anarkali,
            is_terminal=False,
            is_interchange=True,
            is_underground=True,
            interchange_details="Interchange with Metrobus MAO College station.",
            nearby_landmarks="Anarkali Bazaar, Lahore Museum, Mall Road",
            source_url="https://pma.punjab.gov.pk",
            last_verified_date=today
        )
        self.station_dera = TransitStation.objects.create(
            route=self.route_olmt,
            station_name="Dera Gujran",
            urdu_name="ڈیرہ گجراں",
            slug="olmt-dera-gujran",
            station_number=26,
            locality=self.loc_anarkali,
            is_terminal=True,
            is_interchange=False,
            is_underground=False,
            nearby_landmarks="GT Road terminal"
        )

        # Stations for Metrobus
        self.station_shahdara = TransitStation.objects.create(
            route=self.route_mb,
            station_name="Shahdara",
            urdu_name="شاہدرہ",
            slug="metrobus-shahdara",
            station_number=1,
            locality=self.loc_anarkali,
            is_terminal=True,
            is_interchange=True,
            nearby_landmarks="Ravi River Bridge"
        )

        # Travel Guides
        self.guide_cards = TransitGuide.objects.create(
            title="How to Buy and Use Metro Smart Cards",
            slug="how-to-buy-and-use-metro-smart-cards",
            category="smart_cards",
            route=self.route_olmt,
            summary="Complete guide to purchasing permanent reloadable Punjab Masstransit cards.",
            content="Detailed steps for TVM tokens and card registration...",
            source_url="https://pma.punjab.gov.pk",
            last_verified_date=today,
            is_published=True,
            is_featured=True,
            display_order=1
        )
        self.guide_unpublished = TransitGuide.objects.create(
            title="Draft Internal Safety Procedure",
            slug="draft-internal-safety-procedure",
            category="rules_safety",
            route=self.route_olmt,
            summary="Draft guide undergoing editorial review.",
            content="Internal content...",
            is_published=False,
            is_featured=False,
            display_order=99
        )

    # =========================================================================
    # 1. OVERVIEW & SEARCH TESTS
    # =========================================================================

    def test_transit_overview_page_renders_successfully(self):
        """Transit hub overview must return HTTP 200 and display main rapid transit routes."""
        url = reverse('transport:overview')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Orange Line Metro Train")
        self.assertContains(response, "Lahore Metrobus")
        self.assertContains(response, "042-111-222-627")
        self.assertContains(response, "Anarkali")

    def test_transit_overview_search(self):
        """Searching 'Anarkali' locates matching stations."""
        url = reverse('transport:overview') + "?q=Anarkali"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Anarkali")
        self.assertContains(response, 'Search Results for "Anarkali"')

    # =========================================================================
    # 2. ROUTE DIRECTORY & FILTER TESTS
    # =========================================================================

    def test_route_list_public_only_shows_active_routes(self):
        """Route listing must display active routes and exclude inactive ones."""
        url = reverse('transport:route_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Orange Line Metro Train")
        self.assertContains(response, "Lahore Metrobus Green Line")
        self.assertNotContains(response, "Blue Line Metro Train (Proposed)")

    def test_route_list_mode_filter(self):
        """Filtering by mode slug isolates corresponding routes."""
        url = reverse('transport:route_list') + f"?mode={self.mode_train.slug}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Orange Line Metro Train")
        self.assertNotContains(response, "Lahore Metrobus Green Line")

    def test_route_list_search_query(self):
        """Search by terminal station name 'Shahdara' finds Metrobus route."""
        url = reverse('transport:route_list') + "?q=Shahdara"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "MB-01")
        self.assertNotContains(response, "OLMT-01")
        self.assertEqual(len(response.context['routes']), 1)

    def test_route_list_sorting(self):
        """Sorting by distance orders routes properly."""
        url = reverse('transport:route_list') + "?sort=distance"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        routes = list(response.context['routes'])
        self.assertGreaterEqual(routes[0].total_distance_km, routes[-1].total_distance_km)

    # =========================================================================
    # 3. ROUTE DETAIL & PUBLICATION ISOLATION TESTS
    # =========================================================================

    def test_route_detail_active_public_access(self):
        """Active route detail page is publicly visible with stops and fares."""
        url = reverse('transport:route_detail', kwargs={'slug': self.route_olmt.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Orange Line Metro Train")
        self.assertContains(response, "Ali Town")
        self.assertContains(response, "Dera Gujran")
        self.assertContains(response, "PKR 20 for up to 4 km")
        self.assertContains(response, "Punjab Masstransit Authority (PMA)")
        self.assertContains(response, "https://pma.punjab.gov.pk/orange_line_metro_train")
        self.assertContains(response, "BusTrip")

    def test_route_detail_inactive_hidden_from_public(self):
        """Inactive route returns HTTP 404 to anonymous and regular users."""
        url = reverse('transport:route_detail', kwargs={'slug': self.route_inactive.slug})

        # Anonymous visitor
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # Authenticated non-staff commuter
        self.client.login(username='commuter_ali', password='Password123!')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_route_detail_inactive_visible_to_staff(self):
        """Staff members can preview inactive routes."""
        self.client.login(username='transit_admin', password='AdminPassword123!')
        url = reverse('transport:route_detail', kwargs={'slug': self.route_inactive.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Blue Line Metro Train (Proposed)")

    # =========================================================================
    # 4. STATION DIRECTORY & DETAIL TESTS
    # =========================================================================

    def test_station_list_filtering(self):
        """Stations list supports filtering by line and interchange."""
        url = reverse('transport:station_list') + f"?route={self.route_olmt.slug}&interchange=1"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Anarkali")
        self.assertNotContains(response, "Shahdara")

    def test_station_detail_page(self):
        """Station detail page displays landmarks, line sequence, and next/prev stops."""
        url = reverse('transport:station_detail', kwargs={'slug': self.station_anarkali.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Anarkali")
        self.assertContains(response, "انارکلی")
        self.assertContains(response, "Stop #14")
        self.assertContains(response, "Interchange Hub")
        self.assertContains(response, "Underground")
        self.assertContains(response, "Anarkali Bazaar, Lahore Museum, Mall Road")

    def test_station_detail_inactive_route_returns_404(self):
        """Station on an inactive route returns 404 to non-staff."""
        station_inactive = TransitStation.objects.create(
            route=self.route_inactive,
            station_name="Airport Terminal",
            slug="blmt-airport-terminal",
            station_number=1,
            locality=self.loc_gulberg
        )
        url = reverse('transport:station_detail', kwargs={'slug': station_inactive.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    # =========================================================================
    # 5. TRAVEL GUIDES & COMMUTER ADVICE TESTS
    # =========================================================================

    def test_guide_list_filtering(self):
        """Guides list filters by category and keyword search."""
        url = reverse('transport:guide_list') + "?category=smart_cards"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "How to Buy and Use Metro Smart Cards")

    def test_guide_detail_published(self):
        """Published travel guide displays rich instructions, verified date, and PMA source."""
        url = reverse('transport:guide_detail', kwargs={'slug': self.guide_cards.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "How to Buy and Use Metro Smart Cards")
        self.assertContains(response, "November 2026")
        self.assertContains(response, "https://pma.punjab.gov.pk")

    def test_guide_detail_unpublished_hidden_from_public(self):
        """Unpublished guide returns 404 to regular users and 200 to staff."""
        url = reverse('transport:guide_detail', kwargs={'slug': self.guide_unpublished.slug})

        # Public access
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # Staff preview
        self.client.login(username='transit_admin', password='AdminPassword123!')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    # =========================================================================
    # 6. MODEL VALIDATION CONSTRAINTS
    # =========================================================================

    def test_model_validation_constraints(self):
        """Negative distance, invalid URLs, and station numbers < 1 must raise ValidationError."""
        # 1. Invalid distance
        bad_route = TransitRoute(
            mode=self.mode_train,
            route_name="Bad Route",
            route_code="BAD-01",
            total_stations=1,
            total_distance_km=-5.00
        )
        with self.assertRaises(ValidationError):
            bad_route.clean()

        # 2. Invalid source URL
        bad_url_route = TransitRoute(
            mode=self.mode_train,
            route_name="Bad URL Route",
            route_code="BAD-02",
            total_stations=1,
            total_distance_km=10.00,
            source_url="not-a-valid-http-url"
        )
        with self.assertRaises(ValidationError):
            bad_url_route.clean()

        # 3. Invalid station number
        bad_station = TransitStation(
            route=self.route_olmt,
            station_name="Invalid Zero Station",
            station_number=0
        )
        with self.assertRaises(ValidationError):
            bad_station.clean()

    # =========================================================================
    # 7. ADMIN ACTION TESTS
    # =========================================================================

    def test_admin_actions(self):
        """Admin actions correctly activate routes and publish guides."""
        admin_route = TransitRouteAdmin(TransitRoute, None)
        request = self.client.request().wsgi_request
        request.user = self.staff_admin

        # Activate inactive route
        admin_route.make_active(request, TransitRoute.objects.filter(pk=self.route_inactive.pk))
        self.route_inactive.refresh_from_db()
        self.assertTrue(self.route_inactive.is_active)

        # Deactivate route
        admin_route.make_inactive(request, TransitRoute.objects.filter(pk=self.route_inactive.pk))
        self.route_inactive.refresh_from_db()
        self.assertFalse(self.route_inactive.is_active)

        # Publish guide
        admin_guide = TransitGuideAdmin(TransitGuide, None)
        admin_guide.publish_guides(request, TransitGuide.objects.filter(pk=self.guide_unpublished.pk))
        self.guide_unpublished.refresh_from_db()
        self.assertTrue(self.guide_unpublished.is_published)
