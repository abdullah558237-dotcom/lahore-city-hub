from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('about/', views.about_view, name='about'),
    path('contact/', views.contact_view, name='contact'),
    path('privacy/', views.privacy_view, name='privacy'),
    path('terms/', views.terms_view, name='terms'),
    path('pricing/', views.pricing_view, name='pricing'),
    
    # Directory & Category Listing
    path('directory/', views.category_list_view, name='directory_index'),
    path('directory/<slug:category_slug>/', views.category_list_view, name='category_list'),
    
    # Listing Detail View
    path('listing/<slug:slug>/', views.listing_detail_view, name='listing_detail'),
    
    # Search
    path('search/', views.search_results_view, name='search'),
    
    # Accounts & User Workflows
    path('accounts/login/', views.login_view, name='login'),
    path('accounts/register/', views.register_view, name='register'),
    path('member/dashboard/', views.dashboard_view, name='dashboard'),
    
    # Business Submissions
    path('businesses/submit/', views.business_submission_view, name='business_submission'),
    
    # Preview route for 404 test
    path('404-preview/', views.custom_404_view, name='preview_404'),
]
