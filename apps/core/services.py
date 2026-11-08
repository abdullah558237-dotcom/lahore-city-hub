from django.core.cache import cache
from apps.core.models import Locality
from apps.places.models import Place
from apps.jobs.models import JobListing
from apps.restaurants.models import Restaurant
from apps.hospitals.models import Hospital
from apps.education.models import Institution
from apps.businesses.models import Business
from apps.events.models import Event
from apps.updates.models import CityUpdate

LOCALITIES_CACHE_KEY = 'lch_all_localities_with_zone'
LOCALITIES_CACHE_TIMEOUT = 600  # 10 minutes

HOMEPAGE_COUNTS_CACHE_KEY = 'lch_homepage_counts_stats'
HOMEPAGE_COUNTS_CACHE_TIMEOUT = 300  # 5 minutes


def get_cached_localities():
    """
    Returns all localities ordered by zone and name.
    Cached for 10 minutes to eliminate repeated SQL queries across all directory sidebars.
    """
    localities = cache.get(LOCALITIES_CACHE_KEY)
    if localities is None:
        localities = list(Locality.objects.all().select_related('zone').order_by('zone__name', 'name'))
        cache.set(LOCALITIES_CACHE_KEY, localities, LOCALITIES_CACHE_TIMEOUT)
    return localities


def get_cached_homepage_counts(today, now):
    """
    Returns active listing counts for the 8 primary domains displayed on the homepage.
    Cached for 5 minutes in memory to eliminate 8 individual COUNT(*) queries per page hit.
    """
    counts = cache.get(HOMEPAGE_COUNTS_CACHE_KEY)
    if counts is None:
        counts = {
            'places': Place.objects.filter(is_active=True).count(),
            'jobs': JobListing.objects.filter(is_active=True, deadline__gte=today).count(),
            'restaurants': Restaurant.objects.filter(is_active=True).count(),
            'hospitals': Hospital.objects.filter(is_active=True).count(),
            'education': Institution.objects.filter(is_active=True).count(),
            'businesses': Business.objects.filter(is_active=True).count(),
            'events': Event.objects.filter(is_active=True, end_datetime__gte=now).count(),
            'updates': CityUpdate.objects.filter(is_active=True).count(),
        }
        cache.set(HOMEPAGE_COUNTS_CACHE_KEY, counts, HOMEPAGE_COUNTS_CACHE_TIMEOUT)
    return counts
