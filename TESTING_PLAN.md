# Quality Assurance & Comprehensive Testing Plan
> **Project:** Lahore City Hub (LCH)  
> **Testing Framework:** `pytest`, `pytest-django`, `factory_boy`, `coverage.py`  
> **Target Code Coverage:** >= 85% Across All Business Applications  
> **Document Version:** 1.0.0  
> **Status:** Final Architectural Specification

---

## 1. Quality Assurance Strategy & The Testing Pyramid

Quality assurance for **Lahore City Hub** guarantees that data accuracy, permission barriers, SEO tags, and transactional workflows operate flawlessly across local development and production deployments.

```
                  / \
                 /   \
                / E2E \       10% Smoke & Workflow Tests
               /-------\      (Claim approval lifecycle, Search UX)
              / Integr. \     30% View, Form, and Security Tests
             /-----------\    (Status codes, permissions, CSRF, JSON-LD)
            / Unit Tests  \   60% Model, Queryset, and Utility Tests
           /---------------\  (Validation, slugging, filters, helpers)
```

---

## 2. Test Framework & Tooling Ecosystem

| Tool | Purpose | Configuration / Integration |
| :--- | :--- | :--- |
| **`pytest`** | Modern test runner & assertion framework | Fast parallel execution, fixture reusability. |
| **`pytest-django`** | Django test runner integration | Database transaction management (`@pytest.mark.django_db`). |
| **`factory_boy`** | Model factories for test fixture generation | Generates dynamic, realistic test instances without hardcoded fixtures. |
| **`faker`** | Realistic localized dummy data | Generates Pakistani names, addresses, and phone numbers during testing. |
| **`coverage.py`** | Automated coverage measurement | Enforces >= 85% threshold; fails CI if coverage drops. |
| **`flake8` & `black`**| Style enforcement & code formatting | PEP 8 adherence, consistent codebase formatting. |
| **`isort`** | Import order normalization | Enforces strict standard/third-party/local import hierarchy. |

---

## 3. Test Suites Breakdown by Layer

### 3.1 Unit Testing Layer (60% Weight)
- **Model Tests (`test_models.py`):**
  - Verify auto-generation of unique SEO slugs from English titles.
  - Verify that `last_verified_at` and `verified_by` populate correctly when `verification_status` transitions to `verified`.
  - Validate custom model constraints (e.g., `salary_min <= salary_max` in `JobListing`).
  - Test custom Model Managers and QuerySet filters (e.g., `Place.objects.verified()`, `JobListing.objects.active_and_valid()`).
- **Form Tests (`test_forms.py`):**
  - Clean methods: telephone format normalization (`+92...`), URL scheme validation.
  - Business claim document upload validation (rejecting `.exe` or files > 10MB).
  - Review form validation: ratings restricted to 1–5 range, rejection of empty text.
- **Template Tag & Service Tests:**
  - Verify custom filters in `apps.core.templatetags.core_tags`.
  - Test `SearchRouter` token parsing and query aggregation across multiple models.

### 3.2 Integration Testing Layer (30% Weight)
- **View & Routing Tests (`test_views.py`):**
  - Verify HTTP 200 OK responses on all public directory list and detail views.
  - Test faceted search queries (e.g., `?locality=gulberg&cuisine=desi`) and confirm query results are filtered accurately.
  - Verify pagination behavior (page 1, page 2, invalid page numbers returning 404).
  - Test HTTP 404 handling for nonexistent slugs or inactive listings.
- **Authorization & Access Control Tests:**
  - Verify anonymous users receive HTTP 302 redirect to login when attempting to bookmark or claim listings.
  - Test that business owners can only update their own claimed businesses (HTTP 403 Forbidden on foreign entity IDs).
  - Test staff-only quarantine on Django Admin and moderation queues.
- **SEO & Structured Data Integration:**
  - Assert that `<title>` and `<meta name="description">` tags exist and match formula constraints.
  - Extract and validate embedded `<script type="application/ld+json">` payloads using `json.loads()` to verify valid Schema.org structure.
  - Validate `/sitemap.xml` returns valid XML containing only active entities.

### 3.3 End-to-End Workflow Tests (10% Weight)
- **Workflow A: Business Claim Lifecycle:**
  1. Member user submits a business claim with proof file.
  2. Moderation queue verifies pending record created.
  3. Staff user approves claim in admin.
  4. Business status switches to `official_claimed`, audit log records `verified_by`, claimant role elevates to `Business Owner`.
- **Workflow B: Review Submission & Moderation:**
  1. Authenticated user posts review.
  2. Review initially displays status `pending` (hidden from public view).
  3. Moderator approves review.
  4. Review becomes visible; average rating recalculates.

---

## 4. Test Factory Specifications (`factory_boy`)

```python
# apps/core/tests/factories.py example
import factory
from faker import Faker
from apps.accounts.models import CustomUser
from apps.core.models import LocalityZone, Locality
from apps.places.models import PlaceCategory, Place

fake = Faker(['en_US'])

class LocalityZoneFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LocalityZone
    name = "Gulberg & Central"
    slug = "gulberg-central"

class LocalityFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Locality
    zone = factory.SubFactory(LocalityZoneFactory)
    name = "Gulberg III"
    slug = "gulberg-iii"
    postal_code = "54660"

class PlaceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Place
    title = factory.Sequence(lambda n: f"Historical Site {n}")
    summary = "A prominent historical landmark in Lahore."
    description = "Full historical and architectural description."
    locality = factory.SubFactory(LocalityFactory)
    address = "Main Boulevard, Gulberg"
    verification_status = "verified"
    is_active = True
```

---

## 5. Continuous Integration (CI) Pipeline

The automated CI pipeline executes on every Git Push and Pull Request targeting `main` or `develop`:

```yaml
# .github/workflows/ci.yml structure
name: Lahore City Hub CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python 3.12
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install Dependencies
        run: |
          pip install --upgrade pip
          pip install -r requirements/local.txt

      - name: Code Quality & Linting
        run: |
          black --check .
          isort --check-only .
          flake8 .

      - name: Run Pytest Suite with Coverage
        run: |
          pytest --cov=apps --cov-report=term-missing --cov-fail-under=85
```
