from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.utils import timezone

from apps.places.models import Place
from apps.jobs.models import JobListing
from apps.restaurants.models import Restaurant
from apps.hospitals.models import Hospital
from apps.education.models import Institution
from apps.businesses.models import Business
from apps.events.models import Event
from apps.transport.models import TransitRoute, TransitStation, TransitGuide


class StaticViewSitemap(Sitemap):
    """
    Sitemap for authoritative static and high-level directory index pages.
    Excludes private user accounts, dashboards, submission forms, and administrative URLs.
    """
    priority = 0.9
    changefreq = 'weekly'

    def items(self):
        return [
            'core:home',
            'core:about',
            'core:contact',
            'core:privacy',
            'core:terms',
            'core:pricing',
            'core:search',
            'places:list',
            'restaurants:list',
            'hospitals:list',
            'education:list',
            'jobs:list',
            'businesses:list',
            'events:list',
            'transport:overview',
            'transport:route_list',
            'transport:station_list',
            'transport:guide_list',
        ]

    def location(self, item):
        return reverse(item)

    def priority(self, item):
        if item == 'core:home':
            return 1.0
        if item in ['core:about', 'core:contact']:
            return 0.7
        if item in ['core:privacy', 'core:terms']:
            return 0.3
        return 0.8

    def changefreq(self, item):
        if item in ['core:home', 'core:search', 'jobs:list', 'events:list']:
            return 'daily'
        if item in ['core:privacy', 'core:terms']:
            return 'yearly'
        return 'weekly'


class PlaceSitemap(Sitemap):
    """Sitemap for published cultural, heritage, and tourist places in Lahore."""
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        return Place.objects.filter(is_active=True).order_by('-created_at')

    def lastmod(self, obj):
        return obj.updated_at


class JobListingSitemap(Sitemap):
    """
    Sitemap for published and currently active (unexpired) job openings.
    Expired jobs are explicitly excluded to prevent indexing of closed vacancies.
    """
    changefreq = 'daily'
    priority = 0.8

    def items(self):
        today = timezone.now().date()
        return JobListing.objects.filter(is_active=True, deadline__gte=today).order_by('-created_at')

    def lastmod(self, obj):
        return obj.updated_at


class RestaurantSitemap(Sitemap):
    """Sitemap for published dining establishments and food street restaurants."""
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        return Restaurant.objects.filter(is_active=True).order_by('-created_at')

    def lastmod(self, obj):
        return obj.updated_at


class HospitalSitemap(Sitemap):
    """Sitemap for verified public and private hospitals and 24/7 emergency centers."""
    changefreq = 'weekly'
    priority = 0.9

    def items(self):
        return Hospital.objects.filter(is_active=True).order_by('-created_at')

    def lastmod(self, obj):
        return obj.updated_at


class InstitutionSitemap(Sitemap):
    """Sitemap for verified colleges, higher education institutes, and universities."""
    changefreq = 'monthly'
    priority = 0.8

    def items(self):
        return Institution.objects.filter(is_active=True).order_by('-created_at')

    def lastmod(self, obj):
        return obj.updated_at


class BusinessSitemap(Sitemap):
    """Sitemap for verified commercial enterprises and service providers."""
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        return Business.objects.filter(is_active=True).order_by('-created_at')

    def lastmod(self, obj):
        return obj.updated_at


class EventSitemap(Sitemap):
    """Sitemap for verified civic, literary, and cultural events."""
    changefreq = 'daily'
    priority = 0.8

    def items(self):
        return Event.objects.filter(is_active=True).order_by('-created_at')

    def lastmod(self, obj):
        return obj.updated_at


class TransitRouteSitemap(Sitemap):
    """Sitemap for Metrobus, Orange Line, and public transit route guides."""
    changefreq = 'monthly'
    priority = 0.8

    def items(self):
        return TransitRoute.objects.filter(is_active=True).order_by('route_code')

    def lastmod(self, obj):
        return obj.updated_at


class TransitStationSitemap(Sitemap):
    """Sitemap for all major transit stations across Lahore."""
    changefreq = 'monthly'
    priority = 0.7

    def items(self):
        return TransitStation.objects.all().order_by('route', 'station_number')

    def lastmod(self, obj):
        return obj.updated_at


class TransitGuideSitemap(Sitemap):
    """Sitemap for commuter ticketing, rules, and transit guides."""
    changefreq = 'monthly'
    priority = 0.7

    def items(self):
        return TransitGuide.objects.filter(is_published=True).order_by('-created_at')

    def lastmod(self, obj):
        return obj.updated_at


SITEMAPS = {
    'static': StaticViewSitemap,
    'places': PlaceSitemap,
    'jobs': JobListingSitemap,
    'restaurants': RestaurantSitemap,
    'hospitals': HospitalSitemap,
    'education': InstitutionSitemap,
    'businesses': BusinessSitemap,
    'events': EventSitemap,
    'transit_routes': TransitRouteSitemap,
    'transit_stations': TransitStationSitemap,
    'transit_guides': TransitGuideSitemap,
}
