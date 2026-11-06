from django.test import TestCase, Client
from django.urls import reverse

class LahoreCityHubFrontendTests(TestCase):
    """
    Automated test suite verifying template inheritance, response codes,
    navigation links, and DOM elements across all 12 Phase 2 pages.
    """

    def setUp(self):
        self.client = Client()

    def test_homepage_renders_all_15_sections(self):
        """Verifies homepage HTTP 200, SEO title, and key sections."""
        response = self.client.get(reverse('core:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your Complete Guide to Lahore")
        self.assertContains(response, "Discover Lahore by Category")
        self.assertContains(response, "Iconic Lahore Landmarks & Heritage Sites")
        self.assertContains(response, "Latest Job Openings in Lahore")
        self.assertContains(response, "Trending Restaurants & Food Streets")
        self.assertContains(response, "Hospitals & 24/7 Emergency Medical Centers")
        self.assertContains(response, "Universities & Degree Colleges in Lahore")
        self.assertContains(response, "Verified Local Businesses & Services")
        self.assertContains(response, "Orange Line Metro Train (OLMT)")
        self.assertContains(response, "Upcoming Events & Festivals in Lahore")
        self.assertContains(response, "Latest City Notices, Smog & Traffic Advisories")
        self.assertContains(response, "Stay Connected with Lahore")
        self.assertContains(response, "Rescue:</strong> 1122")
        self.assertTemplateUsed(response, 'pages/home.html')
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'navbar.html')
        self.assertTemplateUsed(response, 'footer.html')

    def test_about_page_renders_pillars(self):
        """Verifies About page HTTP 200 and verification pledge."""
        response = self.client.get(reverse('core:about'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dedicated to the Heart & Heritage of Lahore")
        self.assertContains(response, "The Verification Pledge")
        self.assertContains(response, "Hyper-Local Taxonomy")

    def test_contact_page_get_and_post(self):
        """Verifies contact page rendering and form submission flash message."""
        response = self.client.get(reverse('core:contact'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Send a Message to Editorial")

        # Test POST
        post_data = {
            'name': 'Bilal Farooq',
            'email': 'bilal@example.pk',
            'subject': 'Directory Listing Correction',
            'message': 'Please update the opening time of Badshahi Mosque.',
        }
        post_response = self.client.post(reverse('core:contact'), data=post_data)
        self.assertEqual(post_response.status_code, 200)
        self.assertContains(post_response, "Thank you, Bilal Farooq!")

    def test_privacy_and_terms_pages(self):
        """Verifies legal pages render correctly."""
        priv_response = self.client.get(reverse('core:privacy'))
        self.assertEqual(priv_response.status_code, 200)
        self.assertContains(priv_response, "Privacy & Data Protection Policy")

        terms_response = self.client.get(reverse('core:terms'))
        self.assertEqual(terms_response.status_code, 200)
        self.assertContains(terms_response, "Terms and Conditions of Use")

    def test_category_list_pages_and_filters(self):
        """Verifies category listing across different taxonomies and filters."""
        # Test default places
        response = self.client.get(reverse('core:directory_index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tourist Places &amp; Historical Heritage in Lahore")
        self.assertContains(response, "Badshahi Mosque")

        # Test restaurants category
        rest_response = self.client.get(reverse('core:category_list', kwargs={'category_slug': 'restaurants'}))
        self.assertEqual(rest_response.status_code, 200)
        self.assertContains(rest_response, "Restaurants &amp; Cafes in Lahore")
        self.assertContains(rest_response, "Haveli Restaurant")

        # Test locality filter
        filtered_response = self.client.get(
            reverse('core:category_list', kwargs={'category_slug': 'places'}),
            {'locality': 'walled-city'}
        )
        self.assertEqual(filtered_response.status_code, 200)
        self.assertContains(filtered_response, "Badshahi Mosque")

    def test_listing_detail_page(self):
        """Verifies listing detail view with Schema.org JSON-LD and reviews."""
        response = self.client.get(reverse('core:listing_detail', kwargs={'slug': 'badshahi-mosque'}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Badshahi Mosque")
        self.assertContains(response, "Walled City (Androon Lahore)")
        self.assertContains(response, "Essential Facts")
        self.assertContains(response, "Verified Visitor Reviews")
        self.assertContains(response, "application/ld+json")
        self.assertContains(response, "TouristAttraction")

    def test_global_search_view(self):
        """Verifies multi-category search and empty state."""
        # Query with matches
        response = self.client.get(reverse('core:search'), {'q': 'hospital'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Results for')
        self.assertContains(response, 'Shaukat Khanum')

        # Query with no matches triggers empty state
        empty_response = self.client.get(reverse('core:search'), {'q': 'nonexistentqueryxyz999'})
        self.assertEqual(empty_response.status_code, 200)
        self.assertContains(empty_response, 'No results found')

    def test_auth_pages_login_register_dashboard(self):
        """Verifies authentication screens and user dashboard."""
        login_res = self.client.get(reverse('core:login'))
        self.assertEqual(login_res.status_code, 200)
        self.assertContains(login_res, "Sign In to Lahore City Hub")

        reg_res = self.client.get(reverse('core:register'))
        self.assertEqual(reg_res.status_code, 200)
        self.assertContains(reg_res, "Join the Lahore Community")

        dash_res = self.client.get(reverse('core:dashboard'))
        self.assertEqual(dash_res.status_code, 200)
        self.assertContains(dash_res, "Ahmad Raza Khan")
        self.assertContains(dash_res, "Saved Places & Bookmarks")

    def test_business_submission_page(self):
        """Verifies business onboarding and claim submission page."""
        response = self.client.get(reverse('core:business_submission'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Submit or Claim a Business Listing")
        self.assertContains(response, "Proof of Ownership & Verification")

    def test_custom_404_page(self):
        """Verifies custom 404 page rendering."""
        response = self.client.get(reverse('core:preview_404'))
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "Lost in the Walled City?", status_code=404)
        self.assertContains(response, "Return to Homepage", status_code=404)
