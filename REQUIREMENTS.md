# Requirements Specification (SRS)
> **Project:** Lahore City Hub (LCH)  
> **Document Version:** 1.0.0  
> **Standard:** IEEE 830 / ISO/IEC/IEEE 29148 Compliant Hybrid Specification  
> **Status:** Final Baseline for Phase 1

---

## 1. Introduction & Scope

This Requirements Specification establishes the complete functional and non-functional requirements for the **Lahore City Hub** digital portal. It acts as the contract between architectural design, database modeling, user experience, and testing regimes.

---

## 2. Functional Requirements (FR)

### Module 1: Homepage & Global Navigation (FR-01)
- **FR-01.1:** The homepage MUST feature an intuitive Global Search Bar permitting concurrent querying by text (e.g., "biryani", "pediatric clinic", "python developer") and locality dropdown (e.g., "Gulberg", "DHA", "Johar Town", "All Lahore").
- **FR-01.2:** The homepage MUST provide an Emergency & Civic Quick-Ribbon with 1-click access to verified emergency helplines:
  - Rescue 1122
  - Lahore Police (15)
  - Edhi Ambulance (115)
  - Traffic Police Helpline (1915)
  - WASA Drainage Complaint (1334)
  - LESCO Electricity Helpline (118)
- **FR-01.3:** The homepage MUST display dynamic curated sections:
  - *Explore by Category* (10 primary category cards with item counts).
  - *Featured Verified Listings* (highlighted business and tourist spots).
  - *Upcoming Events in Lahore* (next 7 days).
  - *Live City Updates & Advisories* (latest civic, weather, or smog announcements).
- **FR-01.4:** The global navigation header MUST remain sticky or easily accessible, featuring search, top category links, locality selector, and User Profile / Login status.

### Module 2: Tourist Places Directory (FR-02)
- **FR-02.1:** The directory MUST categorize historical, cultural, religious, architectural, and leisure attractions (e.g., Mughal Heritage, Colonial Architecture, Public Parks, Shrines, Museums).
- **FR-02.2:** Each tourist place listing MUST display:
  - Official name (English and Urdu display names).
  - Architectural / Historical Era (e.g., Mughal, British Raj, Contemporary).
  - Verified opening and closing hours, including seasonal variations and prayer break closures.
  - Ticket pricing structure (Pakistani citizens vs. foreign tourists vs. student discounts).
  - Photography rules & permit requirements (mobile phone photography, DSLR, commercial videography).
  - Wheelchair / Accessibility ratings.
  - Interactive Google Maps pin and proximity to nearest Orange Line or Metro Bus station.
  - Curated photo gallery with verified attribution.

### Module 3: Lahore Jobs Directory (FR-03)
- **FR-03.1:** The directory MUST categorize job openings by locality (e.g., Gulberg III, DHA Phase 6, Sundar Industrial Estate), department/discipline (IT & Software, Education, Healthcare, Hospitality, Retail, Manufacturing), and work arrangement (On-site, Hybrid, Remote).
- **FR-03.2:** Each job listing MUST contain:
  - Job title, company name, locality address, and verified employer status.
  - Employment type (Full-time, Part-time, Internship, Contract).
  - Transparent salary range (or explicit "Market Competitive" tag if undisclosed).
  - Application deadline date (with automatic expiry state when deadline passes).
  - Direct verified application mechanism (official career URL or direct HR email; strictly zero intermediary paywalls).
- **FR-03.3:** Anti-Spam & Zero-Fabrication rule: Listings must require verification of employer legitimacy before appearing publicly.

### Module 4: Restaurants & Cafes Directory (FR-04)
- **FR-04.1:** The dining directory MUST support multi-faceted filtering:
  - Cuisine: Traditional Lahori (Desi), Continental, Chinese, Pan-Asian, Fast Food, Artisanal Bakeries, Specialty Coffee.
  - Dining Format: Fine Dining, Casual Family, Street Food (e.g., Gawalmandi, Fort Road, Anarkali), Drive-Thru, Rooftop.
  - Price Tier: `$` (Budget / Street), `$$` (Casual), `$$$` (Upscale), `$$$$` (Fine Dining).
  - Amenities/Badges: Family Hall Available, Outdoor Seating, Air Conditioned, Wi-Fi, Valet Parking, Halal Certified, Prayer Area.
- **FR-04.2:** Each restaurant page MUST include:
  - Verified operating hours, Ramadan timings (Sehri & Iftar buffets during Holy Month).
  - Verified phone numbers for reservations.
  - Locality and exact address with landmark tips.
  - Highlighted signature dishes / menu snippet.

### Module 5: Hospitals & Clinics Directory (FR-05)
- **FR-05.1:** Healthcare listings MUST clearly distinguish between:
  - Public Tertiary Teaching Hospitals (e.g., Mayo Hospital, Jinnah Hospital, Services Hospital, Ganga Ram Hospital).
  - Private Multi-Specialty Hospitals (e.g., Shaukat Khanum, Doctors Hospital, National Hospital DHA).
  - Specialized Clinics (Dental, Eye, Pediatric, Psychiatric).
  - 24/7 Emergency Care and Trauma Centers.
- **FR-05.2:** Each listing MUST highlight:
  - Emergency hotline vs. General OPD appointment exchange numbers.
  - 24/7 Emergency capability badge (Yes/No).
  - 24/7 on-site pharmacy availability.
  - List of primary medical specialties / departments.
  - Blood bank and ambulance contact points.

### Module 6: Education Directory (FR-06)
- **FR-06.1:** Education listings MUST be classified by institutional tier:
  - Universities & Degree Awarding Institutes (e.g., PU, LUMS, UET, Kinnaird, GCU).
  - Intermediate & Degree Colleges.
  - K-12 Schools (Matric/FSc BISE Lahore vs. O/A Levels Cambridge / Edexcel).
  - Vocational, Technical, and IT Training Academies (e.g., TEVTA accredited).
- **FR-06.2:** Each education listing MUST present:
  - Official accreditation bodies (HEC Recognized, PEC Accredited, PMDC/PMC Verified, BISE Lahore Registered).
  - Campus localities (Main Campus, Sub-campuses).
  - Typical annual admission windows (Fall, Spring, Summer cycles).
  - Official admissions office website, email, and verified admissions helpline.

### Module 7: Local Business Directory (FR-07)
- **FR-07.1:** Commercial directory across professional services (Legal, Accounting, IT Solutions, Interior Design, Home Repair, Photography, Real Estate, Automobile Repair).
- **FR-07.2:** Direct Click-to-WhatsApp integration formatted specifically for Pakistani MSMEs, alongside standard phone and email.
- **FR-07.3:** Business Claiming feature: Unclaimed businesses feature a visible "Claim this Business" button, prompting a structured verification questionnaire.

### Module 8: Transport Guides (FR-08)
- **FR-08.1:** Detailed guides for primary public transit networks:
  - **Orange Line Metro Train (OLMT):** Ali Town to Dera Gujran; 26 stations; fare matrices; interchange points; operational timings (06:00 AM – 10:00 PM).
  - **Lahore Metrobus (Green Line):** Gajjumata to Shahdara; 27 stations; dedicated corridor routes and e-ticketing guide.
  - **Speedo Feeder Bus Routes:** Complete list of feeder routes connecting residential sectors to train/metro stations.
  - **Intercity Terminals:** Daewoo Express Thokar Niaz Baig, Badami Bagh General Bus Stand, Niazi Express Band Road.
  - **Railway & Airport:** Lahore Junction Railway Station guide; Allama Iqbal International Airport (LHE) transit and parking guides.
- **FR-08.2:** Downloadable / viewable schematic route maps and fare calculation rules.

### Module 9: Local Events Calendar (FR-09)
- **FR-09.1:** Chronological and category-based event tracking (e.g., Lahore Literary Festival (LLF), Lahore Biennale, horse shows, food festivals, tech conferences, trade expos at Expo Centre Johar Town).
- **FR-09.2:** Event details MUST specify start/end timestamps, venue address, entry requirements (Free, Ticketed, Invitation-only), organizer contact, and official registration URL.
- **FR-09.3:** Events automatically migrate to an "Past Events" archive once their end datetime has elapsed.

### Module 10: City Updates & Advisories (FR-10)
- **FR-10.1:** Real-time publishing of civic advisories:
  - Seasonal Air Quality / Smog Advisories (Punjab Environment Protection Department guidelines).
  - Monsoon Weather & WASA Urban Flooding Advisories.
  - City Traffic Police (CTP) Lahore diversions and route closures (marathons, VIP movements, cricket matches at Gaddafi Stadium).
  - Public holiday announcements (Iqbal Day, Mela Chiraghan, Basant updates if applicable).
- **FR-10.2:** Every update MUST cite an official primary source (official agency circular, gazette, or verified agency handle) with publication timestamp and last-updated timestamp.

### Module 11: User Accounts & Profiles (FR-11)
- **FR-11.1:** Authentication supporting email-based sign-in and password reset workflow.
- **FR-11.2:** User Profile Dashboard allowing:
  - Personal details update.
  - Bookmark / "Saved Places" collection for quick offline retrieval.
  - Submitted reviews tracking and moderation status.
  - Submitted business claims and status history.

### Module 12: Admin Content Management (FR-12)
- **FR-12.1:** Django Admin enhanced with filterable list displays, status badges, search fields, and bulk moderation tools.
- **FR-12.2:** Moderation queues for:
  - User-submitted business claims.
  - User reviews and ratings.
  - Edit suggestions / correction reports.
- **FR-12.3:** Audit logging tracking which staff user approved, edited, or marked an entity as `Verified`.

### Module 13: Global Search & Faceted Discovery (FR-13)
- **FR-13.1:** Single search query dispatches across all relevant directory apps (places, restaurants, hospitals, jobs, businesses, events).
- **FR-13.2:** Search result categorization with hit counts per entity type.
- **FR-13.3:** Faceted filtering by Lahore Localities, Categories, and Verification Status.
- **FR-13.4:** Fallback handling with helpful suggestions when queries return zero results.

### Module 14: Search Engine Optimization (SEO) (FR-14)
- **FR-14.1:** Clean, deterministic, human-readable URL structures using slugified identifiers.
- **FR-14.2:** Unique dynamic `<title>` tags and `<meta name="description">` on every public page.
- **FR-14.3:** Automatic injection of Schema.org JSON-LD structured data matching entity types (`Place`, `Restaurant`, `JobPosting`, `Hospital`, `EducationalOrganization`, `LocalBusiness`, `Event`).
- **FR-14.4:** Categorized dynamic XML Sitemaps and auto-generated `robots.txt`.
- **FR-14.5:** Semantic breadcrumbs on all detail and list views.

### Module 15: Featured Business Listings (FR-15)
- **FR-15.1:** Distinct visual styling ("Featured / Verified Partner" badge) for elevated visibility.
- **FR-15.2:** Priority sorting in directory listings (featured listings appear at top of results within their relevant locality/category).
- **FR-15.3:** Explicit start and end expiration dates with automatic demotion to standard listing upon expiration.

---

## 3. Non-Functional Requirements (NFR)

### 3.1 Performance & Scalability (NFR-01)
- **NFR-01.1:** Time to First Byte (TTFB) under 200ms on server-side rendered pages under standard loads.
- **NFR-01.2:** Database queries per view MUST be bounded (`django-debug-toolbar` verified) using `select_related` and `prefetch_related` to eliminate N+1 query antipatterns.
- **NFR-01.3:** Static assets compressed and hashed via WhiteNoise with long-term cache headers (`Cache-Control: max-age=31536000, immutable`).
- **NFR-01.4:** High-traffic pages (Homepage, Transport guides, Category index) cached via Django's template fragment caching or low-level cache backend.

### 3.2 Security & Data Integrity (NFR-02)
- **NFR-02.1:** Full compliance with OWASP Top 10 web application vulnerabilities.
- **NFR-02.2:** Strict CSRF protection on all mutating HTTP methods (POST, PUT, DELETE).
- **NFR-02.3:** Strict XSS prevention: Django auto-escaping enabled; any allowed Markdown or rich HTML sanitized with `bleach` or `nh3`.
- **NFR-02.4:** Secure password hashing utilizing PBKDF2 with SHA256 or Argon2.
- **NFR-02.5:** Rate limiting on high-frequency endpoints (Login, Search, Contact, Review submissions).
- **NFR-02.6:** Uploaded user media (e.g., listing photos, claim verification documents) strictly validated for file size, MIME type, and sanitized filenames, stored outside the web root.

### 3.3 Usability, Accessibility & Responsiveness (NFR-03)
- **NFR-03.1:** 100% responsive design across viewport widths from 320px (compact mobile) to 2560px (ultra-wide desktop).
- **NFR-03.2:** Touch-friendly tap targets (minimum 44x44px) on all mobile buttons and navigation links.
- **NFR-03.3:** WCAG 2.1 Level AA conformance: sufficient color contrast ratios (minimum 4.5:1 for standard text, 3:1 for large text), ARIA landmarks, and keyboard navigability.
- **NFR-03.4:** Progressive enhancement: Essential reading and navigation functions must remain operational even if client-side JavaScript is disabled.

### 3.4 Data Verification & Editorial Integrity (NFR-04)
- **NFR-04.1:** Zero tolerance for synthetic hallucination: listings must be backed by verifiable sources or direct claim workflows.
- **NFR-04.2:** Every listing must track a `last_verified_at` date stamp, clearly rendered on the user interface ("Verified on: Oct 2026").
- **NFR-04.3:** User-submitted reviews must go through a spam/profanity filter or moderation queue before appearing publicly.

---

## 4. Traceability Matrix (Feature to Module)

| Feature Code | Description | Django Target App | Target Models |
| :--- | :--- | :--- | :--- |
| **FR-01** | Homepage & Navigation | `core` | `SiteSetting`, `EmergencyHelpline` |
| **FR-02** | Tourist Places Directory | `places` | `PlaceCategory`, `Place`, `PlaceGalleryImage` |
| **FR-03** | Lahore Jobs Directory | `jobs` | `JobCategory`, `Employer`, `JobListing` |
| **FR-04** | Restaurants & Cafes | `restaurants` | `Cuisine`, `Restaurant`, `RestaurantFeature` |
| **FR-05** | Hospitals & Clinics | `hospitals` | `MedicalSpecialty`, `Hospital`, `EmergencyService` |
| **FR-06** | Education Directory | `education` | `EducationType`, `Institution`, `Program` |
| **FR-07** | Local Business Directory | `businesses` | `BusinessCategory`, `Business`, `BusinessClaim` |
| **FR-08** | Transport Guides | `transport` | `TransitMode`, `TransitRoute`, `TransitStation` |
| **FR-09** | Local Events Calendar | `events` | `EventCategory`, `EventVenue`, `Event` |
| **FR-10** | City Updates & Advisories| `updates` | `UpdateCategory`, `CityUpdate` |
| **FR-11** | User Accounts & Profiles| `accounts` | `CustomUser`, `UserProfile`, `UserBookmark` |
| **FR-12** | Admin Management | Built-in + `core` | Django Admin Customizations & Inlines |
| **FR-13** | Global Search | `core` | Cross-model Query Engine / PostgreSQL FTS |
| **FR-14** | SEO & Structured Data | `core` + all apps | Reusable `SEOModel` mixin, Sitemaps |
| **FR-15** | Featured Listings | All directory apps| Abstract `ListingBase.is_featured` |
