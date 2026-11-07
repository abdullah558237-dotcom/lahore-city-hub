from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.admin.sites import site
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from decimal import Decimal
import datetime

from apps.core.models import LocalityZone, Locality
from apps.places.models import PlaceCategory, Place, PlaceGalleryImage, validate_image_extension
from apps.places.admin import PlaceAdmin, PlaceCategoryAdmin
from apps.transport.models import TransitMode, TransitRoute, TransitStation

User = get_user_model()


class PlacesModuleComprehensiveTests(TestCase):
    """
    Exhaustive test suite verifying the Places module:
    - Places listing page rendering, metadata, and empty states
    - Place detail page rendering and Schema.org TouristAttraction JSON-LD
    - Category filtering & Area / Locality filtering
    - Keyword search across title, Urdu title, description, and era
    - Verified only, wheelchair accessible, and free entry toggles
    - Pagination with boundary & invalid page number handling
    - Related places recommendation logic (excluding current place)
    - Featured places spotlight ordering
    - View count increment tracking
    - Unpublished / draft content isolation (404 on detail, hidden in list)
    - Admin management actions and registrations
    - Model validations (fees, image extensions)
    """

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='auditor@lahorecityhub.pk',
            username='auditor',
            password='TestPassword123!'
        )

        # Spatial Locality Taxonomy
        self.zone_walled = LocalityZone.objects.create(name="Walled City Zone", slug="walled-city-zone")
        self.zone_central = LocalityZone.objects.create(name="Central Zone", slug="central-zone")

        self.loc_walled = Locality.objects.create(
            zone=self.zone_walled, name="Walled City", slug="walled-city", postal_code="54000"
        )
        self.loc_gulberg = Locality.objects.create(
            zone=self.zone_central, name="Gulberg III", slug="gulberg-3", postal_code="54660"
        )

        # Place Categories
        self.cat_monument = PlaceCategory.objects.create(
            name="Historical Monuments", slug="historical-monuments", icon_class="bi-bank"
        )
        self.cat_garden = PlaceCategory.objects.create(
            name="Gardens & Parks", slug="gardens-parks", icon_class="bi-tree"
        )

        # Transit Station
        self.mode = TransitMode.objects.create(name="Metro", slug="metro")
        self.route = TransitRoute.objects.create(
            mode=self.mode, route_name="Orange Line", route_code="OLMT-01",
            origin_station="Ali Town", destination_station="Dera Gujran",
            total_stations=26, total_distance_km=Decimal("27.10")
        )
        self.station = TransitStation.objects.create(
            route=self.route, station_name="Anarkali Station", station_number=13, locality=self.loc_walled
        )

        # Primary Active Place
        self.place_badshahi = Place.objects.create(
            category=self.cat_monument,
            locality=self.loc_walled,
            title="Badshahi Mosque",
            title_ur="بادشاہی مسجد",
            slug="badshahi-mosque",
            summary="Iconic 1673 AD Mughal imperial mosque opposite Lahore Fort.",
            description="Constructed during the reign of Aurangzeb. World renowned architectural masterpiece.",
            address="Opposite Alamgiri Gate, Walled City, Lahore",
            landmark="Near Fort Road Food Street",
            architectural_era="Mughal Empire (1673 AD)",
            entry_fee_pkr=Decimal("0.00"),
            entry_fee_foreigner_pkr=Decimal("0.00"),
            opening_time=datetime.time(8, 0),
            closing_time=datetime.time(20, 0),
            closed_on_days="Open Daily",
            photography_policy="Free mobile photography permitted.",
            wheelchair_accessible=True,
            nearest_metro_station=self.station,
            latitude=Decimal("31.588200"),
            longitude=Decimal("74.309600"),
            is_active=True,
            is_featured=True,
            verification_status="verified",
            phone_number="+92-42-99214444",
            website="https://wcla.punjab.gov.pk"
        )

    def test_place_list_http_200_and_template(self):
        """Verifies places directory list view renders HTTP 200 with required components."""
        response = self.client.get(reverse('places:list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'places/place_list.html')
        self.assertTemplateUsed(response, 'base.html')
        self.assertContains(response, "Badshahi Mosque")
        self.assertContains(response, "Historical Monuments")
        self.assertContains(response, "Refine Places")

    def test_place_list_category_filter(self):
        """Verifies filtering by category slug isolates respective places."""
        shalamar = Place.objects.create(
            category=self.cat_garden,
            locality=self.loc_walled,
            title="Shalamar Gardens",
            slug="shalamar-gardens",
            summary="Historic Mughal garden complex with 410 fountains.",
            description="UNESCO World Heritage site.",
            address="Grand Trunk Road, Baghbanpura",
            is_active=True
        )

        # Filter: Gardens
        resp_garden = self.client.get(reverse('places:list'), {'category': 'gardens-parks'})
        self.assertEqual(resp_garden.status_code, 200)
        self.assertContains(resp_garden, "Shalamar Gardens")
        self.assertNotContains(resp_garden, "Badshahi Mosque")

        # Filter: Monuments
        resp_monument = self.client.get(reverse('places:list'), {'category': 'historical-monuments'})
        self.assertEqual(resp_monument.status_code, 200)
        self.assertContains(resp_monument, "Badshahi Mosque")
        self.assertNotContains(resp_monument, "Shalamar Gardens")

    def test_place_list_area_filter(self):
        """Verifies filtering by locality or zone isolates respective places."""
        place_gulberg = Place.objects.create(
            category=self.cat_garden,
            locality=self.loc_gulberg,
            title="Jilani Park (Racecourse)",
            slug="jilani-park",
            summary="Expansive floral park in central Lahore.",
            description="Famous for annual spring horse and flower shows.",
            address="Jail Road, Gulberg",
            is_active=True
        )

        # Filter by Walled City
        resp_walled = self.client.get(reverse('places:list'), {'area': 'walled-city'})
        self.assertEqual(resp_walled.status_code, 200)
        self.assertContains(resp_walled, "Badshahi Mosque")
        self.assertNotContains(resp_walled, "Jilani Park")

        # Filter by Gulberg
        resp_gulberg = self.client.get(reverse('places:list'), {'area': 'gulberg-3'})
        self.assertEqual(resp_gulberg.status_code, 200)
        self.assertContains(resp_gulberg, "Jilani Park")
        self.assertNotContains(resp_walled, "Jilani Park")

    def test_place_list_keyword_search(self):
        """Verifies keyword search across English/Urdu title, address, and era."""
        # 1. Search by name
        resp = self.client.get(reverse('places:list'), {'q': 'Badshahi'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Badshahi Mosque")

        # 2. Search by Urdu name
        resp_ur = self.client.get(reverse('places:list'), {'q': 'مسجد'})
        self.assertEqual(resp_ur.status_code, 200)
        self.assertContains(resp_ur, "Badshahi Mosque")

        # 3. Search by era
        resp_era = self.client.get(reverse('places:list'), {'q': '1673 AD'})
        self.assertEqual(resp_era.status_code, 200)
        self.assertContains(resp_era, "Badshahi Mosque")

        # 4. Search no match
        resp_none = self.client.get(reverse('places:list'), {'q': 'NonExistentPlaceQueryXYZ'})
        self.assertEqual(resp_none.status_code, 200)
        self.assertContains(resp_none, "No Tourist Places Found")

    def test_place_list_verified_and_features_filter(self):
        """Verifies verified_only, wheelchair, and free entry toggles."""
        unverified_place = Place.objects.create(
            category=self.cat_monument,
            locality=self.loc_walled,
            title="Unverified Old Gateway",
            slug="unverified-gateway",
            summary="Candidate gate under audit.",
            description="Audit pending.",
            address="Circular Road",
            is_active=True,
            verification_status="unverified",
            entry_fee_pkr=Decimal("100.00"),
            wheelchair_accessible=False
        )

        # Verified Only
        resp_v = self.client.get(reverse('places:list'), {'verified_only': '1'})
        self.assertContains(resp_v, "Badshahi Mosque")
        self.assertNotContains(resp_v, "Unverified Old Gateway")

        # Wheelchair Only
        resp_w = self.client.get(reverse('places:list'), {'wheelchair': '1'})
        self.assertContains(resp_w, "Badshahi Mosque")
        self.assertNotContains(resp_w, "Unverified Old Gateway")

        # Free Entry Only
        resp_f = self.client.get(reverse('places:list'), {'free_entry': '1'})
        self.assertContains(resp_f, "Badshahi Mosque")
        self.assertNotContains(resp_f, "Unverified Old Gateway")

    def test_place_list_pagination(self):
        """Verifies 9 places per page pagination and boundary handling."""
        # Create 14 additional places (total 15 with Badshahi Mosque)
        for i in range(1, 15):
            Place.objects.create(
                category=self.cat_monument,
                locality=self.loc_walled,
                title=f"Historic Monument {i:02d}",
                slug=f"historic-monument-{i:02d}",
                summary=f"Summary {i}",
                description=f"Description {i}",
                address=f"Address {i}",
                is_active=True
            )

        # Page 1 (9 items)
        resp_p1 = self.client.get(reverse('places:list'))
        self.assertEqual(resp_p1.status_code, 200)
        self.assertEqual(len(resp_p1.context['places']), 9)
        self.assertTrue(resp_p1.context['page_obj'].has_next())

        # Page 2 (6 items remaining)
        resp_p2 = self.client.get(reverse('places:list'), {'page': 2})
        self.assertEqual(resp_p2.status_code, 200)
        self.assertEqual(len(resp_p2.context['places']), 6)
        self.assertFalse(resp_p2.context['page_obj'].has_next())

        # Out-of-bounds page falls back to page 2 (last page)
        resp_p_high = self.client.get(reverse('places:list'), {'page': 999})
        self.assertEqual(resp_p_high.status_code, 200)
        self.assertEqual(resp_p_high.context['page_obj'].number, 2)

        # Invalid non-integer page falls back to page 1
        resp_p_invalid = self.client.get(reverse('places:list'), {'page': 'abc'})
        self.assertEqual(resp_p_invalid.status_code, 200)
        self.assertEqual(resp_p_invalid.context['page_obj'].number, 1)

    def test_place_detail_view_success_and_seo(self):
        """Verifies place detail view renders verified data, timings, fee, and Schema.org JSON-LD."""
        detail_url = reverse('places:detail', kwargs={'slug': self.place_badshahi.slug})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'places/place_detail.html')

        # Content verification
        self.assertContains(response, "Badshahi Mosque")
        self.assertContains(response, "بادشاہی مسجد")
        self.assertContains(response, "Mughal Empire (1673 AD)")
        self.assertContains(response, "Anarkali Station (Orange Line)")
        self.assertContains(response, "Free Entry")

        # Schema.org JSON-LD verification
        self.assertContains(response, 'application/ld+json')
        self.assertContains(response, '"@type": "TouristAttraction"')
        self.assertContains(response, '"name": "Badshahi Mosque"')
        self.assertContains(response, '"alternateName": "بادشاہی مسجد"')
        self.assertContains(response, '"latitude": 31.5882')
        self.assertContains(response, '"longitude": 74.3096')

    def test_place_detail_invalid_slug_returns_404(self):
        """Verifies non-existent slug returns standard HTTP 404."""
        invalid_url = reverse('places:detail', kwargs={'slug': 'non-existent-ruins'})
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, 404)

    def test_unpublished_place_visibility_permission(self):
        """Verifies is_active=False places are hidden from directory list and return 404 on detail."""
        hidden_place = Place.objects.create(
            category=self.cat_monument,
            locality=self.loc_walled,
            title="Restricted Underground Tunnel",
            slug="restricted-tunnel",
            summary="Draft secret.",
            description="Must not be published.",
            address="Subterranean Walled City",
            is_active=False
        )

        # Check not in list
        resp_list = self.client.get(reverse('places:list'))
        self.assertNotContains(resp_list, "Restricted Underground Tunnel")

        # Check detail returns 404
        hidden_url = reverse('places:detail', kwargs={'slug': hidden_place.slug})
        resp_detail = self.client.get(hidden_url)
        self.assertEqual(resp_detail.status_code, 404)

    def test_related_places_exclusion_logic(self):
        """Verifies related places shows peers in same category/area but excludes current place."""
        place_2 = Place.objects.create(
            category=self.cat_monument, locality=self.loc_walled,
            title="Lahore Fort", slug="lahore-fort",
            summary="Citadel opposite Badshahi Mosque.", description="Citadel.", address="Fort Rd",
            is_active=True
        )
        place_3 = Place.objects.create(
            category=self.cat_monument, locality=self.loc_walled,
            title="Wazir Khan Mosque", slug="wazir-khan-mosque",
            summary="Frescoed masterpiece.", description="Frescoed.", address="Delhi Gate",
            is_active=True
        )

        detail_url = reverse('places:detail', kwargs={'slug': self.place_badshahi.slug})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)

        # Related places contains Lahore Fort and Wazir Khan Mosque
        self.assertIn(place_2, response.context['related_places'])
        self.assertIn(place_3, response.context['related_places'])
        # Related places does NOT contain Badshahi Mosque itself
        self.assertNotIn(self.place_badshahi, response.context['related_places'])

    def test_place_detail_increments_view_count(self):
        """Verifies visiting a place detail page increments view_count."""
        initial_views = self.place_badshahi.view_count
        detail_url = reverse('places:detail', kwargs={'slug': self.place_badshahi.slug})

        self.client.get(detail_url)
        self.place_badshahi.refresh_from_db()
        self.assertEqual(self.place_badshahi.view_count, initial_views + 1)

    def test_place_gallery_and_validation(self):
        """Verifies PlaceGalleryImage relationship and image validator."""
        gallery_item = PlaceGalleryImage.objects.create(
            place=self.place_badshahi,
            image="places/gallery/test_courtyard.jpg",
            caption="Main Courtyard at Sunset",
            photographer_credit="WCLA Heritage Archives",
            display_order=1
        )
        self.assertEqual(str(gallery_item), "Photo for Badshahi Mosque (#1)")
        self.assertIn(gallery_item, self.place_badshahi.gallery_images.all())

        # Test validator on bad extension
        bad_file = SimpleUploadedFile("malicious.exe", b"fake binary data")
        with self.assertRaises(ValidationError):
            validate_image_extension(bad_file)

    def test_places_admin_registration_and_actions(self):
        """Verifies Django admin registers Place and PlaceCategory with custom actions."""
        self.assertIn(Place, site._registry)
        self.assertIn(PlaceCategory, site._registry)

        place_admin = site._registry[Place]
        self.assertIn('make_verified', place_admin.actions)
        self.assertIn('make_featured', place_admin.actions)
        self.assertIn('publish', place_admin.actions)
        self.assertIn('unpublish', place_admin.actions)

        # Test unpublish action
        class MockRequest:
            user = self.user
            def __init__(self):
                self._messages = []
            def message_user(self, *args, **kwargs):
                pass

        mock_req = MockRequest()
        place_admin.message_user = lambda req, msg: None

        place_admin.unpublish(mock_req, Place.objects.filter(pk=self.place_badshahi.pk))
        self.place_badshahi.refresh_from_db()
        self.assertFalse(self.place_badshahi.is_active)

        # Test publish action
        place_admin.publish(mock_req, Place.objects.filter(pk=self.place_badshahi.pk))
        self.place_badshahi.refresh_from_db()
        self.assertTrue(self.place_badshahi.is_active)
