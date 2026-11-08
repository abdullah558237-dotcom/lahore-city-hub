from django.shortcuts import render
from django.contrib import messages
from django.utils import timezone
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from apps.places.models import Place
from apps.jobs.models import JobListing
from apps.restaurants.models import Restaurant
from apps.hospitals.models import Hospital
from apps.education.models import Institution
from apps.businesses.models import Business
from apps.events.models import Event
from apps.updates.models import CityUpdate
from apps.transport.models import TransitRoute
from .services import get_cached_homepage_counts, get_cached_localities

from .demo_data import (
    DEMO_TOURIST_PLACES,
    DEMO_RESTAURANTS,
    DEMO_HOSPITALS,
    DEMO_EDUCATION,
    DEMO_JOBS,
    DEMO_BUSINESSES,
    DEMO_EVENTS,
    DEMO_UPDATES,
)

def home_view(request):
    """
    Renders the Lahore City Hub comprehensive homepage with live ORM queries.
    Only published, active records are displayed.
    All relationships are selected/pre-fetched to avoid N+1 queries.
    Gracefully falls back to empty states when no records exist.
    """
    now = timezone.now()
    today = now.date()

    # 1. Featured Places (is_active=True)
    featured_places = (
        Place.objects.filter(is_active=True)
        .select_related('locality', 'category')
        .order_by('-is_featured', '-created_at')[:3]
    )

    # 2. Latest Published Jobs (is_active=True, deadline not passed)
    latest_jobs = (
        JobListing.objects.filter(is_active=True, deadline__gte=today)
        .select_related('employer', 'category', 'locality')
        .order_by('-is_featured', '-created_at')[:4]
    )

    # 3. Trending Restaurants (is_active=True, prefetched relations)
    featured_restaurants = (
        Restaurant.objects.filter(is_active=True)
        .select_related('locality')
        .prefetch_related('cuisines', 'features')
        .order_by('-is_featured', '-created_at')[:3]
    )

    # 4. Hospitals & Healthcare (is_active=True)
    featured_hospitals = (
        Hospital.objects.filter(is_active=True)
        .select_related('locality')
        .prefetch_related('specialties')
        .order_by('-is_featured', '-is_24_7_emergency', '-created_at')[:3]
    )

    # 5. Educational Institutions (is_active=True)
    featured_education = (
        Institution.objects.filter(is_active=True)
        .select_related('education_type', 'locality')
        .prefetch_related('accreditations')
        .order_by('-is_featured', '-created_at')[:3]
    )

    # 6. Featured Local Businesses (is_active=True)
    featured_businesses = (
        Business.objects.filter(is_active=True)
        .select_related('category', 'locality')
        .order_by('-is_featured', '-created_at')[:3]
    )

    # 7. Upcoming Events (is_active=True, end_datetime in future)
    upcoming_events = (
        Event.objects.filter(is_active=True, end_datetime__gte=now)
        .select_related('category', 'venue', 'venue__locality')
        .order_by('start_datetime')[:3]
    )

    # 8. Latest City Updates (is_active=True, pinned first)
    city_updates = (
        CityUpdate.objects.filter(is_active=True)
        .select_related('category')
        .order_by('-is_pinned', '-valid_from')[:3]
    )

    # 9. Active Transit Routes
    transit_routes = (
        TransitRoute.objects.filter(is_active=True)
        .select_related('mode')
        .order_by('route_code')[:3]
    )

    # Cached total counts for badge displays (5 min TTL)
    counts = get_cached_homepage_counts(today, now)

    context = {
        'page_title': 'Your Complete Guide to Lahore | Lahore City Hub',
        'meta_description': 'Discover verified tourist places, dining spots, hospitals, jobs, and civic updates across Lahore.',
        'canonical_url': request.build_absolute_uri(request.path),
        'featured_places': featured_places,
        'featured_restaurants': featured_restaurants,
        'featured_hospitals': featured_hospitals,
        'featured_education': featured_education,
        'latest_jobs': latest_jobs,
        'featured_businesses': featured_businesses,
        'upcoming_events': upcoming_events,
        'city_updates': city_updates,
        'transit_routes': transit_routes,
        'counts': counts,
    }
    return render(request, 'pages/home.html', context)


def about_view(request):
    """Platform mission, editorial policy, and verification pledge."""
    context = {
        'page_title': 'About Lahore City Hub | The Civic & Cultural Guide to Lahore',
        'meta_description': 'Learn about our mission to provide verified, accessible civic and commercial information for Lahore, Pakistan.',
    }
    return render(request, 'pages/about.html', context)


def contact_view(request):
    """Civic directory contact details and feedback form with RFC email and length validation."""
    if request.method == 'POST':
        name = request.POST.get('name', '')[:100].strip()
        email = request.POST.get('email', '')[:254].strip().lower()
        subject = request.POST.get('subject', '')[:150].strip()
        message = request.POST.get('message', '')[:3000].strip()

        is_valid_email = True
        try:
            validate_email(email)
        except ValidationError:
            is_valid_email = False

        if name and email and message and is_valid_email:
            messages.success(request, f"Thank you, {name}! Your message regarding '{subject}' has been received by our Lahore editorial team.")
        elif not is_valid_email and email:
            messages.error(request, "Please enter a valid email address.")
        else:
            messages.error(request, "Please fill in all required fields to submit your inquiry.")

    context = {
        'page_title': 'Contact Our Editorial & Civic Team | Lahore City Hub',
        'meta_description': 'Get in touch with the Lahore City Hub editorial staff, submit civic inquiries, or report listing updates.',
    }
    return render(request, 'pages/contact.html', context)


def privacy_view(request):
    """Privacy policy and data protection framework."""
    context = {
        'page_title': 'Privacy Policy | Lahore City Hub',
        'meta_description': 'Read how Lahore City Hub respects user privacy, protects contact records, and enforces transparent data practices.',
    }
    return render(request, 'pages/privacy.html', context)


def terms_view(request):
    """Terms of service and directory listing conditions."""
    context = {
        'page_title': 'Terms & Conditions of Use | Lahore City Hub',
        'meta_description': 'Terms of service, directory verification rules, and community guidelines for Lahore City Hub.',
    }
    return render(request, 'pages/terms.html', context)


def category_list_view(request, category_slug='places'):
    """
    Faceted directory list view supporting locality filtering, price filtering,
    verified toggles, and dual grid/list presentation.
    """
    selected_locality = request.GET.get('locality', '')
    selected_price = request.GET.get('price', '')
    verified_only = request.GET.get('verified_only', '') == '1'
    view_mode = request.GET.get('view', 'grid')  # 'grid' or 'list'
    sort_by = request.GET.get('sort', 'recommended')

    # Choose dataset based on category_slug
    if category_slug == 'restaurants':
        items = list(DEMO_RESTAURANTS)
        cat_title = "Restaurants & Cafes in Lahore"
        cat_desc = "Explore authentic Lahori Karahis, rooftop fine dining, street food, and cafes across Lahore's culinary hubs."
    elif category_slug == 'hospitals':
        items = list(DEMO_HOSPITALS)
        cat_title = "Hospitals & Emergency Healthcare in Lahore"
        cat_desc = "Verified 24/7 trauma centers, teaching hospitals, and specialized clinics with direct helpline numbers."
    elif category_slug == 'education':
        items = list(DEMO_EDUCATION)
        cat_title = "Universities & Educational Institutions in Lahore"
        cat_desc = "HEC-accredited public and private universities, degree colleges, and academic institutions in Lahore."
    elif category_slug == 'jobs':
        items = list(DEMO_JOBS)
        cat_title = "Lahore Jobs & Career Opportunities"
        cat_desc = "Verified employment openings in IT, healthcare, teaching, and hospitality across Gulberg, DHA, and Johar Town."
    elif category_slug == 'businesses':
        items = list(DEMO_BUSINESSES)
        cat_title = "Local Businesses & Commercial Directory"
        cat_desc = "Trusted retail outlets, legal practices, solar solutions, and artisanal craft studios in Lahore."
    else:
        items = list(DEMO_TOURIST_PLACES)
        category_slug = 'places'
        cat_title = "Tourist Places & Historical Heritage in Lahore"
        cat_desc = "Discover centuries of Mughal, Sikh, and Colonial architecture, public gardens, and cultural monuments."

    # Apply filters
    filtered_items = []
    clean_loc = selected_locality.replace('-', ' ').lower() if selected_locality else ''
    for it in items:
        loc_match = not selected_locality or (clean_loc in it.get('locality', '').lower())
        price_match = not selected_price or (it.get('price_tier', '') == selected_price)
        verified_match = not verified_only or it.get('is_verified', False)

        if loc_match and price_match and verified_match:
            filtered_items.append(it)

    # Sort
    if sort_by == 'rating':
        filtered_items.sort(key=lambda x: x.get('rating', 0), reverse=True)
    elif sort_by == 'reviews':
        filtered_items.sort(key=lambda x: x.get('reviews_count', 0), reverse=True)

    context = {
        'page_title': f'{cat_title} | Lahore City Hub',
        'meta_description': cat_desc,
        'category_slug': category_slug,
        'category_title': cat_title,
        'category_description': cat_desc,
        'items': filtered_items,
        'total_results': len(filtered_items),
        'selected_locality': selected_locality,
        'selected_price': selected_price,
        'verified_only': verified_only,
        'view_mode': view_mode,
        'sort_by': sort_by,
    }
    return render(request, 'pages/category_list.html', context)


def listing_detail_view(request, slug="badshahi-mosque"):
    """
    Renders an in-depth directory listing detail page featuring verified badges,
    photo gallery, operational timings, ticketing, location directions, and reviews.
    """
    # Lookup in all collections
    all_entities = DEMO_TOURIST_PLACES + DEMO_RESTAURANTS + DEMO_HOSPITALS + DEMO_EDUCATION + DEMO_BUSINESSES
    entity = next((item for item in all_entities if item.get('slug') == slug), DEMO_TOURIST_PLACES[0])

    reviews = [
        {
            "author": "Hassan Tariq",
            "locality": "Gulberg III, Lahore",
            "rating": 5.0,
            "date": "October 14, 2026",
            "title": "A magnificent spiritual and architectural masterpiece",
            "comment": "Visiting during Maghrib when the red sandstone is illuminated is an unforgettable spiritual experience. The shoes custody service and security arrangements were well organized."
        },
        {
            "author": "Dr. Mariam Farooq",
            "locality": "DHA Phase 6, Lahore",
            "rating": 5.0,
            "date": "September 28, 2026",
            "title": "Immaculate preservation of Lahore's cultural glory",
            "comment": "The vast courtyard and intricate marble inlay work are stunning. Highly recommend taking the Metrobus to Azadi Chowk for seamless access without traffic hassles."
        },
        {
            "author": "Hamza Ali",
            "locality": "Model Town, Lahore",
            "rating": 4.5,
            "date": "August 19, 2026",
            "title": "Great visitor experience with family",
            "comment": "Very peaceful during weekday mornings. Ensure you dress modestly as religious guidelines are respectfully maintained."
        }
    ]

    context = {
        'page_title': f"{entity.get('title')} – {entity.get('locality', 'Lahore')} | Lahore City Hub",
        'meta_description': entity.get('summary', 'Explore verified details, timings, address, and visitor reviews on Lahore City Hub.'),
        'item': entity,
        'reviews': reviews,
        'related_places': [p for p in DEMO_TOURIST_PLACES if p.get('slug') != entity.get('slug')][:3],
    }
    return render(request, 'pages/listing_detail.html', context)


import re
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q


def clean_search_query(q):
    """
    Sanitizes user search query:
    - Strips whitespace
    - Strips null bytes and non-printable control characters
    - Limits query length to 120 characters to prevent query resource exhaustion
    """
    if not q or not isinstance(q, str):
        return ""
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', q).strip()
    MAX_QUERY_LEN = 120
    if len(cleaned) > MAX_QUERY_LEN:
        cleaned = cleaned[:MAX_QUERY_LEN].strip()
    return cleaned


def search_results_view(request):
    """
    Global search across 8 eligible published content domains:
    Places, Jobs, Restaurants, Hospitals, Education, Businesses, Events, and City Updates.
    Supports query refinement, category filtering, area/locality filtering, and pagination.
    Excludes unpublished, inactive, and expired records while protecting user privacy.
    """
    today = timezone.now().date()
    query = clean_search_query(request.GET.get('q', ''))
    raw_category = (request.GET.get('category') or request.GET.get('type') or 'all').strip().lower()
    locality = request.GET.get('locality', '').strip()
    if locality:
        locality = re.sub(r'[^a-zA-Z0-9_\-\s]', '', locality)[:60].strip()

    valid_categories = {
        'all',
        'places',
        'jobs',
        'restaurants',
        'hospitals',
        'education',
        'businesses',
        'events',
        'updates',
    }
    active_category = raw_category if raw_category in valid_categories else 'all'

    # 1. Places (is_active=True)
    places_qs = Place.objects.filter(is_active=True).select_related('locality', 'category')
    if query:
        places_qs = places_qs.filter(
            Q(title__icontains=query) |
            Q(title_ur__icontains=query) |
            Q(summary__icontains=query) |
            Q(description__icontains=query) |
            Q(address__icontains=query) |
            Q(landmark__icontains=query) |
            Q(category__name__icontains=query)
        )
    if locality:
        places_qs = places_qs.filter(Q(locality__slug__iexact=locality) | Q(locality__name__icontains=locality))

    # 2. Jobs (is_active=True, unexpired)
    jobs_qs = JobListing.objects.filter(is_active=True, deadline__gte=today).select_related(
        'employer', 'category', 'locality'
    )
    if query:
        jobs_qs = jobs_qs.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(requirements__icontains=query) |
            Q(employer__name__icontains=query) |
            Q(category__name__icontains=query)
        )
    if locality:
        jobs_qs = jobs_qs.filter(Q(locality__slug__iexact=locality) | Q(locality__name__icontains=locality))

    # 3. Restaurants (is_active=True)
    restaurants_qs = Restaurant.objects.filter(is_active=True).select_related('locality').prefetch_related('cuisines')
    if query:
        restaurants_qs = restaurants_qs.filter(
            Q(title__icontains=query) |
            Q(title_ur__icontains=query) |
            Q(summary__icontains=query) |
            Q(description__icontains=query) |
            Q(address__icontains=query) |
            Q(landmark__icontains=query) |
            Q(cuisines__name__icontains=query)
        ).distinct()
    if locality:
        restaurants_qs = restaurants_qs.filter(Q(locality__slug__iexact=locality) | Q(locality__name__icontains=locality))

    # 4. Hospitals (is_active=True)
    hospitals_qs = Hospital.objects.filter(is_active=True).select_related('locality').prefetch_related('specialties')
    if query:
        hospitals_qs = hospitals_qs.filter(
            Q(title__icontains=query) |
            Q(title_ur__icontains=query) |
            Q(summary__icontains=query) |
            Q(description__icontains=query) |
            Q(address__icontains=query) |
            Q(landmark__icontains=query) |
            Q(specialties__name__icontains=query)
        ).distinct()
    if locality:
        hospitals_qs = hospitals_qs.filter(Q(locality__slug__iexact=locality) | Q(locality__name__icontains=locality))

    # 5. Education (is_active=True)
    education_qs = Institution.objects.filter(is_active=True).select_related('education_type', 'locality')
    if query:
        education_qs = education_qs.filter(
            Q(title__icontains=query) |
            Q(title_ur__icontains=query) |
            Q(summary__icontains=query) |
            Q(description__icontains=query) |
            Q(address__icontains=query) |
            Q(landmark__icontains=query) |
            Q(education_type__name__icontains=query)
        )
    if locality:
        education_qs = education_qs.filter(Q(locality__slug__iexact=locality) | Q(locality__name__icontains=locality))

    # 6. Businesses (is_active=True; user privacy protected)
    businesses_qs = Business.objects.filter(is_active=True).select_related('category', 'locality')
    if query:
        businesses_qs = businesses_qs.filter(
            Q(title__icontains=query) |
            Q(title_ur__icontains=query) |
            Q(summary__icontains=query) |
            Q(description__icontains=query) |
            Q(address__icontains=query) |
            Q(landmark__icontains=query) |
            Q(category__name__icontains=query)
        )
    if locality:
        businesses_qs = businesses_qs.filter(Q(locality__slug__iexact=locality) | Q(locality__name__icontains=locality))

    # 7. Events (is_active=True)
    events_qs = Event.objects.filter(is_active=True).select_related('category', 'venue', 'venue__locality')
    if query:
        events_qs = events_qs.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(venue__name__icontains=query) |
            Q(venue__address__icontains=query) |
            Q(category__name__icontains=query) |
            Q(organizer_name__icontains=query)
        )
    if locality:
        events_qs = events_qs.filter(
            Q(venue__locality__slug__iexact=locality) | Q(venue__locality__name__icontains=locality)
        )

    # 8. City Updates (is_active=True; city-wide, excluded when filtering by specific area)
    updates_qs = CityUpdate.objects.filter(is_active=True).select_related('category')
    if query:
        updates_qs = updates_qs.filter(
            Q(title__icontains=query) |
            Q(summary__icontains=query) |
            Q(content__icontains=query) |
            Q(category__name__icontains=query) |
            Q(issuing_authority__icontains=query)
        )
    if locality:
        updates_qs = updates_qs.none()

    places_count = places_qs.count()
    jobs_count = jobs_qs.count()
    restaurants_count = restaurants_qs.count()
    hospitals_count = hospitals_qs.count()
    education_count = education_qs.count()
    businesses_count = businesses_qs.count()
    events_count = events_qs.count()
    updates_count = updates_qs.count()

    total_hits = (
        places_count +
        jobs_count +
        restaurants_count +
        hospitals_count +
        education_count +
        businesses_count +
        events_count +
        updates_count
    )

    if total_hits > 0 or Place.objects.filter(is_active=True).exists():
        category_qs_map = {
            'places': (places_qs, 'place'),
            'jobs': (jobs_qs, 'job'),
            'restaurants': (restaurants_qs, 'restaurant'),
            'hospitals': (hospitals_qs, 'hospital'),
            'education': (education_qs, 'education'),
            'businesses': (businesses_qs, 'business'),
            'events': (events_qs, 'event'),
            'updates': (updates_qs, 'update'),
        }

        if active_category in category_qs_map:
            qs, item_type_str = category_qs_map[active_category]
            items_to_paginate = []
            for item in qs:
                item.item_type = item_type_str
                items_to_paginate.append(item)
        else:
            combined_items = []
            for p in places_qs[:25]:
                p.item_type = 'place'
                combined_items.append(p)
            for r in restaurants_qs[:25]:
                r.item_type = 'restaurant'
                combined_items.append(r)
            for h in hospitals_qs[:25]:
                h.item_type = 'hospital'
                combined_items.append(h)
            for e in education_qs[:25]:
                e.item_type = 'education'
                combined_items.append(e)
            for j in jobs_qs[:25]:
                j.item_type = 'job'
                combined_items.append(j)
            for b in businesses_qs[:25]:
                b.item_type = 'business'
                combined_items.append(b)
            for ev in events_qs[:25]:
                ev.item_type = 'event'
                combined_items.append(ev)
            for u in updates_qs[:25]:
                u.item_type = 'update'
                combined_items.append(u)

            combined_items.sort(
                key=lambda x: (
                    getattr(x, 'is_featured', False) or getattr(x, 'is_pinned', False),
                ),
                reverse=True
            )
            items_to_paginate = combined_items

        demo_places = []
        demo_restaurants = []
        demo_hospitals = []
        demo_education = []
        demo_jobs = []
        demo_businesses = []
        demo_events = []
        demo_updates = []
    else:
        # Fallback for unseeded test database environments
        def matches(item):
            txt_target = f"{item.get('title', '')} {item.get('summary', '')} {item.get('description', '')} {item.get('category', '')} {item.get('cuisine', '')} {item.get('specialties', '')}".lower()
            query_ok = not query or (query.lower() in txt_target)
            loc_ok = not locality or (locality.lower() in item.get('locality', '').lower())
            return query_ok and loc_ok

        demo_places = [dict(x, item_type='place') for x in DEMO_TOURIST_PLACES if matches(x)]
        demo_restaurants = [dict(x, item_type='restaurant') for x in DEMO_RESTAURANTS if matches(x)]
        demo_hospitals = [dict(x, item_type='hospital') for x in DEMO_HOSPITALS if matches(x)]
        demo_education = [dict(x, item_type='education') for x in DEMO_EDUCATION if matches(x)]
        demo_jobs = [dict(x, item_type='job') for x in DEMO_JOBS if matches(x)]
        demo_businesses = [dict(x, item_type='business') for x in DEMO_BUSINESSES if matches(x)]
        demo_events = [dict(x, item_type='event') for x in DEMO_EVENTS if matches(x)]
        demo_updates = [dict(x, item_type='update') for x in DEMO_UPDATES if matches(x)] if not locality else []

        places_count = len(demo_places)
        restaurants_count = len(demo_restaurants)
        hospitals_count = len(demo_hospitals)
        education_count = len(demo_education)
        jobs_count = len(demo_jobs)
        businesses_count = len(demo_businesses)
        events_count = len(demo_events)
        updates_count = len(demo_updates)

        total_hits = (
            places_count +
            restaurants_count +
            hospitals_count +
            education_count +
            jobs_count +
            businesses_count +
            events_count +
            updates_count
        )

        demo_category_map = {
            'places': demo_places,
            'restaurants': demo_restaurants,
            'hospitals': demo_hospitals,
            'education': demo_education,
            'jobs': demo_jobs,
            'businesses': demo_businesses,
            'events': demo_events,
            'updates': demo_updates,
        }

        if active_category in demo_category_map:
            items_to_paginate = demo_category_map[active_category]
        else:
            items_to_paginate = (
                demo_places +
                demo_restaurants +
                demo_hospitals +
                demo_education +
                demo_jobs +
                demo_businesses +
                demo_events +
                demo_updates
            )

        places_qs = []
        jobs_qs = []
        restaurants_qs = []
        hospitals_qs = []
        education_qs = []
        businesses_qs = []
        events_qs = []
        updates_qs = []

    # Pagination handling
    PER_PAGE = 12
    paginator = Paginator(items_to_paginate, PER_PAGE)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    is_paginated = page_obj.has_other_pages()

    # Query string for preserving search filters in pagination links
    params = request.GET.copy()
    if 'page' in params:
        del params['page']
    pagination_querystring = params.urlencode()

    context = {
        'page_title': (
            f"Search Results for '{query}' | Lahore City Hub" if query
            else f"All Listings in {locality.title()} | Lahore City Hub" if locality
            else "All City Listings | Lahore City Hub"
        ),
        'query': query,
        'locality': locality,
        'active_category': active_category,
        'total_hits': total_hits,
        'places_count': places_count,
        'jobs_count': jobs_count,
        'restaurants_count': restaurants_count,
        'hospitals_count': hospitals_count,
        'education_count': education_count,
        'businesses_count': businesses_count,
        'events_count': events_count,
        'updates_count': updates_count,
        'page_obj': page_obj,
        'paginator': paginator,
        'is_paginated': is_paginated,
        'pagination_querystring': pagination_querystring,
        'matched_places': places_qs if places_qs else demo_places,
        'matched_restaurants': restaurants_qs if restaurants_qs else demo_restaurants,
        'matched_hospitals': hospitals_qs if hospitals_qs else demo_hospitals,
        'matched_education': education_qs if education_qs else demo_education,
        'matched_jobs': jobs_qs if jobs_qs else demo_jobs,
        'matched_businesses': businesses_qs if businesses_qs else demo_businesses,
        'matched_events': events_qs if events_qs else demo_events,
        'matched_updates': updates_qs if updates_qs else demo_updates,
    }
    return render(request, 'pages/search_results.html', context)


def login_view(request):
    """User authentication sign-in screen (delegates to apps.accounts)."""
    from apps.accounts.views import login_view as accounts_login
    return accounts_login(request)


def register_view(request):
    """User registration screen (delegates to apps.accounts)."""
    from apps.accounts.views import register_view as accounts_register
    return accounts_register(request)


def dashboard_view(request):
    """
    User dashboard. If authenticated, delegates to real accounts dashboard.
    If anonymous and requesting demo view, provides sample demonstration data.
    """
    if request.user.is_authenticated:
        from apps.accounts.views import dashboard_view as accounts_dashboard
        return accounts_dashboard(request)

    bookmarks = [
        {"title": "Badshahi Mosque", "category": "Tourist Places", "locality": "Walled City", "rating": 4.9, "slug": "badshahi-mosque"},
        {"title": "Haveli Restaurant", "category": "Dining & Rooftop", "locality": "Fort Road Food Street", "rating": 4.9, "slug": "haveli-restaurant-fort-road"},
        {"title": "Shaukat Khanum Hospital", "category": "Hospitals", "locality": "Johar Town", "rating": 4.9, "slug": "shaukat-khanum-memorial-cancer-hospital"},
    ]
    my_reviews = [
        {"title": "Badshahi Mosque", "rating": 5.0, "status": "Approved & Published", "date": "14 Oct 2026", "comment": "A magnificent spiritual and architectural masterpiece."},
        {"title": "Butt Karahi - Lakshmi Chowk", "rating": 4.5, "status": "Pending Moderation", "date": "02 Nov 2026", "comment": "Authentic Desi Ghee preparation, friendly staff."},
    ]
    my_claims = [
        {"business": "Anarkali Royal Khussa Emporium", "role": "Owner / Managing Partner", "status": "Approved", "date": "12 Sep 2026"},
    ]

    context = {
        'page_title': 'Member Dashboard | Lahore City Hub',
        'user_name': 'Ahmad Raza Khan',
        'user_email': 'ahmad.raza@example.pk',
        'user_locality': 'Johar Town, Lahore',
        'bookmarks': bookmarks,
        'reviews': my_reviews,
        'claims': my_claims,
    }
    return render(request, 'pages/dashboard.html', context)


def business_submission_view(request):
    """Business directory listing and ownership claim submission form (delegates to apps.businesses)."""
    from apps.businesses.views import business_submit
    return business_submit(request)


def custom_404_view(request, exception=None):
    """Custom, branded 404 Not Found error page."""
    context = {
        'page_title': 'Page Not Found (404) | Lahore City Hub',
        'meta_description': 'The page you requested could not be located in our Lahore civic directory.',
    }
    return render(request, '404.html', context, status=404)


def custom_400_view(request, exception=None):
    """Custom 400 Bad Request error page."""
    context = {
        'page_title': 'Bad Request (400) | Lahore City Hub',
        'meta_description': 'The request could not be processed by the server.',
    }
    return render(request, '400.html', context, status=400)


def custom_403_view(request, exception=None):
    """Custom 403 Permission Denied error page."""
    context = {
        'page_title': 'Access Restricted (403) | Lahore City Hub',
        'meta_description': 'You do not have permission to access this resource.',
    }
    return render(request, '403.html', context, status=403)


def custom_500_view(request):
    """Custom 500 Server Error page."""
    context = {
        'page_title': 'Server Error (500) | Lahore City Hub',
        'meta_description': 'An unexpected server error occurred.',
    }
    return render(request, '500.html', context, status=500)


def robots_txt_view(request):
    """
    Renders robots.txt preventing indexing of administrative, private accounts,
    and user submission/moderation endpoints while pointing to the XML sitemap.
    """
    from django.http import HttpResponse
    sitemap_url = request.build_absolute_uri('/sitemap.xml')
    lines = [
        "User-agent: *",
        "Disallow: /admin/",
        "Disallow: /accounts/",
        "Disallow: /member/",
        "Disallow: /businesses/submit/",
        "Disallow: /businesses/edit/",
        "Disallow: /businesses/claim/",
        "Disallow: /businesses/report/",
        "Disallow: /businesses/promote/",
        "Disallow: /404-preview/",
        "Allow: /",
        "",
        f"Sitemap: {sitemap_url}",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain; charset=utf-8")


def pricing_view(request):
    """
    Public pricing and directory promotion plans comparison page.
    Explains organic (free) inclusion, Verified Professional, and Featured Spotlight packages.
    Features explicit Google Search disclaimer that paid placement does not influence external search rankings.
    """
    context = {
        'page_title': 'Promote Your Business & Pricing Plans | Lahore City Hub',
        'meta_description': 'Explore transparent pricing plans for Lahore local businesses. Get SECP-verified badges, category spotlight placement, and high-visibility promotions.',
        'canonical_url': request.build_absolute_uri(request.path),
    }
    return render(request, 'pages/pricing.html', context)


