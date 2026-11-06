# Search Engine Optimization (SEO) & Structured Data Strategy
> **Project:** Lahore City Hub (LCH)  
> **Framework:** Django 5.2 SEO Architecture (`django.contrib.sitemaps`, Schema.org JSON-LD)  
> **Document Version:** 1.0.0  
> **Status:** Final Architectural Specification

---

## 1. Governance & Regulatory SEO Disclaimer

> [!IMPORTANT]  
> **Ethical SEO Compliance:** Search Engine Optimization in Lahore City Hub is engineered around semantic accuracy, crawl efficiency, machine readability, and structural best practices. **No guarantees or promises of specific Google search ranks, keyword positions, or traffic volumes are made.** Search engine algorithms rank content based on organic user utility, freshness, relevance, and editorial authority.

---

## 2. Information Architecture & Canonical URL Taxonomy

Every URL in Lahore City Hub follows deterministic, human-readable, lowercase RESTful patterns with trailing slashes enforced (`APPEND_SLASH = True`).

```
https://lahorecityhub.pk/
├── /                                            # Root Homepage
├── /places/                                     # Tourist Places Index
│   ├── /places/<place-slug>/                    # Detail View (e.g., /places/badshahi-mosque/)
│   └── /places/category/<category-slug>/        # Category Filter (e.g., /places/category/mughal-heritage/)
├── /restaurants/                                # Dining Index
│   ├── /restaurants/<restaurant-slug>/          # Restaurant Detail View
│   └── /restaurants/cuisine/<cuisine-slug>/     # Cuisine Filter (e.g., /restaurants/cuisine/traditional-desi/)
├── /hospitals/                                  # Healthcare Index
│   ├── /hospitals/<hospital-slug>/              # Hospital Detail View
│   └── /hospitals/specialty/<specialty-slug>/   # Specialty Filter (e.g., /hospitals/specialty/pediatrics/)
├── /education/                                  # Education Index
│   ├── /education/<institution-slug>/           # Institution Detail
│   └── /education/type/<type-slug>/             # Tier Filter (e.g., /education/type/universities/)
├── /jobs/                                       # Lahore Jobs Index
│   ├── /jobs/<job-slug>/                        # Job Detail View
│   └── /jobs/category/<category-slug>/          # Job Category Filter
├── /businesses/                                 # Commercial Business Index
│   └── /businesses/<business-slug>/             # Business Profile View
├── /transport/                                  # Public Transit Hub
│   ├── /transport/orange-line-metro/            # Dedicated Route Guide
│   └── /transport/metrobus/                     # Dedicated Route Guide
├── /events/                                     # Local Events Calendar
│   └── /events/<event-slug>/                    # Event Detail View
├── /updates/                                    # City Updates & Smog Advisories
│   └── /updates/<update-slug>/                  # Advisory Detail
├── /localities/                                 # Locality Hub Index
│   └── /localities/<locality-slug>/             # Neighborhood Hub (e.g., /localities/gulberg/)
└── /sitemap.xml                                 # Master Sitemap Index
```

### Canonical Tag Rules:
To avoid duplicate indexing penalties from query parameters (e.g., sorting, page numbers, search filters), every interior page outputs an explicit canonical `<link>`:
```html
<link rel="canonical" href="https://lahorecityhub.pk{{ request.path }}">
```

---

## 3. Metadata Generation Framework

### 3.1 Title Tag Formula (`<title>`)
- **Homepage:** `Lahore City Hub | Your Complete Guide to Lahore` (53 chars)
- **Directory List Pages:** `{Category / Domain Name} in Lahore | Lahore City Hub`
- **Directory Detail Pages:** `{Entity Title} – {Locality}, Lahore | Lahore City Hub` (e.g., `Badshahi Mosque – Walled City, Lahore | Lahore City Hub`)
- **Locality Hubs:** `Guide to {Locality}, Lahore: Places, Dining & Services | Lahore City Hub`

### 3.2 Dynamic Meta Description Formula (`<meta name="description">`)
- Constrained between 130 and 158 characters.
- Must incorporate the locality, category, and core value proposition.
- *Detail View Pattern:*  
  `"Explore {Entity Title} in {Locality}, Lahore. Verified timings, contact details, ticket pricing, and visitor guidelines. Last checked {Month Year}."`

---

## 4. Structured Data (Schema.org JSON-LD) Specifications

Server-rendered JSON-LD scripts are embedded in the `<head>` of detail views to provide unambiguous semantic entities to search engines:

### 4.1 Tourist Attraction (`TouristAttraction` / `Place`)
```json
{
  "@context": "https://schema.org",
  "@type": "TouristAttraction",
  "name": "Badshahi Mosque",
  "description": "Historic 17th-century Mughal congregational mosque in the Walled City of Lahore.",
  "image": "https://lahorecityhub.pk/media/places/banners/badshahi-mosque.jpg",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "Walled City, Near Fort Road Food Street",
    "addressLocality": "Lahore",
    "addressRegion": "Punjab",
    "addressCountry": "PK"
  },
  "geo": {
    "@type": "GeoCoordinates",
    "latitude": 31.5881,
    "longitude": 74.3097
  },
  "telephone": "+92-42-99214444",
  "isAccessibleForFree": false,
  "publicAccess": true
}
```

### 4.2 Restaurant (`Restaurant`)
```json
{
  "@context": "https://schema.org",
  "@type": "Restaurant",
  "name": "Haveli Restaurant",
  "image": "https://lahorecityhub.pk/media/restaurants/banners/haveli.jpg",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "Fort Road Food Street",
    "addressLocality": "Lahore",
    "addressCountry": "PK"
  },
  "servesCuisine": ["Traditional Lahori", "Barbecue", "Desi"],
  "priceRange": "$$$",
  "telephone": "+92-300-8414899",
  "acceptsReservations": "True"
}
```

### 4.3 Hospital (`Hospital`)
```json
{
  "@context": "https://schema.org",
  "@type": "Hospital",
  "name": "Doctors Hospital & Medical Center",
  "image": "https://lahorecityhub.pk/media/hospitals/banners/doctors-hospital.jpg",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "152-G/1, Canal Bank, Johar Town",
    "addressLocality": "Lahore",
    "addressCountry": "PK"
  },
  "telephone": "+92-42-35302701",
  "emergencyTelephone": "+92-42-111-362-867",
  "availableService": [
    { "@type": "MedicalSpecialty", "name": "Emergency Care" },
    { "@type": "MedicalSpecialty", "name": "Cardiology" }
  ]
}
```

### 4.4 Job Posting (`JobPosting`)
```json
{
  "@context": "https://schema.org",
  "@type": "JobPosting",
  "title": "Senior Python/Django Engineer",
  "description": "We are seeking a senior Django engineer based in Lahore...",
  "datePosted": "2026-11-01",
  "validThrough": "2026-11-30",
  "employmentType": "FULL_TIME",
  "hiringOrganization": {
    "@type": "Organization",
    "name": "Arfa Software Technology Park Co.",
    "sameAs": "https://example.com"
  },
  "jobLocation": {
    "@type": "Place",
    "address": {
      "@type": "PostalAddress",
      "addressLocality": "Gulberg III, Lahore",
      "addressRegion": "Punjab",
      "addressCountry": "PK"
    }
  },
  "baseSalary": {
    "@type": "MonetaryAmount",
    "currency": "PKR",
    "value": {
      "@type": "QuantitativeValue",
      "minValue": 250000,
      "maxValue": 400000,
      "unitText": "MONTH"
    }
  }
}
```

### 4.5 BreadcrumbList (Universal)
```json
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {
      "@type": "ListItem",
      "position": 1,
      "name": "Home",
      "item": "https://lahorecityhub.pk/"
    },
    {
      "@type": "ListItem",
      "position": 2,
      "name": "Places",
      "item": "https://lahorecityhub.pk/places/"
    },
    {
      "@type": "ListItem",
      "position": 3,
      "name": "Badshahi Mosque",
      "item": "https://lahorecityhub.pk/places/badshahi-mosque/"
    }
  ]
}
```

---

## 5. XML Sitemap Architecture

Using `django.contrib.sitemaps`, the project generates a **Master Sitemap Index** partitioning URLs into domain-specific sitemaps:

```python
# apps/core/sitemaps.py structure
sitemaps = {
    'static': StaticViewSitemap,
    'localities': LocalitySitemap,
    'places': PlaceSitemap,
    'restaurants': RestaurantSitemap,
    'hospitals': HospitalSitemap,
    'education': InstitutionSitemap,
    'jobs': JobSitemap,
    'businesses': BusinessSitemap,
    'events': EventSitemap,
    'updates': CityUpdateSitemap,
}
```

### Sitemap Logic & Invalidation:
- Expired jobs (`deadline < today`) and inactive listings are excluded automatically.
- `lastmod` maps directly to the entity's `updated_at` timestamp.
- Frequency and priority:
  - Homepage / City Updates: `changefreq="hourly"`, `priority=1.0`
  - Directory Lists / Events: `changefreq="daily"`, `priority=0.8`
  - Detail Pages: `changefreq="weekly"`, `priority=0.7`

---

## 6. Robots.txt Configuration

```txt
# robots.txt for Lahore City Hub
User-agent: *
Disallow: /admin/
Disallow: /accounts/
Disallow: /api/
Disallow: /search/
Disallow: /*?*           # Block infinite faceted query permutations from indexation

# Allow CSS & JS for full Googlebot rendering
Allow: /static/
Allow: /media/

# Master Sitemap Index
Sitemap: https://lahorecityhub.pk/sitemap.xml
```

---

## 7. Hyper-Local Internal Linking & Locality Hubs

To build domain authority without spamming backlinks, Lahore City Hub implements **Locality Hubs**:
- An interior page for each major locality (e.g., `/localities/gulberg/`, `/localities/dha/`, `/localities/walled-city/`).
- The hub automatically aggregates all verified places, cafes, clinics, metro stations, and businesses located within that geographical sector.
- Detail pages cross-link naturally: a page for a restaurant in Gulberg links back to the Gulberg Hub, the nearest Metro station, and nearby cultural sites.
