# Lahore City Hub (LCH)
> **Tagline:** Your Complete Guide to Lahore  
> **Platform Classification:** Comprehensive Civic, Tourism, Commercial, and Information Portal  
> **Framework:** Django 5.2 LTS / Python 3.12+  
> **Frontend:** Bootstrap 5.3 + Vanilla JavaScript + Semantic HTML5 Templates

---

## 1. Project Overview

**Lahore City Hub** is the definitive digital portal for Lahore, Pakistan. It provides residents, tourists, students, and businesses with verified, fast, and structured information across 10 core civic and commercial domains:

- **Tourist Places & Heritage:** Badshahi Mosque, Lahore Fort, Shalimar Gardens, Shahi Hammam.
- **Dining & Food Streets:** Authentic Lahori Karahi, MM Alam cafes, rooftop havelis.
- **Hospitals & Healthcare:** 24/7 trauma emergency centers, ambulance helplines, blood banks.
- **Education Directory:** HEC-accredited universities, colleges, and admission timelines.
- **Lahore Jobs:** Localized careers across Gulberg, DHA, Arfa Software Technology Park.
- **Local Businesses:** Artisanal crafts, solar services, legal advisory, and business claim verification.
- **Transport Guides:** Orange Line Metro Train (OLMT), Green Line Metrobus, Speedo feeder buses.
- **Local Events:** Cultural biennales, Lahore Literary Festival (LLF), technology expos.
- **City Updates:** Real-time civic notifications, air quality & smog advisories, traffic diversions.
- **Accounts & Bookmarks:** User accounts, bookmark collections, and verified community reviews.

---

## 2. Quickstart & Installation

### Prerequisites
- Python 3.11 or Python 3.12+
- Git

### Step-by-Step Setup

1. **Clone or Navigate to the Project Directory:**
   ```bash
   cd C:\Users\DELL\.gemini\antigravity\scratch\lahore_city_hub
   ```

2. **Create and Activate a Virtual Environment:**
   ```bash
   # Windows (PowerShell)
   python -m venv venv
   .\venv\Scripts\Activate.ps1

   # Windows (CMD)
   venv\Scripts\activate.bat
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables Configuration:**
   Copy `.env.example` to `.env`:
   ```bash
   copy .env.example .env
   ```

5. **Run Database Migrations:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create an Administrative Superuser:**
   ```bash
   python manage.py createsuperuser
   ```

7. **Start the Development Server:**
   ```bash
   python manage.py runserver
   ```
   Open your browser at: **`http://127.0.0.1:8000/`**

---

## 3. Running in PyCharm

1. Open **PyCharm**.
2. Select **File -> Open...** and browse to:
   ```text
   C:\Users\DELL\.gemini\antigravity\scratch\lahore_city_hub
   ```
3. Set your Python interpreter to the virtual environment (`venv`).
4. PyCharm will detect `requirements.txt` and prompt to install packages.
5. In the built-in PyCharm **Terminal** (`Alt + F12`), run:
   ```bash
   python manage.py check
   python manage.py runserver
   ```

---

## 4. Project Directory Structure

```
lahore_city_hub/
├── config/                  # Central configuration
│   ├── settings/
│   │   ├── base.py          # Shared decoupled settings, apps, logging
│   │   ├── local.py         # Development overrides (SQLite, console email)
│   │   └── production.py    # Production settings (PostgreSQL, WhiteNoise, SSL)
│   ├── urls.py              # Global router with all 12 app namespaces
│   ├── wsgi.py              # WSGI entrypoint
│   └── asgi.py              # ASGI entrypoint
├── apps/                    # Modular domain applications
│   ├── core/                # Base mixins, spatial models, homepage, search, error views
│   ├── accounts/            # CustomUser (email auth), UserProfile, UserBookmark
│   ├── places/              # Tourist places & Mughal heritage
│   ├── restaurants/         # Food streets, cafes, dining guides
│   ├── hospitals/           # Healthcare & 24/7 trauma centers
│   ├── education/           # Universities & colleges
│   ├── jobs/                # Lahore jobs directory
│   ├── businesses/          # Local commercial directory & claiming
│   ├── transport/           # Orange Line Metro & Metrobus guides
│   ├── events/              # Cultural festivals & expo calendar
│   ├── updates/             # Real-time civic notices & smog alerts
│   └── reviews/             # Generic polymorphic reviews engine
├── templates/               # Component-driven HTML5 templates
├── static/                  # Design system CSS tokens, Vanilla JS, Brand SVGs
├── requirements.txt         # Pinned Python dependencies
├── .env.example             # Clean environment variables template
└── .gitignore               # Git exclusions for Python/Django
```

---

## 5. Verification Commands

Run system checks and automated tests:
```bash
python manage.py check
python manage.py test apps.core
```
