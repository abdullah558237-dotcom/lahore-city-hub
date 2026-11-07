import datetime
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Count
from django.utils import timezone
from django.http import Http404

from .models import EventCategory, EventVenue, Event


def event_list(request):
    """
    Searchable, filterable, and paginated directory view for Lahore civic and cultural events.
    Supports date filtering (upcoming, today, this weekend, this week, past archive),
    category filtering, ticketing policy filtering, and keyword search.
    """
    now = timezone.now()
    local_today = timezone.localdate()

    events_qs = Event.objects.filter(is_active=True).select_related(
        'category', 'venue', 'venue__locality'
    )

    # 1. Date Filter (Timezone-Aware)
    date_filter = request.GET.get('date', 'upcoming').strip()
    if date_filter == 'today':
        today_start = timezone.make_aware(datetime.datetime.combine(local_today, datetime.time.min))
        today_end = timezone.make_aware(datetime.datetime.combine(local_today, datetime.time.max))
        events_qs = events_qs.filter(
            start_datetime__lte=today_end,
            end_datetime__gte=today_start
        ).order_by('start_datetime')
    elif date_filter == 'this_weekend':
        # Saturday and Sunday of this weekend
        if local_today.weekday() == 6:  # Sunday
            saturday = local_today - datetime.timedelta(days=1)
            sunday = local_today
        else:
            days_to_sat = (5 - local_today.weekday()) % 7
            saturday = local_today + datetime.timedelta(days=days_to_sat)
            sunday = saturday + datetime.timedelta(days=1)
        sat_start = timezone.make_aware(datetime.datetime.combine(saturday, datetime.time.min))
        sun_end = timezone.make_aware(datetime.datetime.combine(sunday, datetime.time.max))
        events_qs = events_qs.filter(
            start_datetime__lte=sun_end,
            end_datetime__gte=sat_start
        ).order_by('start_datetime')
    elif date_filter == 'this_week':
        end_of_week = timezone.make_aware(datetime.datetime.combine(local_today + datetime.timedelta(days=7), datetime.time.max))
        events_qs = events_qs.filter(
            start_datetime__lte=end_of_week,
            end_datetime__gte=now
        ).order_by('start_datetime')
    elif date_filter == 'this_month':
        # From start of current month to end of current month
        start_of_month = timezone.make_aware(datetime.datetime(local_today.year, local_today.month, 1, 0, 0, 0))
        # Compute first of next month
        if local_today.month == 12:
            next_month = timezone.make_aware(datetime.datetime(local_today.year + 1, 1, 1, 0, 0, 0))
        else:
            next_month = timezone.make_aware(datetime.datetime(local_today.year, local_today.month + 1, 1, 0, 0, 0))
        events_qs = events_qs.filter(
            start_datetime__lt=next_month,
            end_datetime__gte=now
        ).order_by('start_datetime')
    elif date_filter == 'past':
        events_qs = events_qs.filter(end_datetime__lt=now).order_by('-start_datetime')
    elif date_filter == 'all':
        events_qs = events_qs.order_by('start_datetime')
    else:  # 'upcoming' is default
        date_filter = 'upcoming'
        events_qs = events_qs.filter(end_datetime__gte=now).order_by('start_datetime')

    # 2. Category Filter
    selected_category_slug = request.GET.get('category', '').strip()
    selected_category = None
    if selected_category_slug:
        events_qs = events_qs.filter(category__slug=selected_category_slug)
        selected_category = EventCategory.objects.filter(slug=selected_category_slug).first()

    # 3. Ticket Policy Filter
    selected_ticket = request.GET.get('ticket', '').strip()
    if selected_ticket:
        events_qs = events_qs.filter(ticket_policy=selected_ticket)

    # 4. Keyword Search
    search_query = request.GET.get('q', '').strip()
    if search_query:
        events_qs = events_qs.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(venue__name__icontains=search_query) |
            Q(venue__address__icontains=search_query) |
            Q(organizer_name__icontains=search_query) |
            Q(category__name__icontains=search_query)
        )

    events_qs = events_qs.distinct()
    total_results = events_qs.count()

    # 5. Pagination (9 events per page)
    paginator = Paginator(events_qs, 9)
    page_number = request.GET.get('page', 1)
    try:
        page_obj = paginator.get_page(page_number)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.get_page(1)

    # 6. Sidebar Taxonomies & Facet Counts
    categories = EventCategory.objects.filter(is_active=True).annotate(
        upcoming_count=Count(
            'events',
            filter=Q(events__is_active=True, events__end_datetime__gte=now)
        )
    )

    # 7. Featured Upcoming Events Spotlight
    featured_events = Event.objects.filter(
        is_active=True,
        is_featured=True,
        end_datetime__gte=now
    ).select_related('category', 'venue')[:3]

    # Query string builder for pagination
    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']
    pagination_querystring = query_params.urlencode()

    page_title = "Upcoming Events & Festivals in Lahore | Cultural Calendar"
    meta_description = "Discover verified literary festivals, art exhibitions, food weekends, and conferences across Lahore venues."
    if selected_category:
        page_title = f"{selected_category.name} in Lahore | Events Calendar"
    elif date_filter == 'past':
        page_title = "Past & Concluded Events in Lahore | Event Archive"
        meta_description = "Archive of past cultural, literary, and commercial exhibitions in Lahore."

    context = {
        'page_title': f"{page_title} | Lahore City Hub",
        'meta_description': meta_description,
        'canonical_url': request.build_absolute_uri(request.path),
        'events': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'total_results': total_results,
        'categories': categories,
        'selected_category': selected_category,
        'selected_category_slug': selected_category_slug,
        'selected_ticket': selected_ticket,
        'date_filter': date_filter,
        'search_query': search_query,
        'featured_events': featured_events,
        'pagination_querystring': pagination_querystring,
    }
    return render(request, 'events/event_list.html', context)


def event_detail(request, slug):
    """
    Detailed profile view for a cultural or civic event in Lahore.
    Includes Schema.org/Event structured data, expired event handling,
    ticket links, venue information, and verified source provenance.
    """
    event = get_object_or_404(
        Event.objects.select_related('category', 'venue', 'venue__locality'),
        slug=slug
    )

    # Publication permission check: if inactive and not staff, 404
    if not event.is_active and not request.user.is_staff:
        raise Http404("This event is currently unpublished or inactive.")

    now = timezone.now()
    is_expired = event.is_expired
    is_ongoing = event.is_ongoing

    related_events = Event.objects.filter(
        category=event.category,
        is_active=True,
        end_datetime__gte=now
    ).exclude(pk=event.pk)[:3]

    page_title = f"{event.title} | Events in Lahore"
    meta_description = event.summary or f"{event.title} taking place at {event.venue.name}, Lahore."

    context = {
        'page_title': f"{page_title} | Lahore City Hub",
        'meta_description': meta_description,
        'canonical_url': request.build_absolute_uri(event.get_absolute_url()),
        'event': event,
        'is_expired': is_expired,
        'is_ongoing': is_ongoing,
        'related_events': related_events,
    }
    return render(request, 'events/event_detail.html', context)
