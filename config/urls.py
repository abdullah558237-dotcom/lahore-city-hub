from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin Interface
    path('admin/', admin.site.urls),

    # Core Hub & Public Views
    path('', include(('apps.core.urls', 'core'), namespace='core')),

    # Domain Directories & Services (Namespaced)
    path('accounts/', include(('apps.accounts.urls', 'accounts'), namespace='accounts')),
    path('places/', include(('apps.places.urls', 'places'), namespace='places')),
    path('restaurants/', include(('apps.restaurants.urls', 'restaurants'), namespace='restaurants')),
    path('hospitals/', include(('apps.hospitals.urls', 'hospitals'), namespace='hospitals')),
    path('education/', include(('apps.education.urls', 'education'), namespace='education')),
    path('jobs/', include(('apps.jobs.urls', 'jobs'), namespace='jobs')),
    path('businesses/', include(('apps.businesses.urls', 'businesses'), namespace='businesses')),
    path('transport/', include(('apps.transport.urls', 'transport'), namespace='transport')),
    path('events/', include(('apps.events.urls', 'events'), namespace='events')),
    path('updates/', include(('apps.updates.urls', 'updates'), namespace='updates')),
    path('reviews/', include(('apps.reviews.urls', 'reviews'), namespace='reviews')),
]

# Static and Media Serving in Development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Custom Error Handlers
handler400 = 'apps.core.views.custom_400_view'
handler403 = 'apps.core.views.custom_403_view'
handler404 = 'apps.core.views.custom_404_view'
handler500 = 'apps.core.views.custom_500_view'
