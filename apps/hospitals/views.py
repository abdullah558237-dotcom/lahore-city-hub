from django.shortcuts import render
from apps.core.views import category_list_view, listing_detail_view

def hospital_list(request):
    return category_list_view(request, category_slug='hospitals')

def hospital_detail(request, slug):
    return listing_detail_view(request, slug=slug)
