# Phased Development Roadmap & Implementation Plan
> **Project:** Lahore City Hub (LCH)  
> **Methodology:** Agile / Phased Milestones with Strict Verification Gates  
> **Document Version:** 1.0.0  
> **Status:** Final Architectural Specification

---

## 1. Project Phase Overview

The construction of **Lahore City Hub** is organized into 7 sequential, testable phases. In accordance with senior engineering discipline:
- *Inspect before editing.*
- *Plan before coding.*
- *Avoid unnecessary packages.*
- *Never generate the whole application in a single unmanageable blast.*

```
+-----------------------------------------------------------------------------------------+
| PHASE 1: Architecture, Data Modeling & Governance Documentation [COMPLETED & PENDING SIGN-OFF]
+-----------------------------------------------------------------------------------------+
                                           |
                                           v
+-----------------------------------------------------------------------------------------+
| PHASE 2: Scaffolding, Core Engine, Accounts, Auth & Base UI Layout                      |
+-----------------------------------------------------------------------------------------+
                                           |
                                           v
+-----------------------------------------------------------------------------------------+
| PHASE 3: Core Public Directories (Places, Restaurants, Hospitals, Education)           |
+-----------------------------------------------------------------------------------------+
                                           |
                                           v
+-----------------------------------------------------------------------------------------+
| PHASE 4: Dynamic Civic Modules (Jobs, Transport Guides, Events, City Advisories)         |
+-----------------------------------------------------------------------------------------+
                                           |
                                           v
+-----------------------------------------------------------------------------------------+
| PHASE 5: Business Directory, Ownership Claiming & Generic Moderated Reviews             |
+-----------------------------------------------------------------------------------------+
                                           |
                                           v
+-----------------------------------------------------------------------------------------+
| PHASE 6: Global Faceted Search Engine, Advanced SEO, JSON-LD Schemas & Performance Cache|
+-----------------------------------------------------------------------------------------+
                                           |
                                           v
+-----------------------------------------------------------------------------------------+
| PHASE 7: Full QA Suite, OWASP Security Hardening & Production Container Readiness       |
+-----------------------------------------------------------------------------------------+
```

---

## 2. Detailed Milestone & Deliverable Breakdown

### Phase 1: Planning, Architecture & Requirements (Current Milestone)
- **Status:** **Completed (Awaiting User Sign-off)**
- **Deliverables:**
  - `PROJECT_OVERVIEW.md` (Mission, audience personas, KPIs)
  - `REQUIREMENTS.md` (SRS for all 15 features, NFRs, traceability matrix)
  - `ARCHITECTURE.md` (Modular monolith, high-level diagrams, shared model hierarchy)
  - `DATABASE_DESIGN.md` (Full ERD, model field definitions, indexing rules)
  - `APP_STRUCTURE.md` (Tree hierarchy, app justification, inter-app communication)
  - `USER_ROLES_AND_PERMISSIONS.md` (RBAC matrix, business claim lifecycle, audit logs)
  - `UI_UX_PLAN.md` (Design tokens, mobile-first breakpoints, wireframes)
  - `SEO_STRATEGY.md` (Canonical taxonomy, JSON-LD schemas, XML sitemaps, robots.txt)
  - `SECURITY_PLAN.md` (OWASP Top 10 mitigation, rate limiting, upload hardening)
  - `TESTING_PLAN.md` (Testing pyramid, tooling, factories, CI workflow)
  - `DEVELOPMENT_ROADMAP.md` (Phased schedule, risks, definition of done)
- **Verification Gate:** Formal review and approval from product owner before creating application code.

---

### Phase 2: Project Scaffolding, Core Engine, Accounts & Base Layout
- **Objective:** Establish the foundational Django environment, database migrations for core and accounts, master HTML5/Bootstrap 5 layouts, and authentication.
- **Key Tasks:**
  1. Scaffold `config/settings/` (`base.py`, `local.py`, `production.py`) and environment variables (`.env.example`).
  2. Implement `apps.core.models` (`TimeStampedModel`, `SluggableModel`, `VerifiableModel`, `ContactableModel`, `LocationModel`, `SEOModel`, `ListingBase`, `LocalityZone`, `Locality`, `EmergencyHelpline`).
  3. Implement `apps.accounts` with `CustomUser` (email as identifier), profile signals, and authentication views.
  4. Build master template hierarchy: `base.html`, `navbar.html`, `footer.html`, `_emergency_ribbon.html`, and static asset pipelines (Bootstrap 5, custom CSS/JS).
  5. Load initial geographic seed fixtures (`01_locality_zones.json`, `02_localities.json`, `03_emergency_helplines.json`).
- **Definition of Done (DoD):**
  - Developer can run migrations cleanly on SQLite.
  - User can register, log in, view their profile dashboard, and log out.
  - Responsive navbar and emergency helpline ribbon render seamlessly on mobile and desktop.
  - All Phase 2 unit tests pass with zero errors.

---

### Phase 3: Core Public Directories (Places, Restaurants, Hospitals, Education)
- **Objective:** Deliver the primary foundational information directories that attract tourist and resident web traffic.
- **Key Tasks:**
  1. **`apps.places`**: Models (`PlaceCategory`, `Place`, `PlaceGalleryImage`), list/detail views, filtering by heritage era and accessibility.
  2. **`apps.restaurants`**: Models (`Cuisine`, `RestaurantFeature`, `Restaurant`, `MenuHighlight`), list/detail views, filtering by cuisine, price tier, and family hall amenities.
  3. **`apps.hospitals`**: Models (`MedicalSpecialty`, `Hospital`), list/detail views, emergency trauma filtering, direct call links.
  4. **`apps.education`**: Models (`EducationType`, `AccreditationBoard`, `Institution`), list/detail views, filtering by accreditation and institution tier.
  5. Standardized `directory_list.html` and `directory_detail.html` layouts with breadcrumbs and verified badges.
- **Definition of Done (DoD):**
  - Verified sample data for prominent Lahore landmarks (e.g. Badshahi Mosque, Shaukat Khanum, GCU, Haveli) displays accurately.
  - Detail pages show telephone numbers, map directions, operating hours, and last-verified timestamps.
  - Test suites for places, restaurants, hospitals, and education achieve > 85% coverage.

---

### Phase 4: Dynamic Civic Modules (Jobs, Transport, Events, Updates)
- **Objective:** Implement time-sensitive civic services and practical daily city utilities.
- **Key Tasks:**
  1. **`apps.jobs`**: Models (`JobCategory`, `Employer`, `JobListing`), deadline expiry filtering, direct application mechanism.
  2. **`apps.transport`**: Models (`TransitMode`, `TransitRoute`, `TransitStation`), Orange Line Metro and Metrobus line guides, station lookup.
  3. **`apps.events`**: Models (`EventCategory`, `EventVenue`, `Event`), calendar/list views, automated past-event archiving.
  4. **`apps.updates`**: Models (`UpdateCategory`, `CityUpdate`), severity ribbons (Smog alert, traffic diversions), official source citations.
- **Definition of Done (DoD):**
  - Transport pages render station lists and interchange points.
  - Expired job listings automatically hide from public search.
  - Emergency advisories display on the homepage banner ticker.

---

### Phase 5: Commercial Directory, Business Claims & Generic Reviews
- **Objective:** Enable local business engagement, community reviews, and verified merchant claiming.
- **Key Tasks:**
  1. **`apps.businesses`**: Models (`BusinessCategory`, `Business`, `BusinessClaim`), WhatsApp direct integration.
  2. Business Claim Submission Form with file upload validation (proofs).
  3. Staff moderation queue in Django Admin for approving/rejecting claims.
  4. **`apps.reviews`**: Generic rating and review engine (`GenericForeignKey`), review submission form, anti-spam moderation queue.
  5. User bookmarking engine (`UserBookmark`) with dashboard saved list.
- **Definition of Done (DoD):**
  - Business owners can submit claim proofs; approved claims grant profile editing access.
  - User reviews remain pending until approved by a moderator.
  - Authenticated members can toggle bookmarks with optimistic UI updates.

---

### Phase 6: Global Faceted Search, Advanced SEO & Performance Caching
- **Objective:** Unify discovery across all 10 directories and optimize for web crawlers and sub-second load times.
- **Key Tasks:**
  1. Build `apps.core.services.search.SearchRouter` providing cross-model query aggregation with category count tabs.
  2. Implement Schema.org JSON-LD structured data generators across all detail views.
  3. Configure dynamic XML sitemap partition (`sitemaps.py`) and `robots.txt`.
  4. Configure template fragment caching on global navigation, category indexes, and helpline ribbons.
  5. Verify Google Lighthouse performance, accessibility, and SEO audit scores (> 90).
- **Definition of Done (DoD):**
  - Search query "Gulberg" returns categorized hits (e.g., 8 Restaurants, 3 Hospitals, 5 Jobs).
  - Valid Schema.org JSON-LD passes Google Rich Results Test without critical errors.
  - XML sitemaps render valid XML conforming to Sitemaps protocol.

---

### Phase 7: Comprehensive QA, Security Hardening & Production Readiness
- **Objective:** Final end-to-end verification, security audits, and deployment configuration.
- **Key Tasks:**
  1. Complete test suite execution (`pytest --cov=apps`) verifying >= 85% coverage.
  2. Security audit: verify CSP headers, HSTS, secure cookies, rate limiting, and brute-force lockout (`django-axes`).
  3. Production settings configuration (`config/settings/production.py`) with PostgreSQL connection pooling, WhiteNoise manifest storage, and logging.
  4. Dockerfile, `docker-compose.yml`, and Gunicorn/Nginx deployment templates.
- **Definition of Done (DoD):**
  - Zero high/critical vulnerability findings from `pip-audit`.
  - Automated CI test pipeline passes green.
  - Ready for immediate staging/production deployment upon client infrastructure provisioning.

---

## 3. Technical Risk Assessment & Mitigation Strategies

| Risk Identifier | Impact | Likelihood | Mitigation Strategy |
| :--- | :---: | :---: | :--- |
| **TR-01: Stale / Outdated Directory Information** | High | High | Display explicit `last_verified_at` dates; schedule periodic automated email reminders to claimed business owners to confirm opening hours and phone numbers; provide community "Suggest an Edit" button. |
| **TR-02: Review Spam & Astroturfing** | Medium | Medium | Implement pre-moderation queue; enforce unique constraint on user-entity pairs; apply rate limiting and regex profanity filters. |
| **TR-03: Fraudulent Business Takeovers** | High | Low | Require institutional email domain or formal registration documents (SECP/bill); review claims through a manual moderator queue before granting owner privileges. |
| **TR-04: Multi-Model Search Latency on SQLite** | Medium | Medium | Abstract search router to use optimized Django `Q` lookups with `select_related` in development, with seamless upgrade path to PostgreSQL Full-Text Search and Trigram similarity (`pg_trgm`) in production. |
| **TR-05: High Server Load During Civic Emergencies (e.g. Smog / Flooding)** | High | Medium | Implement aggressive template fragment caching (Redis/LocMem) on emergency helpline widgets and city updates ticker; serve static assets via CDN/WhiteNoise. |

---

## 4. Definition of Done (DoD) for Phase 1
- [x] All 11 planning and architectural specification documents are created in the project workspace.
- [x] Every document is internally consistent with zero conflicting requirements or duplicated models.
- [x] Database design defines relationships, constraints, indices, and mixin hierarchies.
- [x] SEO strategy addresses URL canonicalization, Schema.org JSON-LD, sitemaps, and robots.txt without promising unverified search engine rankings.
- [x] Data integrity strategy guarantees zero fabricated entities, fake contacts, or hallucinated claims.
- [x] Application development stops here until explicit user sign-off is granted.
