from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.admin.sites import site
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.core.models import LocalityZone, Locality
from apps.education.models import EducationType, AccreditationBoard, Institution
from apps.education.admin import InstitutionAdmin, EducationTypeAdmin, AccreditationBoardAdmin

User = get_user_model()


class EducationDirectoryComprehensiveTests(TestCase):
    """
    Exhaustive test suite for the Education Directory module:
    - Listing page rendering, HTTP 200, template and metadata
    - Institution type filtering (Schools, Colleges, Universities, Training Institutes)
    - Campus Area / Locality filtering
    - Gender policy filtering (Co-ed, Girls only, Boys only)
    - Accreditation board filtering (HEC, BISE, Cambridge, PEC)
    - Keyword search across name, Urdu title, programs, admission details, address
    - Pagination handling with query string preservation
    - Empty state handling
    - Detail page rendering, Schema.org EducationalOrganization JSON-LD
    - Programs offered and admission criteria verification
    - URL validation on website, admission_url, prospectus_url, source_url
    - Established year validation
    - Unpublished / draft content isolation (404 on detail, hidden from list)
    - Admin moderation actions (verify, feature, unfeature, publish, unpublish)
    """

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='eduinspector@lahorecityhub.pk',
            username='eduinspector',
            password='TestPassword123!'
        )

        # Spatial Hierarchy
        self.zone_walled = LocalityZone.objects.create(name="Walled City Zone", slug="walled-city-zone")
        self.zone_canal = LocalityZone.objects.create(name="Canal Road Zone", slug="canal-road-zone")

        self.loc_katchery = Locality.objects.create(
            zone=self.zone_walled, name="Katchery Road", slug="katchery-road", postal_code="54000"
        )
        self.loc_canal = Locality.objects.create(
            zone=self.zone_canal, name="Canal Road Campus", slug="canal-road-campus", postal_code="54600"
        )

        # Education Types: Schools, Colleges, Universities, Training Institutes
        self.type_uni = EducationType.objects.create(
            name="University", slug="university", icon_class="bi-mortarboard"
        )
        self.type_college = EducationType.objects.create(
            name="Intermediate College", slug="college", icon_class="bi-bank"
        )
        self.type_school = EducationType.objects.create(
            name="School", slug="school", icon_class="bi-backpack"
        )
        self.type_institute = EducationType.objects.create(
            name="Technical Training Institute", slug="training-institute", icon_class="bi-laptop"
        )

        # Accreditation Boards
        self.board_hec = AccreditationBoard.objects.create(
            name="Higher Education Commission of Pakistan", abbreviation="HEC", website="https://hec.gov.pk"
        )
        self.board_bise = AccreditationBoard.objects.create(
            name="Board of Intermediate and Secondary Education Lahore", abbreviation="BISE", website="https://biselahore.com"
        )

        # 1. Active University (GCU Lahore)
        self.inst_gcu = Institution.objects.create(
            title="Government College University (GCU) Lahore",
            title_ur="گورنمنٹ کالج یونیورسٹی لاہور",
            slug="gcu-lahore",
            education_type=self.type_uni,
            locality=self.loc_katchery,
            address="Katchery Road, Anarkali, Lahore",
            landmark="Near Old Anarkali and District Courts",
            established_year=1864,
            gender_policy="coed",
            summary="Historic public research university founded in 1864, renowned for literature, natural sciences, and computer sciences.",
            description="One of the oldest educational institutions in South Asia, producing eminent Nobel laureates, poets, and statesmen. Operates undergraduate, graduate, and doctorate programs.",
            programs_offered="BS Computer Science, BS Biotechnology, BS English Literature, MS Clinical Psychology, PhD Physics.",
            admission_info="Open merit and test-based admissions for Fall and Spring semesters. Online applications processed through official university portal.",
            admission_cycles="Fall Admissions (August - September); Spring Admissions (January)",
            admission_url="https://www.gcu.edu.pk/admissions/",
            prospectus_url="https://www.gcu.edu.pk/prospectus.pdf",
            phone_number="+92-42-111000010",
            email="admissions@gcu.edu.pk",
            website="https://www.gcu.edu.pk",
            source_url="https://hec.gov.pk/universities/gcu-lahore",
            is_active=True,
            is_featured=True,
            verification_status="verified",
            last_verified_at=timezone.now()
        )
        self.inst_gcu.accreditations.add(self.board_hec)

        # 2. Active College (Kinnaird College)
        self.inst_kinnaird = Institution.objects.create(
            title="Kinnaird College for Women",
            slug="kinnaird-college-for-women",
            education_type=self.type_college,
            locality=self.loc_canal,
            address="93 Jail Road, Lahore",
            landmark="Opposite Race Course Park",
            established_year=1913,
            gender_policy="girls",
            summary="Historic women's college providing FSc, FA, and undergraduate degrees.",
            description="Established in 1913, Kinnaird is one of the premier women's colleges in Pakistan with high academic standing.",
            programs_offered="FSc Pre-Medical, FSc Pre-Engineering, FA Humanities, BS Media Studies.",
            admission_info="Merit-based admission for female applicants following BISE matriculation results.",
            admission_cycles="Summer Admissions (July - August)",
            admission_url="https://www.kinnaird.edu.pk/admissions/",
            phone_number="+92-42-99203781",
            website="https://www.kinnaird.edu.pk",
            is_active=True,
            is_featured=False,
            verification_status="verified",
            last_verified_at=timezone.now()
        )
        self.inst_kinnaird.accreditations.add(self.board_bise)

        # 3. Draft / Unpublished Institute
        self.inst_draft = Institution.objects.create(
            title="Unregistered Academy",
            slug="unregistered-academy",
            education_type=self.type_institute,
            locality=self.loc_katchery,
            address="Underground lane, Anarkali",
            is_active=False,
            verification_status="pending"
        )

    # 1. Listing Page Response & Templates
    def test_education_list_http_200_and_template(self):
        url = reverse('education:list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'education/education_list.html')
        self.assertIn('institutions', response.context)
        self.assertIn('education_types', response.context)
        self.assertIn('total_results', response.context)

    # 2. Type Filter (Universities, Colleges, Schools, Training Institutes)
    def test_education_list_type_filter(self):
        url = reverse('education:list') + f"?type={self.type_uni.slug}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        titles = [i.title for i in response.context['institutions']]
        self.assertIn(self.inst_gcu.title, titles)
        self.assertNotIn(self.inst_kinnaird.title, titles)

    # 3. Area / Locality Filter
    def test_education_list_area_filter(self):
        url = reverse('education:list') + f"?area={self.loc_canal.slug}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        titles = [i.title for i in response.context['institutions']]
        self.assertIn(self.inst_kinnaird.title, titles)
        self.assertNotIn(self.inst_gcu.title, titles)

    # 4. Gender Policy Filter
    def test_education_list_gender_filter(self):
        url = reverse('education:list') + "?gender=girls"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        titles = [i.title for i in response.context['institutions']]
        self.assertIn(self.inst_kinnaird.title, titles)
        self.assertNotIn(self.inst_gcu.title, titles)

    # 5. Accreditation Board Filter
    def test_education_list_board_filter(self):
        url = reverse('education:list') + "?board=HEC"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        titles = [i.title for i in response.context['institutions']]
        self.assertIn(self.inst_gcu.title, titles)
        self.assertNotIn(self.inst_kinnaird.title, titles)

    # 6. Keyword Search
    def test_education_list_keyword_search(self):
        # Match by academic degree
        response = self.client.get(reverse('education:list') + "?q=Biotechnology")
        self.assertEqual(response.status_code, 200)
        titles = [i.title for i in response.context['institutions']]
        self.assertIn(self.inst_gcu.title, titles)
        self.assertNotIn(self.inst_kinnaird.title, titles)

        # Match by Urdu title
        response_ur = self.client.get(reverse('education:list') + "?q=گورنمنٹ")
        self.assertEqual(response_ur.status_code, 200)
        titles_ur = [i.title for i in response_ur.context['institutions']]
        self.assertIn(self.inst_gcu.title, titles_ur)

    # 7. Pagination
    def test_education_list_pagination(self):
        # Create 10 additional institutions to exceed 9 per page
        for i in range(10):
            Institution.objects.create(
                title=f"Batch School {i}",
                slug=f"batch-school-{i}",
                education_type=self.type_school,
                locality=self.loc_canal,
                address="Canal Road, Lahore",
                is_active=True
            )

        response_page1 = self.client.get(reverse('education:list'))
        self.assertEqual(len(response_page1.context['institutions']), 9)
        self.assertTrue(response_page1.context['page_obj'].has_next())

        response_page2 = self.client.get(reverse('education:list') + "?page=2")
        self.assertEqual(response_page2.status_code, 200)
        self.assertTrue(response_page2.context['page_obj'].has_previous())

    # 8. Empty State
    def test_education_list_empty_state(self):
        response = self.client.get(reverse('education:list') + "?q=nonexistentcollege12345")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_results'], 0)
        self.assertContains(response, "No Educational Institutions Found")

    # 9. Detail Page & Schema.org JSON-LD
    def test_education_detail_view_success_and_seo(self):
        url = reverse('education:detail', kwargs={'slug': self.inst_gcu.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'education/education_detail.html')
        self.assertEqual(response.context['institution'].pk, self.inst_gcu.pk)

        content = response.content.decode('utf-8')
        # Check Schema.org EducationalOrganization
        self.assertIn('"@type": "EducationalOrganization"', content)
        self.assertContains(response, self.inst_gcu.title)
        self.assertContains(response, "BS Computer Science")
        self.assertContains(response, "Estd. 1864")
        self.assertIn("+92-42-111000010", content)

    # 10. Invalid Slug Returns 404
    def test_education_detail_invalid_slug_returns_404(self):
        url = reverse('education:detail', kwargs={'slug': 'non-existent-uni-slug'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    # 11. Unpublished Isolation
    def test_unpublished_institution_isolation(self):
        # 404 on direct detail request
        url = reverse('education:detail', kwargs={'slug': self.inst_draft.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # Hidden in public listing
        response_list = self.client.get(reverse('education:list'))
        titles = [i.title for i in response_list.context['institutions']]
        self.assertNotIn(self.inst_draft.title, titles)

    # 12. View Count Increment
    def test_institution_detail_increments_view_count(self):
        initial_views = self.inst_gcu.view_count
        url = reverse('education:detail', kwargs={'slug': self.inst_gcu.slug})
        self.client.get(url)
        self.inst_gcu.refresh_from_db()
        self.assertEqual(self.inst_gcu.view_count, initial_views + 1)

    # 13. Related Institutions Logic
    def test_related_institutions_exclusion(self):
        url = reverse('education:detail', kwargs={'slug': self.inst_gcu.slug})
        response = self.client.get(url)
        related = response.context['related_institutions']
        related_ids = [i.pk for i in related]
        self.assertNotIn(self.inst_gcu.pk, related_ids)
        self.assertNotIn(self.inst_draft.pk, related_ids)

    # 14. URL & Established Year Validation
    def test_url_validation_and_model_clean(self):
        # Valid URLs succeed
        self.inst_gcu.website = "https://www.gcu.edu.pk"
        self.inst_gcu.admission_url = "https://www.gcu.edu.pk/apply"
        self.inst_gcu.prospectus_url = "https://www.gcu.edu.pk/prospectus.pdf"
        self.inst_gcu.source_url = "https://hec.gov.pk"
        self.inst_gcu.clean()  # Must not raise

        # Invalid website raises ValidationError
        self.inst_gcu.website = "not-a-valid-url"
        with self.assertRaises(ValidationError):
            self.inst_gcu.clean()

        # Invalid admission URL raises ValidationError
        self.inst_gcu.website = "https://valid.pk"
        self.inst_gcu.admission_url = "invalid-url-scheme"
        with self.assertRaises(ValidationError):
            self.inst_gcu.clean()

        # Unrealistic established year raises ValidationError
        self.inst_gcu.admission_url = "https://valid.pk/apply"
        self.inst_gcu.established_year = 350
        with self.assertRaises(ValidationError):
            self.inst_gcu.clean()

    # 15. Admin Moderation & Actions
    def test_education_admin_management_and_actions(self):
        self.assertIn(Institution, site._registry)
        self.assertIn(EducationType, site._registry)
        self.assertIn(AccreditationBoard, site._registry)

        admin_instance = InstitutionAdmin(Institution, site)
        qs = Institution.objects.filter(pk=self.inst_kinnaird.pk)

        # Action: Make Verified
        admin_instance.make_verified(None, qs)
        self.inst_kinnaird.refresh_from_db()
        self.assertEqual(self.inst_kinnaird.verification_status, 'verified')
        self.assertIsNotNone(self.inst_kinnaird.last_verified_at)

        # Action: Make Featured
        admin_instance.make_featured(None, qs)
        self.inst_kinnaird.refresh_from_db()
        self.assertTrue(self.inst_kinnaird.is_featured)

        # Action: Unfeature
        admin_instance.unfeature(None, qs)
        self.inst_kinnaird.refresh_from_db()
        self.assertFalse(self.inst_kinnaird.is_featured)

        # Action: Unpublish
        admin_instance.unpublish(None, qs)
        self.inst_kinnaird.refresh_from_db()
        self.assertFalse(self.inst_kinnaird.is_active)

        # Action: Publish
        admin_instance.publish(None, qs)
        self.inst_kinnaird.refresh_from_db()
        self.assertTrue(self.inst_kinnaird.is_active)
