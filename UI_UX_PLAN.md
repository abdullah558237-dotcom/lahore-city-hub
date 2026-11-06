# UI/UX Design System & Layout Specifications
> **Project:** Lahore City Hub (LCH)  
> **Aesthetic Theme:** "Mughal Heritage Meets Modern Smart City"  
> **Frontend Stack:** Bootstrap 5.3 + Vanilla JS + HTML5 Semantic Templates  
> **Document Version:** 1.0.0  
> **Status:** Final Architectural Specification

---

## 1. Design System & Visual Identity

### 1.1 Color Palette
The color system honors Lahore's rich architectural history (the red sandstone of Badshahi Mosque, Shalimar Garden greenery, and historical brickwork) while maintaining crisp modern contrast ratios exceeding WCAG 2.1 AA standards.

| Token Name | Hex Code | Usage Rationale | Sample UI Context |
| :--- | :--- | :--- | :--- |
| **`--lch-primary-green`** | `#0B4632` | Royal Mughal Green; evokes Shalimar Gardens and Punjab civic pride. | Primary header, primary buttons, brand accents. |
| **`--lch-accent-terracotta`** | `#C0392B` | Badshahi Mosque & Lahore Fort red sandstone brick. | Call-to-action buttons, emergency indicators, urgent badges. |
| **`--lch-ochre-gold`** | `#D4A373` | Historical glazed kashi tilework of Wazir Khan Mosque. | Star ratings, "Featured" badges, secondary highlights. |
| **`--lch-dark-slate`** | `#1C2833` | Deep high-contrast charcoal slate. | Primary typography, dark footers, icon accents. |
| **`--lch-canvas-bg`** | `#F8F9FA` | Soft off-white neutral canvas. | Global page background, directory card backgrounds. |
| **`--lch-border-subtle`** | `#E5E7EB` | Clean hairline divider. | Card borders, table dividers, form input outlines. |

### 1.2 Typography
- **Primary Interface Font:** `Plus Jakarta Sans` or `Inter` (sans-serif)  
  *Characteristics:* High x-height, exceptional legibility on low-resolution mobile displays, clean numerical rendering for phone numbers and ticket prices.
- **Urdu Transliteration / Native Font:** `Noto Nastaliq Urdu` / `Noto Sans Arabic`  
  *Characteristics:* Seamless rendering of Urdu titles (`بادشاہی مسجد`, `گلبرگ`, `شالامار باغ`) without horizontal clipping.

### 1.3 Iconography
- **Library:** `Bootstrap Icons 1.11+`  
  *Implementation:* Embedded inline SVGs or sprite fonts for zero layout shift (CLS), negligible network payload, and crisp rendering on high-DPI retina screens.

---

## 2. Responsive Breakpoints & Mobile-First Strategy

In Pakistan, over 78% of web traffic originates from mobile devices running Android on mobile cellular connections. The interface is engineered **mobile-first**:

- **Mobile (< 768px):**  
  - Full-width stacked category cards.
  - Sticky search bar with auto-collapsing header.
  - Directory filter sidebar transforms into a slide-over **Offcanvas Drawer** triggered by a floating action button ("Filters & Localities").
  - Large touch targets (minimum 48x48px tap areas) for phone numbers and directions.
- **Tablet (768px – 991px):**  
  - Two-column directory grid.
  - Collapsible horizontal filter ribbon.
- **Desktop (992px – 1400px+):**  
  - Two-pane directory layout: 300px fixed faceted filter sidebar + 3-column responsive card grid.
  - Expanded mega-menu for rapid category exploration.

---

## 3. Core Page Wireframes & Layout Specifications

### 3.1 Homepage Layout Flow
```
+-------------------------------------------------------------------------+
| [TOP RIBBON] 1122 Rescue | Police 15 | Edhi 115 | Traffic 1915 | WASA   |
+-------------------------------------------------------------------------+
| [NAVBAR]  Lahore City Hub Logo    [Explore v] [Localities v]  [Login]   |
+-------------------------------------------------------------------------+
| [HERO BANNER with Lahore Skyline Silhouette]                            |
|    "Your Complete Guide to Lahore"                                      |
|    [  Search places, jobs, food, hospitals...  ] [ Locality v ] [Search]|
|    Popular: Badshahi Mosque | DHA Cafes | Tech Jobs | 24/7 Hospitals    |
+-------------------------------------------------------------------------+
| [EMERGENCY & CIVIC ADVISORIES TICKER]                                   |
|    "Smog Alert: Moderate AQI recorded today in Gulberg & Mall Road"     |
+-------------------------------------------------------------------------+
| [EXPLORE LAHORE - 10 Core Directory Cards]                              |
| [Places] [Food] [Hospitals] [Education] [Jobs] [Businesses] [Transport] |
+-------------------------------------------------------------------------+
| [FEATURED VERIFIED SPOTS IN LAHORE] (Carousel / Grid)                   |
|  [ Card 1: Haveli Restaurant ] [ Card 2: Doctors Hospital ] [ Card 3 ]  |
+-------------------------------------------------------------------------+
| [THIS WEEK IN LAHORE - Upcoming Events]                                 |
|  [ Event 1: LLF at Alhamra ]   [ Event 2: Tech Expo at Expo Centre ]    |
+-------------------------------------------------------------------------+
| [LATEST CITY NOTICES & TRAFFIC UPDATES]                                 |
|  - CTP Lahore Traffic Diversion on Canal Road                           |
|  - Orange Line Metro extended weekend operating schedule                |
+-------------------------------------------------------------------------+
| [FOOTER] Civic Links | Directory Sitemap | Verification Policy | Copr.  |
+-------------------------------------------------------------------------+
```

### 3.2 Directory List View Layout (e.g., `/places/`, `/restaurants/`, `/hospitals/`)
```
+-------------------------------------------------------------------------+
| Breadcrumbs: Home > Directory > Restaurants & Cafes                     |
+-------------------------------------------------------------------------+
| Header: "Restaurants & Cafes in Lahore" (Showing 142 Verified Listings) |
+-----------------------+-------------------------------------------------+
| FILTERS (Sidebar)     | SORT & VIEW BAR: [Sort: Rating v] [Grid | List] |
|                       +-------------------------------------------------+
| Locality:             | [ CARD 1 ]  [Verified Badge] [★ 4.8 (84)]       |
| [x] Gulberg           | Title: Butt Karahi - Lakshmi Chowk              |
| [ ] DHA               | Cuisine: Traditional Lahori | Price: $$         |
| [ ] Johar Town        | Locality: Walled City / Lakshmi Chowk           |
|                       | Last Verified: Oct 2026 | Source: Direct Visit  |
| Cuisine / Type:       | [View Details] [Call: +92-42-373...] [Bookmark] |
| [x] Traditional Desi  +-------------------------------------------------+
| [ ] Continental       | [ CARD 2 ]                                      |
|                       | Title: Monal Lahore (Rooftop)                   |
| Price Range:          | Amenities: Rooftop, Family Hall, Valet          |
| [$] [$$] [$$$] [$$$$] | Locality: Liberty Roundabout, Gulberg III       |
|                       +-------------------------------------------------+
| Verification:         | [ CARD 3 ] ...                                  |
| [x] Verified Only     +-------------------------------------------------+
|                       | [PAGINATION:  < Prev   1   2   3   4 ...  Next > ]  |
+-----------------------+-------------------------------------------------+
```

### 3.3 Directory Detail View Layout
```
+-------------------------------------------------------------------------+
| Breadcrumbs: Home > Places > Walled City > Badshahi Mosque              |
+-------------------------------------------------------------------------+
| [HERO IMAGE BANNER / GALLERY PREVIEW]                                   |
| High-resolution photography with photo attribution ("Photo: WCLA")      |
+-------------------------------------------------------------------------+
| [KEY METRICS & VERIFICATION STRIP]                                      |
| [✓ Verified Listing] | Last Verified: Oct 2026 | Source: WCLA Official  |
| [★ 4.9 (420 Reviews)] | [Bookmark] | [Share] | [Claim Listing]         |
+---------------------------------------+---------------------------------+
| MAIN CONTENT COLUMN (65% Width)       | SIDEBAR / ACTION BAR (35% Width)|
|                                       |                                 |
| Overview & Architecture               | Quick Facts Card:               |
| Built in 1673 by Emperor Aurangzeb... | - Entry Fee: PKR 50 / USD 5     |
|                                       | - Timings: 08:00 AM - 08:00 PM  |
| Architectural Highlights & Details    | - Closed: During Friday Prayers |
| Capacity: 100,000 worshippers...      | - Photography: Allowed (Phones) |
|                                       |                                 |
| Visitor Guidelines                    | Location & Directions:          |
| - Modest dress code enforced          | Address: Walled City, Lahore    |
| - Shoe custody service at gateway     | Nearest Transit:                |
|                                       | [Azadi Chowk Metrobus Station]  |
| Interactive Photo Gallery (6 photos)  | [Open in Google Maps]           |
|                                       |                                 |
| Public Community Reviews (★ 4.9)      | Contact Information:            |
| [Submit a Review Button]              | Phone: +92-42-99214444          |
| Review 1: "Magnificent heritage site" | Official Site: wcla.punjab.gov  |
+---------------------------------------+---------------------------------+
```

---

## 4. Usability & Accessibility (WCAG 2.1 AA Checklist)

1. **Color Contrast:** All text tokens against canvas backgrounds maintain at least a `4.8:1` contrast ratio.
2. **Keyboard Navigability:** Visible `:focus-visible` outline rings (in `--lch-primary-green`) on all interactive buttons, inputs, and links.
3. **Screen Reader Optimization:** ARIA landmarks (`<header role="banner">`, `<main id="main-content">`, `<nav aria-label="Breadcrumb">`).
4. **Skip Links:** A hidden "Skip to main content" link at the very top of `base.html` for keyboard and screen reader accessibility.
5. **No Flashing Content:** Fully compliant with photosensitive seizure prevention; animations respect `prefers-reduced-motion: reduce`.

---

## 5. Micro-Interactions & Progressive Enhancement

- **Optimistic Bookmark Toggle:** Clicking the bookmark heart icon updates the icon immediately in the UI via `fetch()` and reverts with an alert only if the network request fails.
- **Dynamic Search Autocomplete:** Lightweight debounce (250ms) querying `/api/search-suggest/?q=` without locking the browser thread.
- **Dial-to-Call & WhatsApp Direct Launch:** On mobile, telephone and WhatsApp buttons use proper URI schemes (`tel:+92...` and `https://wa.me/92...`) for instantaneous native app launch.
