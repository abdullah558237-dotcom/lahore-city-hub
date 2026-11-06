from django.shortcuts import render
from apps.core.views import category_list_view

def job_list(request):
    return category_list_view(request, category_slug='jobs')
