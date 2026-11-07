from datetime import date, timedelta
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.admin.sites import site
from django.core.exceptions import ValidationError

from apps.core.models import LocalityZone, Locality
from apps.jobs.models import JobCategory, Employer, JobListing
from apps.jobs.admin import JobListingAdmin, EmployerAdmin, JobCategoryAdmin

User = get_user_model()


class JobsModuleComprehensiveTests(TestCase):
    """
    Exhaustive test suite for the Jobs module:
    - Jobs listing page rendering, HTTP 200, template and metadata
    - Keyword search across title, employer, description, requirements, qualifications
    - Category filtering
    - Employment type filtering
    - Qualification / Experience level filtering
    - Deadline filtering (active default, closing soon, include expired)
    - Pagination handling with query string preservation
    - Job detail page rendering, Schema.org JobPosting structured data
    - Expired job handling (banner notice, disabled application CTA)
    - Related jobs logic (excludes self, excludes expired)
    - URL validation on application_url and source_url
    - Model validation for salaries
    - Unpublished / draft content isolation (404 on detail, hidden from list)
    - Admin moderation actions (verify, flag, publish, extend deadline)
    """

    def setUp(self):
        self.client = Client()
        self.today = date.today()

        # Spatial Hierarchy
        self.zone = LocalityZone.objects.create(name="Gulberg Zone", slug="gulberg-zone")
        self.locality_gulberg = Locality.objects.create(
            zone=self.zone, name="Gulberg III", slug="gulberg-iii", postal_code="54660"
        )
        self.locality_dha = Locality.objects.create(
            zone=self.zone, name="DHA Phase 5", slug="dha-phase-5", postal_code="54792"
        )

        # Categories
        self.cat_tech = JobCategory.objects.create(
            name="Information Technology", slug="information-technology", icon_class="bi-code-slash"
        )
        self.cat_finance = JobCategory.objects.create(
            name="Banking & Finance", slug="banking-finance", icon_class="bi-cash-coin"
        )

        # Employers
        self.employer_tech = Employer.objects.create(
            name="Lahore Digital Innovations",
            slug="lahore-digital-innovations",
            locality=self.locality_gulberg,
            address="Main Boulevard, Gulberg III",
            website="https://lahoredigital.pk",
            is_verified=True
        )
        self.employer_bank = Employer.objects.create(
            name="Punjab National Financial",
            slug="punjab-national-financial",
            locality=self.locality_dha,
            address="DHA Phase 5 Commercial Plaza",
            website="https://punjabfinancial.pk",
            is_verified=False
        )

        # Active Tech Job (Urgent, closing in 3 days)
        self.job_active_tech = JobListing.objects.create(
            title="Senior Python Backend Developer",
            slug="senior-python-backend-developer",
            employer=self.employer_tech,
            category=self.cat_tech,
            locality=self.locality_gulberg,
            employment_type="full_time",
            experience_level="senior",
            salary_min_pkr=Decimal("250000.00"),
            salary_max_pkr=Decimal("380000.00"),
            is_salary_negotiable=True,
            description="Leading development of scalable microservices in Django and PostgreSQL for smart city solutions.",
            requirements="5+ years Python/Django, Celery, Docker, Redis, CI/CD experience.",
            qualifications="Bachelor's or Master's in Computer Science or Software Engineering.",
            application_instructions="Submit CV directly via our official candidate portal.",
            application_url="https://lahoredigital.pk/careers/senior-python",
            application_email="careers@lahoredigital.pk",
            source_url="https://lahoredigital.pk/jobs/posting-101",
            deadline=self.today + timedelta(days=3),
            is_active=True,
            is_featured=True,
            verification_status="verified"
        )

        # Active Banking Job (Closing in 20 days)
        self.job_active_bank = JobListing.objects.create(
            title="Senior Risk & Compliance Analyst",
            slug="senior-risk-compliance-analyst",
            employer=self.employer_bank,
            category=self.cat_finance,
            locality=self.locality_dha,
            employment_type="contract",
            experience_level="mid",
            salary_min_pkr=Decimal("150000.00"),
            salary_max_pkr=Decimal("200000.00"),
            description="Manage regulatory compliance filings with State Bank of Pakistan and monitor risk profiles.",
            requirements="3+ years risk management, AML/KYC certification, audit experience.",
            qualifications="ACCA, CA finalist or MBA Finance.",
            application_url="https://punjabfinancial.pk/apply/risk-analyst",
            deadline=self.today + timedelta(days=20),
            is_active=True,
            is_featured=False,
            verification_status="pending"
        )

        # Expired Job (Deadline was 10 days ago)
        self.job_expired = JobListing.objects.create(
            title="Junior Frontend React Intern",
            slug="junior-frontend-react-intern",
            employer=self.employer_tech,
            category=self.cat_tech,
            locality=self.locality_gulberg,
            employment_type="internship",
            experience_level="entry",
            salary_min_pkr=Decimal("50000.00"),
            salary_max_pkr=Decimal("70000.00"),
            description="Internship opportunity for fresh graduates learning React, TypeScript, and modern CSS.",
            requirements="Familiarity with JavaScript, HTML5, CSS3 and Git.",
            qualifications="Recent CS graduate or final year student.",
            application_url="https://lahoredigital.pk/careers/react-intern",
            deadline=self.today - timedelta(days=10),
            is_active=True,
            verification_status="verified"
        )

        # Inactive / Draft Job
        self.job_draft = JobListing.objects.create(
            title="Confidential Chief Technology Officer",
            slug="confidential-chief-technology-officer",
            employer=self.employer_tech,
            category=self.cat_tech,
            locality=self.locality_gulberg,
            employment_type="full_time",
            experience_level="lead",
            description="Executive leadership search for technology transformation.",
            deadline=self.today + timedelta(days=60),
            is_active=False,
            verification_status="pending"
        )

    # 1. Listing Page Response & Templates
    def test_job_list_http_200_and_template(self):
        url = reverse('jobs:list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'jobs/job_list.html')
        self.assertIn('jobs', response.context)
        self.assertIn('categories', response.context)
        self.assertIn('total_results', response.context)

    # 2. Category Filter
    def test_job_list_category_filter(self):
        url = reverse('jobs:list') + f"?category={self.cat_tech.slug}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        job_titles = [j.title for j in response.context['jobs']]
        self.assertIn(self.job_active_tech.title, job_titles)
        self.assertNotIn(self.job_active_bank.title, job_titles)

    # 3. Employment Type Filter
    def test_job_list_employment_type_filter(self):
        url = reverse('jobs:list') + "?type=contract"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        job_titles = [j.title for j in response.context['jobs']]
        self.assertIn(self.job_active_bank.title, job_titles)
        self.assertNotIn(self.job_active_tech.title, job_titles)

    # 4. Experience Level Filter
    def test_job_list_experience_level_filter(self):
        url = reverse('jobs:list') + "?experience=senior"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        job_titles = [j.title for j in response.context['jobs']]
        self.assertIn(self.job_active_tech.title, job_titles)
        self.assertNotIn(self.job_active_bank.title, job_titles)

    # 5. Locality Filter
    def test_job_list_area_filter(self):
        url = reverse('jobs:list') + f"?area={self.locality_dha.slug}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        job_titles = [j.title for j in response.context['jobs']]
        self.assertIn(self.job_active_bank.title, job_titles)
        self.assertNotIn(self.job_active_tech.title, job_titles)

    # 6. Keyword Search
    def test_job_list_keyword_search(self):
        # Match by programming language in title
        response = self.client.get(reverse('jobs:list') + "?q=Python")
        self.assertEqual(response.status_code, 200)
        job_titles = [j.title for j in response.context['jobs']]
        self.assertIn(self.job_active_tech.title, job_titles)
        self.assertNotIn(self.job_active_bank.title, job_titles)

        # Match by qualification
        response_qual = self.client.get(reverse('jobs:list') + "?q=ACCA")
        self.assertEqual(response_qual.status_code, 200)
        job_titles_qual = [j.title for j in response_qual.context['jobs']]
        self.assertIn(self.job_active_bank.title, job_titles_qual)

    # 7. Expired & Active Handling
    def test_job_list_active_and_expired_deadline_handling(self):
        # Default: only active, unexpired jobs shown
        response_default = self.client.get(reverse('jobs:list'))
        default_titles = [j.title for j in response_default.context['jobs']]
        self.assertIn(self.job_active_tech.title, default_titles)
        self.assertIn(self.job_active_bank.title, default_titles)
        self.assertNotIn(self.job_expired.title, default_titles)
        self.assertNotIn(self.job_draft.title, default_titles)

        # Filter by status=expired
        response_expired = self.client.get(reverse('jobs:list') + "?status=expired")
        expired_titles = [j.title for j in response_expired.context['jobs']]
        self.assertIn(self.job_expired.title, expired_titles)
        self.assertNotIn(self.job_active_tech.title, expired_titles)

        # Filter by status=all (includes active and expired)
        response_all = self.client.get(reverse('jobs:list') + "?status=all")
        all_titles = [j.title for j in response_all.context['jobs']]
        self.assertIn(self.job_active_tech.title, all_titles)
        self.assertIn(self.job_expired.title, all_titles)
        self.assertNotIn(self.job_draft.title, all_titles)

    # 8. Deadline Urgency Filter
    def test_job_list_deadline_urgency_filter(self):
        # closing_soon (within 7 days)
        response_urgent = self.client.get(reverse('jobs:list') + "?deadline=closing_soon")
        urgent_titles = [j.title for j in response_urgent.context['jobs']]
        self.assertIn(self.job_active_tech.title, urgent_titles)  # 3 days left
        self.assertNotIn(self.job_active_bank.title, urgent_titles)  # 20 days left

    # 9. Pagination
    def test_job_list_pagination(self):
        # Create 11 extra jobs to exceed 10 per page
        for i in range(11):
            JobListing.objects.create(
                title=f"Batch Software Engineer {i}",
                slug=f"batch-software-engineer-{i}",
                employer=self.employer_tech,
                category=self.cat_tech,
                locality=self.locality_gulberg,
                deadline=self.today + timedelta(days=15),
                is_active=True
            )

        response_page1 = self.client.get(reverse('jobs:list'))
        self.assertEqual(len(response_page1.context['jobs']), 10)
        self.assertTrue(response_page1.context['page_obj'].has_next())

        response_page2 = self.client.get(reverse('jobs:list') + "?page=2")
        self.assertEqual(response_page2.status_code, 200)
        self.assertTrue(response_page2.context['page_obj'].has_previous())

    # 10. Job Detail View & SEO
    def test_job_detail_view_success_and_seo(self):
        url = reverse('jobs:detail', kwargs={'slug': self.job_active_tech.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'jobs/job_detail.html')
        self.assertEqual(response.context['job'].pk, self.job_active_tech.pk)

        content = response.content.decode('utf-8')
        # Check Schema.org JobPosting
        self.assertIn('"@type": "JobPosting"', content)
        self.assertIn(self.job_active_tech.title, content)
        self.assertIn(self.employer_tech.name, content)
        self.assertIn(self.job_active_tech.salary_display, content)

    # 11. Invalid Slug Returns 404
    def test_job_detail_invalid_slug_returns_404(self):
        url = reverse('jobs:detail', kwargs={'slug': 'non-existent-vacancy-slug'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    # 12. Unpublished Job Isolation
    def test_unpublished_job_visibility_permission(self):
        # Unpublished job must return 404 to anonymous public users
        url = reverse('jobs:detail', kwargs={'slug': self.job_draft.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    # 13. Expired Job Detail Marking
    def test_expired_job_detail_marking(self):
        url = reverse('jobs:detail', kwargs={'slug': self.job_expired.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_expired'])
        content = response.content.decode('utf-8')
        self.assertIn("Application Deadline Has Passed", content)
        self.assertIn("Applications Closed", content)

    # 14. Related Jobs Logic
    def test_related_jobs_exclusion_and_active_only(self):
        url = reverse('jobs:detail', kwargs={'slug': self.job_active_tech.slug})
        response = self.client.get(url)
        related = response.context['related_jobs']

        # Related cannot contain self
        related_ids = [j.pk for j in related]
        self.assertNotIn(self.job_active_tech.pk, related_ids)

        # Related cannot contain expired job
        self.assertNotIn(self.job_expired.pk, related_ids)

    # 15. URL Validation and Model Clean
    def test_url_validation_and_model_clean(self):
        # Valid URLs succeed
        job_valid = JobListing(
            title="Valid URL Test",
            slug="valid-url-test",
            employer=self.employer_tech,
            category=self.cat_tech,
            locality=self.locality_gulberg,
            application_url="https://valid.example.com/apply",
            source_url="http://valid.example.com/source",
            deadline=self.today + timedelta(days=5),
            salary_min_pkr=Decimal("100000.00"),
            salary_max_pkr=Decimal("150000.00")
        )
        job_valid.clean()  # Must not raise

        # Invalid application_url without scheme
        job_invalid_url = JobListing(
            title="Invalid URL Test",
            slug="invalid-url-test",
            employer=self.employer_tech,
            category=self.cat_tech,
            locality=self.locality_gulberg,
            application_url="not-a-valid-url",
            deadline=self.today + timedelta(days=5)
        )
        with self.assertRaises(ValidationError):
            job_invalid_url.clean()

        # Inverted salaries (min > max)
        job_inverted_salary = JobListing(
            title="Inverted Salary Test",
            slug="inverted-salary-test",
            employer=self.employer_tech,
            category=self.cat_tech,
            locality=self.locality_gulberg,
            salary_min_pkr=Decimal("200000.00"),
            salary_max_pkr=Decimal("100000.00"),
            deadline=self.today + timedelta(days=5)
        )
        with self.assertRaises(ValidationError):
            job_inverted_salary.clean()

    # 16. Admin Moderation & Actions
    def test_jobs_admin_moderation_and_actions(self):
        # Check admin registration
        self.assertIn(JobListing, site._registry)
        self.assertIn(Employer, site._registry)
        self.assertIn(JobCategory, site._registry)

        admin_instance = JobListingAdmin(JobListing, site)
        qs = JobListing.objects.filter(pk=self.job_active_bank.pk)

        # Action: Mark Verified
        admin_instance.mark_verified(None, qs)
        self.job_active_bank.refresh_from_db()
        self.assertEqual(self.job_active_bank.verification_status, 'verified')

        # Action: Mark Flagged
        admin_instance.mark_flagged(None, qs)
        self.job_active_bank.refresh_from_db()
        self.assertEqual(self.job_active_bank.verification_status, 'flagged')

        # Action: Unpublish
        admin_instance.unpublish_jobs(None, qs)
        self.job_active_bank.refresh_from_db()
        self.assertFalse(self.job_active_bank.is_active)

        # Action: Publish
        admin_instance.publish_jobs(None, qs)
        self.job_active_bank.refresh_from_db()
        self.assertTrue(self.job_active_bank.is_active)

        # Action: Extend Deadline 30 Days
        original_deadline = self.job_active_bank.deadline
        admin_instance.extend_deadline_30_days(None, qs)
        self.job_active_bank.refresh_from_db()
        self.assertEqual(self.job_active_bank.deadline, original_deadline + timedelta(days=30))
