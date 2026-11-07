from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, F, Count
from django.contrib.contenttypes.models import ContentType

from apps.core.models import Locality
from apps.reviews.models import Review
from .models import Restaurant, Cuisine, RestaurantFeature


def restaurant_list(request):
    """
    Faceted, searchable, and paginated directory view for Lahore restaurants and cafes.
    Supports filtering by cuisine, locality/zone, price tier, dining features,
    verification status, and keyword search.
    """
    restaurants_qs = Restaurant.objects.filter(is_active=True).select_related(
        'locality', 'locality__zone'
    ).prefetch_related('cuisines', 'features')

    # 1. Filter: Cuisine
    selected_cuisine_slug = request.GET.get('cuisine', '').strip()
    selected_cuisine = None
    if selected_cuisine_slug:
        restaurants_qs = restaurants_qs.filter(cuisines__slug=selected_cuisine_slug)
        selected_cuisine = Cuisine.objects.filter(slug=selected_cuisine_slug).first()

    # 2. Filter: Area / Locality / Zone
    selected_area_slug = (request.GET.get('area') or request.GET.get('locality') or '').strip()
    selected_locality = None
    if selected_area_slug:
        restaurants_qs = restaurants_qs.filter(
            Q(locality__slug=selected_area_slug) | Q(locality__zone__slug=selected_area_slug)
        )
        selected_locality = Locality.objects.filter(slug=selected_area_slug).first()

    # 3. Filter: Price Category / Tier
    selected_price = request.GET.get('price', '').strip()
    if selected_price:
        restaurants_qs = restaurants_qs.filter(price_tier=selected_price)

    # 4. Filter: Keyword Search
    search_query = request.GET.get('q', '').strip()
    if search_query:
        restaurants_qs = restaurants_qs.filter(
            Q(title__icontains=search_query) |
            Q(title_ur__icontains=search_query) |
            Q(summary__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(address__icontains=search_query) |
            Q(landmark__icontains=search_query) |
            Q(cuisines__name__icontains=search_query)
        )

    # 5. Filter: Dining Amenities
    family_hall_only = request.GET.get('family_hall') == '1'
    if family_hall_only:
        restaurants_qs = restaurants_qs.filter(has_family_hall=True)

    takeaway_only = request.GET.get('takeaway') == '1'
    if takeaway_only:
        restaurants_qs = restaurants_qs.filter(provides_takeaway=True)

    delivery_only = request.GET.get('delivery') == '1'
    if delivery_only:
        restaurants_qs = restaurants_qs.filter(provides_delivery=True)

    # 6. Filter: Verified Only
    verified_only = request.GET.get('verified_only') == '1'
    if verified_only:
        restaurants_qs = restaurants_qs.filter(verification_status__in=['verified', 'claimed'])

    # Distinct query set when joining ManyToMany fields
    restaurants_qs = restaurants_qs.distinct()

    # 7. Sorting
    sort_by = request.GET.get('sort', 'recommended').strip()
    if sort_by == 'title':
        restaurants_qs = restaurants_qs.order_by('title')
    elif sort_by == 'newest':
        restaurants_qs = restaurants_qs.order_by('-created_at')
    elif sort_by == 'views':
        restaurants_qs = restaurants_qs.order_by('-view_count')
    elif sort_by == 'price_asc':
        restaurants_qs = restaurants_qs.order_by('price_tier', '-is_featured', 'title')
    elif sort_by == 'price_desc':
        restaurants_qs = restaurants_qs.order_by('-price_tier', '-is_featured', 'title')
    else:  # recommended
        restaurants_qs = restaurants_qs.order_by('-is_featured', 'title')

    total_results = restaurants_qs.count()

    # 8. Pagination (9 restaurants per page)
    paginator = Paginator(restaurants_qs, 9)
    page_number = request.GET.get('page', 1)
    try:
        page_obj = paginator.get_page(page_number)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.get_page(1)

    # 9. Sidebar Taxonomies & Facet Counts
    cuisines = Cuisine.objects.filter(is_active=True).annotate(
        active_restaurants_count=Count('restaurants', filter=Q(restaurants__is_active=True))
    )
    localities = Locality.objects.all().select_related('zone').order_by('zone__name', 'name')
    features = RestaurantFeature.objects.all()

    # 10. Featured Spotlight (Top 3)
    featured_restaurants = Restaurant.objects.filter(
        is_active=True, is_featured=True
    ).select_related('locality').prefetch_related('cuisines')[:3]

    # Query string builder for pagination links
    query_params = request.GET.copy()
    if 'page' in query_params:
        query_params.pop('page')
    extra_query_string = f"&{query_params.urlencode()}" if query_params else ""

    # Dynamic SEO Metadata
    if selected_cuisine:
        page_title = f"{selected_cuisine.name} Restaurants in Lahore | Dining Guide"
        meta_desc = f"Discover the best {selected_cuisine.name.lower()} restaurants in Lahore, Pakistan. Check verified opening hours, menu prices, contact numbers, and reviews."
    elif selected_locality:
        page_title = f"Restaurants in {selected_locality.name}, Lahore | Food & Dining"
        meta_desc = f"Explore popular restaurants, family halls, and cafes in {selected_locality.name}, Lahore. Verified addresses, menus, and ratings."
    elif selected_price:
        price_labels = {'$': 'Budget & Street Food', '$$': 'Casual Dining', '$$$': 'Upscale Dining', '$$$$': 'Fine Dining & Luxury'}
        label = price_labels.get(selected_price, selected_price)
        page_title = f"{label} Restaurants in Lahore | Food Directory"
        meta_desc = f"Find top-rated {label.lower()} options in Lahore, Pakistan with confirmed menus and locations."
    elif search_query:
        page_title = f"Search Results for '{search_query}' – Lahore Restaurants"
        meta_desc = f"Search results for '{search_query}' in Lahore City Hub food and dining directory."
    else:
        page_title = "Restaurants & Dining in Lahore | Lahore Food Guide"
        meta_desc = "Discover authentic Lahore food: traditional karahi, barbecue, desi breakfast, continental cafes, and fine dining across Gulberg, DHA, and the Walled City."

    context = {
        'page_title': page_title,
        'meta_description': meta_desc,
        'canonical_url': request.build_absolute_uri(request.path),
        'page_obj': page_obj,
        'restaurants': page_obj.object_list,
        'total_results': total_results,
        'cuisines': cuisines,
        'localities': localities,
        'features': features,
        'price_choices': Restaurant.PRICE_CHOICES,
        'featured_restaurants': featured_restaurants,
        'selected_cuisine': selected_cuisine_slug,
        'selected_cuisine_obj': selected_cuisine,
        'selected_area': selected_area_slug,
        'selected_locality_obj': selected_locality,
        'selected_price': selected_price,
        'family_hall_only': family_hall_only,
        'takeaway_only': takeaway_only,
        'delivery_only': delivery_only,
        'verified_only': verified_only,
        'sort_by': sort_by,
        'search_query': search_query,
        'extra_query_string': extra_query_string,
    }
    return render(request, 'restaurants/restaurant_list.html', context)


def restaurant_detail(request, slug):
    """
    Detailed dining guide for an individual restaurant in Lahore.
    Includes verified operational timings, menu highlights, price category,
    family hall details, delivery options, photo gallery, and visitor reviews.
    """
    restaurant = get_object_or_404(
        Restaurant.objects.select_related(
            'locality', 'locality__zone'
        ).prefetch_related('cuisines', 'features', 'menu_highlights', 'gallery_images'),
        slug=slug,
        is_active=True
    )

    # Increment view count
    Restaurant.objects.filter(pk=restaurant.pk).update(view_count=F('view_count') + 1)

    # Related restaurants: active restaurants in same locality OR sharing any cuisine (excluding self)
    cuisine_ids = restaurant.cuisines.values_list('id', flat=True)
    related_restaurants = (
        Restaurant.objects.filter(is_active=True)
        .filter(Q(locality=restaurant.locality) | Q(cuisines__in=cuisine_ids))
        .exclude(pk=restaurant.pk)
        .select_related('locality')
        .prefetch_related('cuisines')
        .distinct()[:3]
    )

    # Approved Visitor Reviews
    restaurant_ct = ContentType.objects.get_for_model(Restaurant)
    reviews = Review.objects.filter(
        content_type=restaurant_ct,
        object_id=restaurant.pk,
        moderation_status=Review.STATUS_APPROVED
    ).select_related('user').order_by('-created_at')

    # SEO metadata
    meta_title = restaurant.meta_title or f"{restaurant.title} – Menu, Timings & Reviews | Lahore"
    meta_desc = restaurant.meta_description or restaurant.summary
    canonical_url = request.build_absolute_uri(restaurant.get_absolute_url())

    context = {
        'restaurant': restaurant,
        'item': restaurant,  # For backward-compatibility with component partials
        'related_restaurants': related_restaurants,
        'reviews': reviews,
        'page_title': meta_title,
        'meta_description': meta_desc,
        'canonical_url': canonical_url,
    }
    return render(request, 'restaurants/restaurant_detail.html', context)
