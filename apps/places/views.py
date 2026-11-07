from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, F, Count
from django.contrib.contenttypes.models import ContentType

from apps.core.models import Locality
from apps.reviews.models import Review
from .models import Place, PlaceCategory


def place_list(request):
    """
    Faceted, searchable, and paginated directory list view for Lahore tourist places.
    Supports filtering by category, area / locality, keyword search, and verification.
    """
    places_qs = Place.objects.filter(is_active=True).select_related(
        'locality', 'locality__zone', 'category', 'nearest_metro_station'
    )

    # 1. Filter: Category
    selected_category_slug = request.GET.get('category', '').strip()
    selected_category = None
    if selected_category_slug:
        places_qs = places_qs.filter(category__slug=selected_category_slug)
        selected_category = PlaceCategory.objects.filter(slug=selected_category_slug).first()

    # 2. Filter: Area / Locality / Zone
    selected_area_slug = (request.GET.get('area') or request.GET.get('locality') or '').strip()
    selected_locality = None
    if selected_area_slug:
        places_qs = places_qs.filter(
            Q(locality__slug=selected_area_slug) | Q(locality__zone__slug=selected_area_slug)
        )
        selected_locality = Locality.objects.filter(slug=selected_area_slug).first()

    # 3. Filter: Keyword Search (title, Urdu, summary, description, address, era, landmark)
    search_query = request.GET.get('q', '').strip()
    if search_query:
        places_qs = places_qs.filter(
            Q(title__icontains=search_query) |
            Q(title_ur__icontains=search_query) |
            Q(summary__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(address__icontains=search_query) |
            Q(architectural_era__icontains=search_query) |
            Q(landmark__icontains=search_query)
        )

    # 4. Filter: Verified Only
    verified_only = request.GET.get('verified_only') == '1'
    if verified_only:
        places_qs = places_qs.filter(verification_status__in=['verified', 'claimed'])

    # 5. Filter: Wheelchair Accessibility
    wheelchair_only = request.GET.get('wheelchair') == '1'
    if wheelchair_only:
        places_qs = places_qs.filter(wheelchair_accessible=True)

    # 6. Filter: Free Entry
    free_entry = request.GET.get('free_entry') == '1'
    if free_entry:
        places_qs = places_qs.filter(entry_fee_pkr=0)

    # 7. Sorting & Ordering
    sort_by = request.GET.get('sort', 'recommended')
    if sort_by == 'title':
        places_qs = places_qs.order_by('title')
    elif sort_by == 'newest':
        places_qs = places_qs.order_by('-created_at')
    elif sort_by == 'views':
        places_qs = places_qs.order_by('-view_count')
    else:  # recommended
        places_qs = places_qs.order_by('-is_featured', 'title')

    total_results = places_qs.count()

    # 8. Pagination (9 places per page)
    paginator = Paginator(places_qs, 9)
    page_number = request.GET.get('page', 1)
    try:
        page_obj = paginator.get_page(page_number)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.get_page(1)

    # 9. Sidebar Taxonomy Data
    categories = PlaceCategory.objects.filter(is_active=True).annotate(
        active_places_count=Count('places', filter=Q(places__is_active=True))
    )
    localities = Locality.objects.all().select_related('zone').order_by('zone__name', 'name')

    # 10. Featured Spotlight (for top callout banner)
    featured_places = Place.objects.filter(is_active=True, is_featured=True).select_related(
        'locality', 'category'
    )[:3]

    # Query string builder for pagination links without losing filters
    query_params = request.GET.copy()
    if 'page' in query_params:
        query_params.pop('page')
    extra_query_string = f"&{query_params.urlencode()}" if query_params else ""

    # SEO metadata
    if selected_category:
        page_title = f"{selected_category.name} in Lahore | Tourist Places Guide"
        meta_desc = f"Discover verified {selected_category.name.lower()} in Lahore, Pakistan. Check entry fees, visitor timings, architectural eras, and directions."
    elif selected_locality:
        page_title = f"Tourist Places in {selected_locality.name}, Lahore | Heritage Guide"
        meta_desc = f"Explore historical landmarks, shrines, and monuments located in {selected_locality.name}, Lahore, Pakistan."
    elif search_query:
        page_title = f"Search Results for '{search_query}' – Places in Lahore"
        meta_desc = f"Search results for '{search_query}' in Lahore City Hub tourist places directory."
    else:
        page_title = "Tourist Places & Historical Heritage in Lahore | Lahore City Hub"
        meta_desc = "Discover verified historical places, Mughal monuments, UNESCO citadels, historic gardens, and cultural landmarks across Lahore, Pakistan."

    context = {
        'page_title': page_title,
        'meta_description': meta_desc,
        'canonical_url': request.build_absolute_uri(request.path),
        'page_obj': page_obj,
        'places': page_obj.object_list,
        'total_results': total_results,
        'categories': categories,
        'localities': localities,
        'featured_places': featured_places,
        'selected_category': selected_category_slug,
        'selected_category_obj': selected_category,
        'selected_area': selected_area_slug,
        'selected_locality_obj': selected_locality,
        'search_query': search_query,
        'verified_only': verified_only,
        'wheelchair_only': wheelchair_only,
        'free_entry': free_entry,
        'sort_by': sort_by,
        'extra_query_string': extra_query_string,
    }
    return render(request, 'places/place_list.html', context)


def place_detail(request, slug):
    """
    Detailed destination guide for an individual tourist place in Lahore.
    Includes verified visitor logistics, timings, fee structures, photo gallery,
    directions, transit access, visitor reviews, and nearby related recommendations.
    """
    place = get_object_or_404(
        Place.objects.select_related(
            'locality', 'locality__zone', 'category', 'nearest_metro_station', 'nearest_metro_station__route'
        ).prefetch_related('gallery_images'),
        slug=slug,
        is_active=True
    )

    # Increment view count
    Place.objects.filter(pk=place.pk).update(view_count=F('view_count') + 1)

    # Related recommendations (same category or same locality, excluding self)
    related_places = (
        Place.objects.filter(is_active=True)
        .filter(Q(category=place.category) | Q(locality=place.locality))
        .exclude(pk=place.pk)
        .select_related('locality', 'category')
        .distinct()[:3]
    )

    # Approved Visitor Reviews
    place_ct = ContentType.objects.get_for_model(Place)
    reviews = Review.objects.filter(
        content_type=place_ct,
        object_id=place.pk,
        moderation_status=Review.STATUS_APPROVED
    ).select_related('user').order_by('-created_at')

    # SEO metadata
    meta_title = place.meta_title or f"{place.title} – Timings, History & Visitor Guide | Lahore"
    meta_desc = place.meta_description or place.summary
    canonical_url = request.build_absolute_uri(place.get_absolute_url())

    context = {
        'place': place,
        'item': place,  # For backward-compatibility with component partials
        'related_places': related_places,
        'reviews': reviews,
        'page_title': meta_title,
        'meta_description': meta_desc,
        'canonical_url': canonical_url,
    }
    return render(request, 'places/place_detail.html', context)
