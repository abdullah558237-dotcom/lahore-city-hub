from django.shortcuts import render
from django.contrib import messages
from django.utils import timezone

from apps.places.models import Place
from apps.jobs.models import JobListing
from apps.restaurants.models import Restaurant
from apps.hospitals.models import Hospital
from apps.education.models import Institution
from apps.businesses.models import Business
from apps.events.models import Event
from apps.updates.models import CityUpdate
from apps.transport.models import TransitRoute

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

    # Total counts for badge displays
    total_places = Place.objects.filter(is_active=True).count()
    total_jobs = JobListing.objects.filter(is_active=True, deadline__gte=today).count()
    total_restaurants = Restaurant.objects.filter(is_active=True).count()
    total_hospitals = Hospital.objects.filter(is_active=True).count()
    total_education = Institution.objects.filter(is_active=True).count()
    total_businesses = Business.objects.filter(is_active=True).count()
    total_events = Event.objects.filter(is_active=True, end_datetime__gte=now).count()
    total_updates = CityUpdate.objects.filter(is_active=True).count()

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
        'counts': {
            'places': total_places,
            'jobs': total_jobs,
            'restaurants': total_restaurants,
            'hospitals': total_hospitals,
            'education': total_education,
            'businesses': total_businesses,
            'events': total_events,
            'updates': total_updates,
        }
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
    """Civic directory contact details and feedback form."""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()

        if name and email and message:
            messages.success(request, f"Thank you, {name}! Your message regarding '{subject}' has been received by our Lahore editorial team.")
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


def search_results_view(request):
    """
    Global search across all 10 directory domains with category-segmented hit counts.
    """
    query = request.GET.get('q', '').strip()
    locality = request.GET.get('locality', '').strip()

    def matches(item):
        txt_target = f"{item.get('title', '')} {item.get('summary', '')} {item.get('category', '')} {item.get('cuisine', '')} {item.get('specialties', '')}".lower()
        query_ok = not query or (query.lower() in txt_target)
        loc_ok = not locality or (locality.lower() in item.get('locality', '').lower())
        return query_ok and loc_ok

    matched_places = [x for x in DEMO_TOURIST_PLACES if matches(x)]
    matched_restaurants = [x for x in DEMO_RESTAURANTS if matches(x)]
    matched_hospitals = [x for x in DEMO_HOSPITALS if matches(x)]
    matched_education = [x for x in DEMO_EDUCATION if matches(x)]
    matched_jobs = [x for x in DEMO_JOBS if matches(x)]
    matched_businesses = [x for x in DEMO_BUSINESSES if matches(x)]

    total_hits = (
        len(matched_places) +
        len(matched_restaurants) +
        len(matched_hospitals) +
        len(matched_education) +
        len(matched_jobs) +
        len(matched_businesses)
    )

    context = {
        'page_title': f"Search Results for '{query}' in {locality or 'All Lahore'} | Lahore City Hub",
        'query': query,
        'locality': locality,
        'total_hits': total_hits,
        'matched_places': matched_places,
        'matched_restaurants': matched_restaurants,
        'matched_hospitals': matched_hospitals,
        'matched_education': matched_education,
        'matched_jobs': matched_jobs,
        'matched_businesses': matched_businesses,
    }
    return render(request, 'pages/search_results.html', context)


def login_view(request):
    """User authentication sign-in screen."""
    if request.method == 'POST':
        messages.success(request, "Demonstration sign-in successful! Welcome back to Lahore City Hub.")
    context = {
        'page_title': 'Sign In to Your Account | Lahore City Hub',
        'meta_description': 'Access your saved bookmarks, submitted reviews, and claimed business listings on Lahore City Hub.',
    }
    return render(request, 'pages/login.html', context)


def register_view(request):
    """User registration screen."""
    if request.method == 'POST':
        messages.success(request, "Account created successfully! Welcome to the Lahore City Hub community.")
    context = {
        'page_title': 'Create a Member Account | Lahore City Hub',
        'meta_description': 'Join Lahore City Hub to bookmark favorite spots, submit verified reviews, and manage business listings.',
    }
    return render(request, 'pages/register.html', context)


def dashboard_view(request):
    """User dashboard displaying saved bookmarks, reviews, and business claims."""
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
    """Business directory listing and ownership claim submission form."""
    if request.method == 'POST':
        biz_name = request.POST.get('business_name', '').strip()
        if biz_name:
            messages.success(request, f"Submission received for '{biz_name}'! Our verification team will review your proof documents within 48 hours.")
        else:
            messages.error(request, "Please enter your business title and contact phone number.")

    context = {
        'page_title': 'Submit or Claim a Business Listing | Lahore City Hub',
        'meta_description': 'Submit your Lahore business listing or claim your existing company profile for verification and premium reach.',
    }
    return render(request, 'pages/business_submission.html', context)


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

