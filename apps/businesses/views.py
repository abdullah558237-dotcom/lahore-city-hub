from django.shortcuts import render
from apps.core.views import category_list_view, business_submission_view

def business_list(request):
    return category_list_view(request, category_slug='businesses')

business_submit = business_submission_view
