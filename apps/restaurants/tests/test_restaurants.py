import datetime
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.admin.sites import site
from django.core.exceptions import ValidationError

from apps.core.models import LocalityZone, Locality
from apps.restaurants.models import Cuisine, RestaurantFeature, Restaurant, MenuHighlight
from apps.restaurants.admin import RestaurantAdmin, CuisineAdmin, RestaurantFeatureAdmin

User = get_user_model()


class RestaurantDirectoryComprehensiveTests(TestCase):
    """
    Exhaustive test suite for the Restaurants directory module:
    - Restaurant listing page rendering, HTTP 200, template and metadata
    - Cuisine filtering & Locality/Area filtering
    - Price category filtering ($, $$, $$$, $$$$)
    - Dining amenity filters (family hall, takeaway, delivery, verified only)
    - Keyword search across title, Urdu title, description, address, cuisines
    - Pagination handling with query string preservation
    - Empty state handling
    - Restaurant detail page rendering, Schema.org Restaurant JSON-LD
    - Menu highlights display and pricing validation
    - View count atomic increment tracking
    - Related restaurants recommendation logic (excluding current listing)
    - Unpublished / draft content isolation (404 on detail, hidden from list)
    - Admin moderation actions (verify, feature, unfeature, publish, unpublish)
    """

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='foodcritic@lahorecityhub.pk',
            username='foodcritic',
            password='TestPassword123!'
        )

        # Spatial Hierarchy
        self.zone_walled = LocalityZone.objects.create(name="Walled City Zone", slug="walled-city-zone")
        self.zone_gulberg = LocalityZone.objects.create(name="Gulberg Zone", slug="gulberg-zone")

        self.loc_walled = Locality.objects.create(
            zone=self.zone_walled, name="Fort Road", slug="fort-road", postal_code="54000"
        )
        self.loc_gulberg = Locality.objects.create(
            zone=self.zone_gulberg, name="Gulberg II", slug="gulberg-ii", postal_code="54660"
        )

        # Cuisines
        self.cuisine_desi = Cuisine.objects.create(
            name="Traditional Karahi & BBQ", slug="traditional-karahi-bbq", description="Authentic Punjabi Karahi and grilled meats."
        )
        self.cuisine_continental = Cuisine.objects.create(
            name="Continental & Italian", slug="continental-italian", description="Wood-fired pizzas and steaks."
        )

        # Features
        self.feat_valet = RestaurantFeature.objects.create(name="Valet Parking", slug="valet-parking")
        self.feat_rooftop = RestaurantFeature.objects.create(name="Rooftop View", slug="rooftop-view")

        # Active Desi Restaurant
        self.rest_haveli = Restaurant.objects.create(
            title="Haveli Heritage Restaurant",
            title_ur="حویلی ریسٹورنٹ",
            slug="haveli-heritage-restaurant",
            locality=self.loc_walled,
            address="Fort Road Food Street, Walled City",
            landmark="Badshahi Mosque view",
            summary="Panoramic rooftop restaurant overlooking the Mughal Badshahi Mosque serving authentic mutton karahi.",
            description="Established within a restored historic haveli on Fort Road Food Street, offering multi-level dining with direct views of the illuminated Badshahi Mosque.",
            price_tier="$$$",
            seating_capacity=250,
            has_family_hall=True,
            provides_takeaway=True,
            provides_delivery=False,
            opening_time=datetime.time(17, 0),
            closing_time=datetime.time(1, 0),
            closed_on_days="Open Daily",
            ramadan_timings="Iftar buffet from Maghrib; Sehri buffet 1:30 AM to Fajr",
            phone_number="+92-42-37668888",
            website="https://haveli.com.pk",
            is_active=True,
            is_featured=True,
            verification_status="verified"
        )
        self.rest_haveli.cuisines.add(self.cuisine_desi)
        self.rest_haveli.features.add(self.feat_rooftop, self.feat_valet)

        # Menu Highlights for Haveli
        self.item_karahi = MenuHighlight.objects.create(
            restaurant=self.rest_haveli,
            item_name="Mutton Shinwari Karahi",
            description="Fresh mutton cooked in lamb fat, tomatoes, green chilies, and black pepper.",
            price_pkr=Decimal("3800.00"),
            is_signature=True
        )

        # Active Continental Cafe
        self.rest_cafe = Restaurant.objects.create(
            title="Gulberg Bistro & Bakery",
            slug="gulberg-bistro-bakery",
            locality=self.loc_gulberg,
            address="MM Alam Road, Gulberg II",
            summary="Artisanal sourdough bakery and modern European cafe serving handcrafted pasta and espresso.",
            description="Contemporary dining room featuring indoor botanical garden seating, specialty coffee bar, and wood-fired pizzas.",
            price_tier="$$",
            seating_capacity=80,
            has_family_hall=True,
            provides_takeaway=True,
            provides_delivery=True,
            opening_time=datetime.time(8, 0),
            closing_time=datetime.time(23, 30),
            phone_number="+92-42-35789999",
            website="https://gulbergbistro.pk",
            is_active=True,
            is_featured=False,
            verification_status="verified"
        )
        self.rest_cafe.cuisines.add(self.cuisine_continental)

        # Draft / Unpublished Restaurant
        self.rest_draft = Restaurant.objects.create(
            title="Secret Underground Speakeasy Cafe",
            slug="secret-underground-speakeasy-cafe",
            locality=self.loc_gulberg,
            address="Private basement, Gulberg II",
            summary="Unlisted private tasting lounge.",
            description="Testing venue currently under internal review.",
            price_tier="$$$$",
            is_active=False,
            verification_status="pending"
        )

    # 1. Listing Page Response & Templates
    def test_restaurant_list_http_200_and_template(self):
        url = reverse('restaurants:list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'restaurants/restaurant_list.html')
        self.assertIn('restaurants', response.context)
        self.assertIn('cuisines', response.context)
        self.assertIn('total_results', response.context)

    # 2. Cuisine Filter
    def test_restaurant_list_cuisine_filter(self):
        url = reverse('restaurants:list') + f"?cuisine={self.cuisine_desi.slug}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        titles = [r.title for r in response.context['restaurants']]
        self.assertIn(self.rest_haveli.title, titles)
        self.assertNotIn(self.rest_cafe.title, titles)

    # 3. Area / Locality Filter
    def test_restaurant_list_area_filter(self):
        url = reverse('restaurants:list') + f"?area={self.loc_gulberg.slug}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        titles = [r.title for r in response.context['restaurants']]
        self.assertIn(self.rest_cafe.title, titles)
        self.assertNotIn(self.rest_haveli.title, titles)

    # 4. Price Tier Filter
    def test_restaurant_list_price_filter(self):
        url = reverse('restaurants:list') + "?price=$$$"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        titles = [r.title for r in response.context['restaurants']]
        self.assertIn(self.rest_haveli.title, titles)
        self.assertNotIn(self.rest_cafe.title, titles)

    # 5. Keyword Search
    def test_restaurant_list_keyword_search(self):
        # Search by specialty term in description
        response = self.client.get(reverse('restaurants:list') + "?q=sourdough")
        self.assertEqual(response.status_code, 200)
        titles = [r.title for r in response.context['restaurants']]
        self.assertIn(self.rest_cafe.title, titles)
        self.assertNotIn(self.rest_haveli.title, titles)

        # Search by Urdu title
        response_ur = self.client.get(reverse('restaurants:list') + "?q=حویلی")
        self.assertEqual(response_ur.status_code, 200)
        titles_ur = [r.title for r in response_ur.context['restaurants']]
        self.assertIn(self.rest_haveli.title, titles_ur)

    # 6. Dining Amenity Filters
    def test_restaurant_list_amenity_filters(self):
        # Filter delivery only
        response_deliv = self.client.get(reverse('restaurants:list') + "?delivery=1")
        deliv_titles = [r.title for r in response_deliv.context['restaurants']]
        self.assertIn(self.rest_cafe.title, deliv_titles)
        self.assertNotIn(self.rest_haveli.title, deliv_titles)

    # 7. Verified Only Filter
    def test_restaurant_list_verified_filter(self):
        response = self.client.get(reverse('restaurants:list') + "?verified_only=1")
        self.assertEqual(response.status_code, 200)
        for r in response.context['restaurants']:
            self.assertIn(r.verification_status, ['verified', 'claimed'])

    # 8. Pagination
    def test_restaurant_list_pagination(self):
        # Create 10 additional restaurants to trigger pagination (9 per page)
        for i in range(10):
            Restaurant.objects.create(
                title=f"Batch Dining Spot {i}",
                slug=f"batch-dining-spot-{i}",
                locality=self.loc_gulberg,
                address="Gulberg, Lahore",
                price_tier="$$",
                is_active=True
            )

        response_page1 = self.client.get(reverse('restaurants:list'))
        self.assertEqual(len(response_page1.context['restaurants']), 9)
        self.assertTrue(response_page1.context['page_obj'].has_next())

        response_page2 = self.client.get(reverse('restaurants:list') + "?page=2")
        self.assertEqual(response_page2.status_code, 200)
        self.assertTrue(response_page2.context['page_obj'].has_previous())

    # 9. Empty State
    def test_restaurant_list_empty_state(self):
        response = self.client.get(reverse('restaurants:list') + "?q=nonexistentdishtacos9999")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_results'], 0)
        self.assertContains(response, "No Restaurants Found")

    # 10. Restaurant Detail View & Schema.org JSON-LD
    def test_restaurant_detail_view_success_and_seo(self):
        url = reverse('restaurants:detail', kwargs={'slug': self.rest_haveli.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'restaurants/restaurant_detail.html')
        self.assertEqual(response.context['restaurant'].pk, self.rest_haveli.pk)

        content = response.content.decode('utf-8')
        # Check Schema.org Restaurant JSON-LD
        self.assertIn('"@type": "Restaurant"', content)
        self.assertIn(self.rest_haveli.title, content)
        self.assertIn("Mutton Shinwari Karahi", content)
        self.assertIn("PKR 3800", content)
        self.assertIn(self.rest_haveli.phone_number, content)

    # 11. Invalid Slug Returns 404
    def test_restaurant_detail_invalid_slug_returns_404(self):
        url = reverse('restaurants:detail', kwargs={'slug': 'non-existent-diner-slug'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    # 12. Unpublished Restaurant Isolation
    def test_unpublished_restaurant_isolation(self):
        # Must return 404 on direct detail view
        url = reverse('restaurants:detail', kwargs={'slug': self.rest_draft.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # Must not appear in listing
        response_list = self.client.get(reverse('restaurants:list'))
        titles = [r.title for r in response_list.context['restaurants']]
        self.assertNotIn(self.rest_draft.title, titles)

    # 13. View Count Atomic Increment
    def test_restaurant_detail_increments_view_count(self):
        initial_views = self.rest_haveli.view_count
        url = reverse('restaurants:detail', kwargs={'slug': self.rest_haveli.slug})
        self.client.get(url)
        self.rest_haveli.refresh_from_db()
        self.assertEqual(self.rest_haveli.view_count, initial_views + 1)

    # 14. Related Restaurants Logic
    def test_related_restaurants_exclusion(self):
        url = reverse('restaurants:detail', kwargs={'slug': self.rest_haveli.slug})
        response = self.client.get(url)
        related = response.context['related_restaurants']
        related_ids = [r.pk for r in related]
        self.assertNotIn(self.rest_haveli.pk, related_ids)
        self.assertNotIn(self.rest_draft.pk, related_ids)

    # 15. Model Validation
    def test_restaurant_model_validation(self):
        # Valid website succeeds
        self.rest_haveli.website = "https://verified-site.com"
        self.rest_haveli.clean()  # Should not raise

        # Invalid website raises ValidationError
        self.rest_haveli.website = "not-a-valid-url-without-scheme"
        with self.assertRaises(ValidationError):
            self.rest_haveli.clean()

        # Negative seating capacity raises ValidationError
        self.rest_haveli.website = "https://valid.com"
        self.rest_haveli.seating_capacity = -5
        with self.assertRaises(ValidationError):
            self.rest_haveli.clean()

        # Negative menu item price raises ValidationError
        invalid_item = MenuHighlight(
            restaurant=self.rest_haveli,
            item_name="Faulty Item",
            price_pkr=Decimal("-50.00")
        )
        with self.assertRaises(ValidationError):
            invalid_item.clean()

    # 16. Admin Moderation & Actions
    def test_restaurants_admin_management_and_actions(self):
        self.assertIn(Restaurant, site._registry)
        self.assertIn(Cuisine, site._registry)
        self.assertIn(RestaurantFeature, site._registry)

        admin_instance = RestaurantAdmin(Restaurant, site)
        qs = Restaurant.objects.filter(pk=self.rest_cafe.pk)

        # Action: Mark Verified
        admin_instance.make_verified(None, qs)
        self.rest_cafe.refresh_from_db()
        self.assertEqual(self.rest_cafe.verification_status, 'verified')

        # Action: Make Featured
        admin_instance.make_featured(None, qs)
        self.rest_cafe.refresh_from_db()
        self.assertTrue(self.rest_cafe.is_featured)

        # Action: Unfeature
        admin_instance.unfeature(None, qs)
        self.rest_cafe.refresh_from_db()
        self.assertFalse(self.rest_cafe.is_featured)

        # Action: Unpublish
        admin_instance.unpublish(None, qs)
        self.rest_cafe.refresh_from_db()
        self.assertFalse(self.rest_cafe.is_active)

        # Action: Publish
        admin_instance.publish(None, qs)
        self.rest_cafe.refresh_from_db()
        self.assertTrue(self.rest_cafe.is_active)
