from django.contrib import admin
from .models import EventCategory, EventVenue, Event

@admin.register(EventCategory)
class EventCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(EventVenue)
class EventVenueAdmin(admin.ModelAdmin):
    list_display = ('name', 'locality', 'capacity')
    search_fields = ('name', 'address')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'venue', 'start_datetime', 'ticket_policy', 'is_featured')
    list_filter = ('category', 'ticket_policy', 'is_featured', 'start_datetime')
    search_fields = ('title', 'description', 'organizer_name')
    prepopulated_fields = {'slug': ('title',)}
