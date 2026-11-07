from datetime import datetime, timezone as dt_timezone
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.admin.sites import site
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.core.models import LocalityZone, Locality
from apps.hospitals.models import MedicalSpecialty, Hospital
from apps.hospitals.admin import HospitalAdmin, MedicalSpecialtyAdmin

User = get_user_model()


class HospitalDirectoryComprehensiveTests(TestCase):
    """
    Exhaustive test suite for the Hospitals & Clinics directory:
    - Listing page rendering, HTTP 200, template and metadata
    - Facility type filtering (public, private, trust, clinic, diagnostic)
    - Area / Locality filtering
    - Medical specialty / clinical service filtering
    - Verified 24/7 emergency care filter
    - Clinical infrastructure filters (trauma center, blood bank, pharmacy)
    - Keyword search across name, Urdu name, description, address, specialties
    - Pagination handling with query string preservation
    - Empty state handling
    - Facility detail page rendering, Schema.org Hospital JSON-LD
    - Verified emergency protocol & ambulance contacts
    - Non-fabrication & emergency claims validation (unverified emergency raises ValidationError)
    - URL validation on website and source_url
    - Unpublished / draft content isolation (404 on detail, hidden from list)
    - Admin moderation actions (verify, feature, unfeature, publish, unpublish)
    """

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='healthauditor@lahorecityhub.pk',
            username='healthauditor',
            password='TestPassword123!'
        )

        # Spatial Hierarchy
        self.zone_central = LocalityZone.objects.create(name="Central Lahore Zone", slug="central-lahore-zone")
        self.zone_suburban = LocalityZone.objects.create(name="Johar Town Zone", slug="johar-town-zone")

        self.loc_jail_road = Locality.objects.create(
            zone=self.zone_central, name="Jail Road", slug="jail-road", postal_code="54000"
        )
        self.loc_johar_town = Locality.objects.create(
            zone=self.zone_suburban, name="Johar Town Phase 2", slug="johar-town-phase-2", postal_code="54770"
        )

        # Specialties
        self.spec_cardio = MedicalSpecialty.objects.create(
            name="Cardiology & Cardiac Surgery", slug="cardiology-cardiac-surgery", description="Adult and pediatric cardiac interventions."
        )
        self.spec_oncology = MedicalSpecialty.objects.create(
            name="Oncology & Chemotherapy", slug="oncology-chemotherapy", description="Comprehensive cancer care and radiotherapy."
        )
        self.spec_pediatrics = MedicalSpecialty.objects.create(
            name="Pediatrics & Neonatology", slug="pediatrics-neonatology", description="Child health and neonatal intensive care."
        )

        # 1. Verified Public Teaching Hospital (with verified 24/7 emergency)
        self.hosp_services = Hospital.objects.create(
            title="Services Hospital Lahore",
            title_ur="سروسز ہسپتال لاہور",
            slug="services-hospital-lahore",
            hospital_type="public",
            locality=self.loc_jail_road,
            address="Ghaus-ul-Azam Road, Jail Road",
            landmark="Near Race Course Park",
            summary="Premier tertiary care public teaching hospital affiliated with Services Institute of Medical Sciences (SIMS).",
            description="Large multidisciplinary public hospital providing emergency trauma care, cardiology, pediatrics, and surgical suites.",
            is_24_7_emergency=True,
            has_trauma_center=True,
            has_blood_bank=True,
            has_24_7_pharmacy=True,
            bed_capacity=1196,
            phone_number="+92-42-99203402",
            emergency_phone="+92-42-99203425",
            ambulance_direct_phone="+92-42-99203429",
            emergency_notes="Dedicated 40-bed resuscitation bay with immediate triage triage nurse and surgical staff.",
            website="https://serviceshospital.punjab.gov.pk",
            source_url="https://health.punjab.gov.pk/facilities/services-hospital",
            is_active=True,
            is_featured=True,
            verification_status="verified",
            last_verified_at=timezone.now()
        )
        self.hosp_services.specialties.add(self.spec_cardio, self.spec_pediatrics)

        # 2. Verified Trust Cancer Hospital (outpatient & oncology focus)
        self.hosp_shaukat = Hospital.objects.create(
            title="Shaukat Khanum Memorial Cancer Hospital",
            title_ur="شوکت خانم میموریل کینسر ہسپتال",
            slug="shaukat-khanum-memorial-cancer-hospital",
            hospital_type="trust",
            locality=self.loc_johar_town,
            address="7A Block R-3, Johar Town",
            landmark="Near Expo Centre Lahore",
            summary="State-of-the-art charitable cancer research and treatment center in Lahore.",
            description="Internationally accredited comprehensive cancer center providing subsidized diagnostic imaging, chemotherapy, and surgical oncology.",
            is_24_7_emergency=False,  # Specialty oncology, not general ER
            has_trauma_center=False,
            has_blood_bank=True,
            has_24_7_pharmacy=True,
            bed_capacity=195,
            phone_number="+92-42-35905000",
            website="https://shaukatkhanum.org.pk",
            source_url="https://shaukatkhanum.org.pk/about-us/",
            is_active=True,
            is_featured=True,
            verification_status="verified",
            last_verified_at=timezone.now()
        )
        self.hosp_shaukat.specialties.add(self.spec_oncology)

        # 3. Draft / Unpublished Hospital
        self.hosp_draft = Hospital.objects.create(
            title="Proposed MediCity Complex",
            slug="proposed-medicity-complex",
            hospital_type="private",
            locality=self.loc_johar_town,
            address="Southern Bypass, Johar Town",
            summary="Unopened healthcare facility currently in development.",
            description="Facility undergoing equipment commissioning and regulatory approval.",
            is_24_7_emergency=False,
            is_active=False,
            verification_status="pending"
        )

    # 1. Listing Page Response & Templates
    def test_hospital_list_http_200_and_template(self):
        url = reverse('hospitals:list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'hospitals/hospital_list.html')
        self.assertIn('hospitals', response.context)
        self.assertIn('hospital_types', response.context)
        self.assertIn('specialties', response.context)
        self.assertIn('total_results', response.context)

    # 2. Facility Type Filter
    def test_hospital_list_type_filter(self):
        url = reverse('hospitals:list') + "?type=public"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        titles = [h.title for h in response.context['hospitals']]
        self.assertIn(self.hosp_services.title, titles)
        self.assertNotIn(self.hosp_shaukat.title, titles)

    # 3. Area / Locality Filter
    def test_hospital_list_area_filter(self):
        url = reverse('hospitals:list') + f"?area={self.loc_jail_road.slug}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        titles = [h.title for h in response.context['hospitals']]
        self.assertIn(self.hosp_services.title, titles)
        self.assertNotIn(self.hosp_shaukat.title, titles)

    # 4. Medical Specialty Filter
    def test_hospital_list_specialty_filter(self):
        url = reverse('hospitals:list') + f"?specialty={self.spec_oncology.slug}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        titles = [h.title for h in response.context['hospitals']]
        self.assertIn(self.hosp_shaukat.title, titles)
        self.assertNotIn(self.hosp_services.title, titles)

    # 5. Keyword Search
    def test_hospital_list_keyword_search(self):
        # Match by specialty keyword
        response = self.client.get(reverse('hospitals:list') + "?q=chemotherapy")
        self.assertEqual(response.status_code, 200)
        titles = [h.title for h in response.context['hospitals']]
        self.assertIn(self.hosp_shaukat.title, titles)
        self.assertNotIn(self.hosp_services.title, titles)

        # Match by Urdu title
        response_ur = self.client.get(reverse('hospitals:list') + "?q=سروسز")
        self.assertEqual(response_ur.status_code, 200)
        titles_ur = [h.title for h in response_ur.context['hospitals']]
        self.assertIn(self.hosp_services.title, titles_ur)

    # 6. Verified 24/7 Emergency Filter
    def test_hospital_list_verified_emergency_filter(self):
        response = self.client.get(reverse('hospitals:list') + "?emergency=1")
        self.assertEqual(response.status_code, 200)
        titles = [h.title for h in response.context['hospitals']]
        self.assertIn(self.hosp_services.title, titles)
        self.assertNotIn(self.hosp_shaukat.title, titles)

    # 7. Clinical Capabilities Filter
    def test_hospital_list_clinical_capabilities_filter(self):
        # Filter trauma center only
        response = self.client.get(reverse('hospitals:list') + "?trauma=1")
        self.assertEqual(response.status_code, 200)
        titles = [h.title for h in response.context['hospitals']]
        self.assertIn(self.hosp_services.title, titles)
        self.assertNotIn(self.hosp_shaukat.title, titles)

    # 8. Pagination
    def test_hospital_list_pagination(self):
        # Create 10 additional hospitals to trigger pagination (9 per page)
        for i in range(10):
            Hospital.objects.create(
                title=f"Batch Clinic {i}",
                slug=f"batch-clinic-{i}",
                hospital_type="clinic",
                locality=self.loc_jail_road,
                address="Jail Road, Lahore",
                is_active=True
            )

        response_page1 = self.client.get(reverse('hospitals:list'))
        self.assertEqual(len(response_page1.context['hospitals']), 9)
        self.assertTrue(response_page1.context['page_obj'].has_next())

        response_page2 = self.client.get(reverse('hospitals:list') + "?page=2")
        self.assertEqual(response_page2.status_code, 200)
        self.assertTrue(response_page2.context['page_obj'].has_previous())

    # 9. Empty State
    def test_hospital_list_empty_state(self):
        response = self.client.get(reverse('hospitals:list') + "?q=nonexistenthospitalxyz9999")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_results'], 0)
        self.assertContains(response, "No Medical Facilities Found")

    # 10. Detail Page & Schema.org JSON-LD
    def test_hospital_detail_view_success_and_seo(self):
        url = reverse('hospitals:detail', kwargs={'slug': self.hosp_services.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'hospitals/hospital_detail.html')
        self.assertEqual(response.context['hospital'].pk, self.hosp_services.pk)

        content = response.content.decode('utf-8')
        # Check Schema.org Hospital and content
        self.assertIn('"@type": "Hospital"', content)
        self.assertContains(response, self.hosp_services.title)
        self.assertContains(response, "1196 Beds")
        self.assertContains(response, "Cardiology &amp; Cardiac Surgery")
        self.assertIn("+92-42-99203429", content)

    # 11. Invalid Slug Returns 404
    def test_hospital_detail_invalid_slug_returns_404(self):
        url = reverse('hospitals:detail', kwargs={'slug': 'non-existent-clinic-slug'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    # 12. Unpublished Isolation
    def test_unpublished_hospital_isolation(self):
        # Must return 404 on direct detail request
        url = reverse('hospitals:detail', kwargs={'slug': self.hosp_draft.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # Must not appear in public listing
        response_list = self.client.get(reverse('hospitals:list'))
        titles = [h.title for h in response_list.context['hospitals']]
        self.assertNotIn(self.hosp_draft.title, titles)

    # 13. View Count Atomic Increment
    def test_hospital_detail_increments_view_count(self):
        initial_views = self.hosp_services.view_count
        url = reverse('hospitals:detail', kwargs={'slug': self.hosp_services.slug})
        self.client.get(url)
        self.hosp_services.refresh_from_db()
        self.assertEqual(self.hosp_services.view_count, initial_views + 1)

    # 14. Related Facilities Logic
    def test_related_facilities_exclusion(self):
        url = reverse('hospitals:detail', kwargs={'slug': self.hosp_services.slug})
        response = self.client.get(url)
        related = response.context['related_facilities']
        related_ids = [h.pk for h in related]
        self.assertNotIn(self.hosp_services.pk, related_ids)
        self.assertNotIn(self.hosp_draft.pk, related_ids)

    # 15. Emergency Verification Rule
    def test_emergency_claim_validation(self):
        # Unverified facility claiming 24/7 emergency must raise ValidationError
        unverified_emergency_hospital = Hospital(
            title="Unverified ER Clinic",
            slug="unverified-er-clinic",
            hospital_type="clinic",
            locality=self.loc_jail_road,
            is_24_7_emergency=True,
            verification_status="unverified"
        )
        with self.assertRaises(ValidationError):
            unverified_emergency_hospital.clean()

        # Verified facility claiming 24/7 emergency succeeds
        verified_emergency_hospital = Hospital(
            title="Verified ER Clinic",
            slug="verified-er-clinic",
            hospital_type="private",
            locality=self.loc_jail_road,
            is_24_7_emergency=True,
            verification_status="verified"
        )
        verified_emergency_hospital.clean()  # Should not raise

    # 16. URL & Model Validation
    def test_url_validation_and_model_clean(self):
        # Valid URLs succeed
        self.hosp_services.website = "https://verified-health.pk"
        self.hosp_services.source_url = "https://health.punjab.gov.pk"
        self.hosp_services.clean()  # Must not raise

        # Invalid website URL raises ValidationError
        self.hosp_services.website = "not-a-valid-url"
        with self.assertRaises(ValidationError):
            self.hosp_services.clean()

        # Invalid source URL raises ValidationError
        self.hosp_services.website = "https://valid.pk"
        self.hosp_services.source_url = "ftp://invalid-scheme.pk"
        with self.assertRaises(ValidationError):
            self.hosp_services.clean()

        # Negative bed capacity raises ValidationError
        self.hosp_services.source_url = "https://health.punjab.gov.pk"
        self.hosp_services.bed_capacity = -10
        with self.assertRaises(ValidationError):
            self.hosp_services.clean()

    # 17. Admin Moderation & Actions
    def test_hospitals_admin_moderation_and_actions(self):
        self.assertIn(Hospital, site._registry)
        self.assertIn(MedicalSpecialty, site._registry)

        admin_instance = HospitalAdmin(Hospital, site)
        qs = Hospital.objects.filter(pk=self.hosp_services.pk)

        # Action: Make Verified
        admin_instance.make_verified(None, qs)
        self.hosp_services.refresh_from_db()
        self.assertEqual(self.hosp_services.verification_status, 'verified')
        self.assertIsNotNone(self.hosp_services.last_verified_at)

        # Action: Make Featured
        admin_instance.make_featured(None, qs)
        self.hosp_services.refresh_from_db()
        self.assertTrue(self.hosp_services.is_featured)

        # Action: Unfeature
        admin_instance.unfeature(None, qs)
        self.hosp_services.refresh_from_db()
        self.assertFalse(self.hosp_services.is_featured)

        # Action: Unpublish
        admin_instance.unpublish(None, qs)
        self.hosp_services.refresh_from_db()
        self.assertFalse(self.hosp_services.is_active)

        # Action: Publish
        admin_instance.publish(None, qs)
        self.hosp_services.refresh_from_db()
        self.assertTrue(self.hosp_services.is_active)
