# Application Directory & Modular Code Structure
> **Project:** Lahore City Hub (LCH)  
> **Framework:** Django 5.2 LTS  
> **Architecture:** Clean Modular Monolith (`apps/` namespaced)  
> **Document Version:** 1.0.0  
> **Status:** Final Architectural Specification

---

## 1. Project Directory Tree Layout

The project structure is organized with a dedicated `apps/` directory to prevent root clutter, alongside centralized configurations, static assets, templates, and fixture data.

```
lahore_city_hub/
├── manage.py
├── pyproject.toml
├── requirements/
│   ├── base.txt
│   ├── local.txt
│   └── production.txt
├── .env.example
├── .gitignore
├── README.md
│
├── config/                          # Central Django Project Configuration
│   ├── __init__.py
│   ├── asgi.py
│   ├── wsgi.py
│   ├── urls.py                      # Global URL router
│   └── settings/
│       ├── __init__.py
│       ├── base.py                  # Common settings (Installed apps, middleware, auth)
│       ├── local.py                 # Development settings (SQLite, DebugToolbar, Console Email)
│       └── production.py            # Production settings (PostgreSQL, WhiteNoise, Security, Sentry)
│
├── apps/                            # Domain Applications Directory
│   ├── __init__.py
│   │
│   ├── core/                        # Core & Cross-Domain Services
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── admin.py
│   │   ├── models.py                # Abstract base models, Locality, EmergencyHelpline
│   │   ├── views.py                 # Homepage, global search, civic info, error views
│   │   ├── urls.py
│   │   ├── forms.py
│   │   ├── sitemaps.py              # Dynamic XML sitemaps
│   │   ├── context_processors.py    # Global context (emergency ribbon, active localities)
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   └── search.py            # Unified multi-model search aggregator
│   │   ├── templatetags/
│   │   │   ├── __init__.py
│   │   │   └── core_tags.py         # Custom template filters, URL helpers, icon helpers
│   │   └── tests/
│   │       ├── test_models.py
│   │       ├── test_views.py
│   │       └── test_search.py
│   │
│   ├── accounts/                    # User Authentication & Profiles
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── admin.py
│   │   ├── models.py                # CustomUser, UserProfile, UserBookmark
│   │   ├── views.py                 # Login, Register, Profile Dashboard, Bookmark Views
│   │   ├── urls.py
│   │   ├── forms.py                 # Registration, profile edit, password reset forms
│   │   ├── signals.py               # Auto-create UserProfile upon user creation
│   │   └── tests/
│   │
│   ├── places/                      # Tourist Places & Cultural Heritage
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── admin.py
│   │   ├── models.py                # PlaceCategory, Place, PlaceGalleryImage
│   │   ├── views.py                 # PlaceListView, PlaceDetailView
│   │   ├── urls.py
│   │   └── tests/
│   │
│   ├── restaurants/                 # Dining & Food Guides
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── admin.py
│   │   ├── models.py                # Cuisine, RestaurantFeature, Restaurant, MenuHighlight
│   │   ├── views.py                 # RestaurantListView, RestaurantDetailView
│   │   ├── urls.py
│   │   └── tests/
│   │
│   ├── hospitals/                   # Healthcare & Emergency Facilities
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── admin.py
│   │   ├── models.py                # MedicalSpecialty, Hospital
│   │   ├── views.py                 # HospitalListView, HospitalDetailView, EmergencyQuickView
│   │   ├── urls.py
│   │   └── tests/
│   │
│   ├── education/                   # Universities, Colleges & Schools
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── admin.py
│   │   ├── models.py                # EducationType, AccreditationBoard, Institution
│   │   ├── views.py                 # InstitutionListView, InstitutionDetailView
│   │   ├── urls.py
│   │   └── tests/
│   │
│   ├── jobs/                        # Lahore Jobs Directory
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── admin.py
│   │   ├── models.py                # JobCategory, Employer, JobListing
│   │   ├── views.py                 # JobListView, JobDetailView, EmployerDetailView
│   │   ├── urls.py
│   │   ├── forms.py
│   │   └── tests/
│   │
│   ├── businesses/                  # Commercial Directory & Claiming
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── admin.py
│   │   ├── models.py                # BusinessCategory, Business, BusinessClaim
│   │   ├── views.py                 # BusinessListView, BusinessDetailView, ClaimBusinessView
│   │   ├── urls.py
│   │   ├── forms.py                 # ClaimSubmissionForm
│   │   └── tests/
│   │
│   ├── transport/                   # Transit Guides & Timetables
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── admin.py
│   │   ├── models.py                # TransitMode, TransitRoute, TransitStation
│   │   ├── views.py                 # TransitOverviewView, RouteDetailView
│   │   ├── urls.py
│   │   └── tests/
│   │
│   ├── events/                      # Local Events Calendar
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── admin.py
│   │   ├── models.py                # EventCategory, EventVenue, Event
│   │   ├── views.py                 # EventListView, EventDetailView, EventCalendarView
│   │   ├── urls.py
│   │   └── tests/
│   │
│   ├── updates/                     # City Advisories & Smog Alerts
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── admin.py
│   │   ├── models.py                # UpdateCategory, CityUpdate
│   │   ├── views.py                 # UpdateListView, UpdateDetailView
│   │   ├── urls.py
│   │   └── tests/
│   │
│   └── reviews/                     # Generic Reviews & Ratings
│       ├── __init__.py
│       ├── apps.py
│       ├── admin.py
│       ├── models.py                # Review
│       ├── views.py                 # SubmitReviewView, DeleteReviewView
│       ├── urls.py
│       ├── forms.py                 # ReviewForm
│       └── tests/
│
├── templates/                       # Master UI Templates
│   ├── base.html                    # Root base layout
│   ├── navbar.html                  # Global top header & navigation
│   ├── footer.html                  # Civic footer with links & disclaimers
│   ├── 404.html                     # Custom SEO-friendly 404
│   ├── 500.html                     # Custom 500 handler
│   ├── components/                  # Reusable UI partials
│   │   ├── _breadcrumbs.html
│   │   ├── _verification_badge.html
│   │   ├── _emergency_ribbon.html
│   │   ├── _pagination.html
│   │   ├── _rating_stars.html
│   │   └── _claim_banner.html
│   ├── layouts/
│   │   ├── directory_list.html      # Master list view with faceted sidebar
│   │   └── directory_detail.html    # Master detail view
│   ├── core/                        # Homepage & global search templates
│   ├── accounts/                    # Auth & dashboard templates
│   ├── places/
│   ├── restaurants/
│   ├── hospitals/
│   ├── education/
│   ├── jobs/
│   ├── businesses/
│   ├── transport/
│   ├── events/
│   ├── updates/
│   └── reviews/
│
├── static/                          # Static Frontend Assets
│   ├── css/
│   │   ├── custom.css               # Lahore City Hub theme styling
│   │   └── bootstrap.min.css        # Bootstrap 5.3 distribution
│   ├── js/
│   │   ├── main.js                  # Global UI interactions (dropdowns, search autocomplete)
│   │   └── bootstrap.bundle.min.js
│   └── img/
│       ├── logo.svg
│       ├── favicon.ico
│       ├── og-default.jpg
│       └── lahore-skyline-vector.svg
│
├── fixtures/                        # Initial Verified Geographic & Category Seed Data
│   ├── 01_locality_zones.json       # Lahore administrative zones
│   ├── 02_localities.json           # 80+ standard Lahore localities
│   ├── 03_emergency_helplines.json  # Verified civic emergency numbers
│   ├── 04_transit_routes.json       # Orange Line & Metro Bus route data
│   └── 05_categories.json           # Initial taxonomies across all directory apps
│
└── docs/                            # Project Architecture & Operational Documentation
```

---

## 2. App-by-App Responsibility & Technical Justification

### App 1: `core`
- **Justification:** Centralizes shared domain logic, preventing circular dependencies between directory apps. Hosts the abstract base models (`ListingBase`, `TimeStampedModel`, `VerifiableModel`, etc.), Lahore locality geography models, dynamic XML sitemaps, global search coordinator, and homepage views.
- **Key Inter-app links:** Every other directory app imports base classes from `apps.core.models`.

### App 2: `accounts`
- **Justification:** Encapsulates the custom user model (`CustomUser`), profile dashboard, bookmark storage, and authentication workflows. Keeping `accounts` independent ensures user security logic is quarantined from public directory queries.
- **Key Inter-app links:** Directory listings reference `accounts.CustomUser` for claims and verification audits.

### App 3: `places`
- **Justification:** Dedicated to cultural, heritage, and leisure tourism. Captures museum rules, photography policies, architectural eras, and heritage preservation data specific to Lahore’s Walled City and historical monuments.

### App 4: `restaurants`
- **Justification:** Dedicated dining domain. Manages cuisines, seating features (family halls, rooftops), price tiers, Ramadan timings (Sehri/Iftar), and signature dishes.

### App 5: `hospitals`
- **Justification:** Dedicated healthcare domain requiring life-critical metadata: 24/7 emergency trauma status, on-site blood banks, ambulance contact exchanges, and clinical specialties.

### App 6: `education`
- **Justification:** Focuses on institutional education, tracking accreditation bodies (HEC, PEC, PMDC, BISE), gender policies, campus locations, and annual admission cycles.

### App 7: `jobs`
- **Justification:** Localized employment directory. Requires transactional lifecycle management (deadlines, expiration states, verified employers, direct application redirects).

### App 8: `businesses`
- **Justification:** Commercial directory for private enterprises, services, and retail shops. Hosts the proprietary `BusinessClaim` workflow enabling owners to submit verification proof.

### App 9: `transport`
- **Justification:** Public and intercity transit guides. Encapsulates transit modes, fixed routes (Orange Line, Metrobus, Speedo feeder buses), station sequences, and fare structures.

### App 10: `events`
- **Justification:** Time-sensitive event calendar. Manages venue mappings, ticket pricing, start/end datetimes, and automated archiving of past events.

### App 11: `updates`
- **Justification:** Real-time civic notifications, smog levels, traffic diversions, and emergency municipal advisories. Strictly tracks issuing government authorities and source URLs.

### App 12: `reviews`
- **Justification:** Generic rating and review engine. By leveraging Django’s ContentTypes framework (`GenericForeignKey`), reviews can be attached to any directory model without modifying directory app schemas.

---

## 3. Inter-App Communication Patterns & Guidelines

To maintain decoupling and prevent circular import antipatterns:
1. **Model Inheritance:** Child apps import *only* abstract models from `apps.core.models`. They never import sibling domain models directly.
2. **Foreign Key Strategy:** Where an inter-app relationship is needed (e.g., `Place` referencing `transport.TransitStation`), use lazy string references (`'transport.TransitStation'`) rather than direct Python class imports.
3. **Generic Foreign Keys for Cross-Cutting Services:** `reviews.Review` and `accounts.UserBookmark` reference domain listings via `django.contrib.contenttypes.models.ContentType` and `object_id`.
4. **Signals:** Signal handlers (such as automatic profile creation upon user registration) are connected inside `apps.accounts.signals` and registered via `accounts.apps.AccountsConfig.ready()`.
