from django.shortcuts import render
from apps.core.views import category_list_view, listing_detail_view

def restaurant_list(request):
    return category_list_view(request, category_slug='restaurants')

def restaurant_detail(request, slug):
    return listing_detail_view(request, slug=slug)
