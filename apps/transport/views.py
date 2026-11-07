from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Count
from django.http import Http404

from .models import TransitMode, TransitRoute, TransitStation, TransitGuide


def transit_overview(request):
    """
    Public transit overview hub for Lahore.
    Surfaces the Orange Line Metro Train, Green Line Metrobus, Speedo Feeder buses,
    key interchange stations, operating hours, and essential commuter travel advice.
    """
    modes = TransitMode.objects.filter(is_active=True).annotate(
        active_routes_count=Count('routes', filter=Q(routes__is_active=True))
    )

    routes = TransitRoute.objects.filter(is_active=True).select_related('mode').prefetch_related('stations')

    interchanges = TransitStation.objects.filter(
        is_interchange=True,
        route__is_active=True
    ).select_related('route', 'locality').order_by('route', 'station_number')

    featured_guides = TransitGuide.objects.filter(
        is_published=True
    ).select_related('route').order_by('display_order', '-is_featured')[:4]

    search_query = request.GET.get('q', '').strip()
    search_results = None
    if search_query:
        search_results = {
            'routes': TransitRoute.objects.filter(
                Q(route_name__icontains=search_query) |
                Q(route_code__icontains=search_query) |
                Q(origin_station__icontains=search_query) |
                Q(destination_station__icontains=search_query),
                is_active=True
            ),
            'stations': TransitStation.objects.filter(
                Q(station_name__icontains=search_query) |
                Q(urdu_name__icontains=search_query) |
                Q(nearby_landmarks__icontains=search_query) |
                Q(interchange_details__icontains=search_query),
                route__is_active=True
            ).select_related('route')[:10]
        }

    context = {
        'page_title': 'Lahore Public Transit, Metrobus & Orange Line Guide | Lahore City Hub',
        'meta_description': 'Complete guide to Lahore rapid transit: Orange Line Metro Train (OLMT), Green Line Metrobus, Speedo feeder routes, station timetables, and smart card fares.',
        'canonical_url': request.build_absolute_uri(request.path),
        'modes': modes,
        'routes': routes,
        'interchanges': interchanges,
        'featured_guides': featured_guides,
        'search_query': search_query,
        'search_results': search_results,
    }
    return render(request, 'transport/overview.html', context)


def route_list(request):
    """
    Searchable and filterable listing of all active transit lines and corridors in Lahore.
    Supports mode filtering, keyword search, and pagination.
    """
    routes_qs = TransitRoute.objects.filter(is_active=True).select_related('mode')

    # 1. Filter: Mode
    selected_mode_slug = request.GET.get('mode', '').strip()
    selected_mode = None
    if selected_mode_slug:
        routes_qs = routes_qs.filter(mode__slug=selected_mode_slug)
        selected_mode = TransitMode.objects.filter(slug=selected_mode_slug).first()

    # 2. Filter: Search
    search_query = request.GET.get('q', '').strip()
    if search_query:
        routes_qs = routes_qs.filter(
            Q(route_name__icontains=search_query) |
            Q(route_code__icontains=search_query) |
            Q(origin_station__icontains=search_query) |
            Q(destination_station__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(operator__icontains=search_query)
        )

    routes_qs = routes_qs.distinct()

    # 3. Sorting
    sort_by = request.GET.get('sort', 'code').strip()
    if sort_by == 'stations':
        routes_qs = routes_qs.order_by('-total_stations')
    elif sort_by == 'distance':
        routes_qs = routes_qs.order_by('-total_distance_km')
    elif sort_by == 'name':
        routes_qs = routes_qs.order_by('route_name')
    else:  # code / default
        routes_qs = routes_qs.order_by('-is_featured', 'route_code')

    total_results = routes_qs.count()

    # 4. Pagination
    paginator = Paginator(routes_qs, 9)
    page_number = request.GET.get('page', 1)
    try:
        page_obj = paginator.get_page(page_number)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.get_page(1)

    modes = TransitMode.objects.filter(is_active=True).annotate(
        active_routes_count=Count('routes', filter=Q(routes__is_active=True))
    )

    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']
    pagination_querystring = query_params.urlencode()

    context = {
        'page_title': 'Lahore Public Transit Routes & Lines | Transit Hub',
        'meta_description': 'Explore all public transit routes in Lahore, including the Orange Line Metro Train, Green Line Metrobus, and feeder bus networks.',
        'canonical_url': request.build_absolute_uri(request.path),
        'routes': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'total_results': total_results,
        'modes': modes,
        'selected_mode': selected_mode,
        'selected_mode_slug': selected_mode_slug,
        'search_query': search_query,
        'sort_by': sort_by,
        'pagination_querystring': pagination_querystring,
    }
    return render(request, 'transport/route_list.html', context)


def route_detail(request, slug):
    """
    Detailed route guide showing sequence of stations, total distance,
    fares, operating hours, interchanges, and route-specific travel advice.
    """
    route = get_object_or_404(
        TransitRoute.objects.select_related('mode'),
        slug=slug
    )

    # Permission check: if inactive and not staff, 404
    if not route.is_active and not request.user.is_staff:
        raise Http404("This transit route is currently inactive or undergoing maintenance.")

    stations = route.stations.all().select_related('locality').order_by('station_number')
    guides = route.guides.filter(is_published=True).order_by('display_order')

    interchanges_count = stations.filter(is_interchange=True).count()

    context = {
        'page_title': f"{route.route_name} - Route Guide & Stations | Lahore City Hub",
        'meta_description': f"Official route guide for {route.route_name} ({route.route_code}). {route.total_stations} stations connecting {route.origin_station} to {route.destination_station}.",
        'canonical_url': request.build_absolute_uri(route.get_absolute_url()),
        'route': route,
        'stations': stations,
        'guides': guides,
        'interchanges_count': interchanges_count,
    }
    return render(request, 'transport/route_detail.html', context)


def station_list(request):
    """
    Searchable station directory across all Lahore transit routes.
    Supports filtering by route, interchange status, and underground status.
    """
    stations_qs = TransitStation.objects.filter(
        route__is_active=True
    ).select_related('route', 'route__mode', 'locality')

    # 1. Filter: Route
    selected_route_slug = request.GET.get('route', '').strip()
    selected_route = None
    if selected_route_slug:
        stations_qs = stations_qs.filter(route__slug=selected_route_slug)
        selected_route = TransitRoute.objects.filter(slug=selected_route_slug).first()

    # 2. Filter: Interchange Only
    interchange_only = request.GET.get('interchange') == '1'
    if interchange_only:
        stations_qs = stations_qs.filter(is_interchange=True)

    # 3. Filter: Underground Only
    underground_only = request.GET.get('underground') == '1'
    if underground_only:
        stations_qs = stations_qs.filter(is_underground=True)

    # 4. Search Query
    search_query = request.GET.get('q', '').strip()
    if search_query:
        stations_qs = stations_qs.filter(
            Q(station_name__icontains=search_query) |
            Q(urdu_name__icontains=search_query) |
            Q(nearby_landmarks__icontains=search_query) |
            Q(interchange_details__icontains=search_query) |
            Q(route__route_name__icontains=search_query) |
            Q(route__route_code__icontains=search_query)
        )

    stations_qs = stations_qs.order_by('route', 'station_number')
    total_results = stations_qs.count()

    # Pagination (15 stations per page)
    paginator = Paginator(stations_qs, 15)
    page_number = request.GET.get('page', 1)
    try:
        page_obj = paginator.get_page(page_number)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.get_page(1)

    routes = TransitRoute.objects.filter(is_active=True).select_related('mode').order_by('route_code')

    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']
    pagination_querystring = query_params.urlencode()

    context = {
        'page_title': 'Lahore Metro & Transit Stations Directory | Lahore City Hub',
        'meta_description': 'Search and browse all stations across the Orange Line Metro Train, Green Line Metrobus, and feeder routes in Lahore.',
        'canonical_url': request.build_absolute_uri(request.path),
        'stations': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'total_results': total_results,
        'routes': routes,
        'selected_route': selected_route,
        'selected_route_slug': selected_route_slug,
        'interchange_only': interchange_only,
        'underground_only': underground_only,
        'search_query': search_query,
        'pagination_querystring': pagination_querystring,
    }
    return render(request, 'transport/station_list.html', context)


def station_detail(request, slug):
    """
    Detailed profile view for an individual transit station.
    Displays line affiliation, sequence number, next/previous stops,
    accessibility amenities, and transfer directions.
    """
    station = get_object_or_404(
        TransitStation.objects.select_related('route', 'route__mode', 'locality'),
        slug=slug
    )

    if not station.route.is_active and not request.user.is_staff:
        raise Http404("This station belongs to an inactive transit route.")

    # Next and Previous stations along the same route
    prev_station = TransitStation.objects.filter(
        route=station.route,
        station_number=station.station_number - 1
    ).first()

    next_station = TransitStation.objects.filter(
        route=station.route,
        station_number=station.station_number + 1
    ).first()

    # Interchange connections (stations with same or connected name on other routes)
    connected_stations = TransitStation.objects.filter(
        station_name__icontains=station.station_name,
        route__is_active=True
    ).exclude(pk=station.pk).select_related('route')

    context = {
        'page_title': f"{station.station_name} Station (#{station.station_number}) - {station.route.route_code} | Lahore City Hub",
        'meta_description': f"Information for {station.station_name} Station on {station.route.route_name}. Nearby landmarks: {station.nearby_landmarks or 'Lahore'}.",
        'canonical_url': request.build_absolute_uri(station.get_absolute_url()),
        'station': station,
        'prev_station': prev_station,
        'next_station': next_station,
        'connected_stations': connected_stations,
    }
    return render(request, 'transport/station_detail.html', context)


def guide_list(request):
    """
    Public transport guides, passenger rules, ticketing instructions, and commuter advice.
    """
    guides_qs = TransitGuide.objects.filter(is_published=True).select_related('route')

    # 1. Filter: Category
    selected_category = request.GET.get('category', '').strip()
    if selected_category:
        guides_qs = guides_qs.filter(category=selected_category)

    # 2. Filter: Route
    selected_route_slug = request.GET.get('route', '').strip()
    selected_route = None
    if selected_route_slug:
        guides_qs = guides_qs.filter(route__slug=selected_route_slug)
        selected_route = TransitRoute.objects.filter(slug=selected_route_slug).first()

    # 3. Search Query
    search_query = request.GET.get('q', '').strip()
    if search_query:
        guides_qs = guides_qs.filter(
            Q(title__icontains=search_query) |
            Q(summary__icontains=search_query) |
            Q(content__icontains=search_query)
        )

    guides_qs = guides_qs.order_by('display_order', '-is_featured', 'title')
    total_results = guides_qs.count()

    routes = TransitRoute.objects.filter(is_active=True).select_related('mode').order_by('route_code')

    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']
    pagination_querystring = query_params.urlencode()

    context = {
        'page_title': 'Lahore Public Transit Guides & Travel Advice | Lahore City Hub',
        'meta_description': 'Commuter advice, Metro Smart Card ticketing, platform rules, women and senior accessibility guidelines for Lahore transit.',
        'canonical_url': request.build_absolute_uri(request.path),
        'guides': guides_qs,
        'total_results': total_results,
        'category_choices': TransitGuide.CATEGORY_CHOICES,
        'selected_category': selected_category,
        'routes': routes,
        'selected_route': selected_route,
        'selected_route_slug': selected_route_slug,
        'search_query': search_query,
        'pagination_querystring': pagination_querystring,
    }
    return render(request, 'transport/guide_list.html', context)


def guide_detail(request, slug):
    """
    Reading view for a detailed transit guide or travel advice article.
    """
    guide = get_object_or_404(
        TransitGuide.objects.select_related('route', 'route__mode'),
        slug=slug
    )

    if not guide.is_published and not request.user.is_staff:
        raise Http404("This transit guide is unpublished or undergoing revision.")

    related_guides = TransitGuide.objects.filter(
        category=guide.category,
        is_published=True
    ).exclude(pk=guide.pk)[:3]

    context = {
        'page_title': f"{guide.title} | Lahore Transit Guide",
        'meta_description': guide.summary,
        'canonical_url': request.build_absolute_uri(guide.get_absolute_url()),
        'guide': guide,
        'related_guides': related_guides,
    }
    return render(request, 'transport/guide_detail.html', context)
