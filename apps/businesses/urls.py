from django.urls import path
from . import views

app_name = 'businesses'

urlpatterns = [
    path('', views.business_list, name='list'),
    path('submit/', views.business_submit, name='submit'),
    path('dashboard/', views.owner_dashboard, name='dashboard'),
    path('edit/<slug:slug>/', views.business_edit, name='edit'),
    path('delete/<slug:slug>/', views.business_delete, name='delete'),
    path('report/<slug:slug>/', views.report_listing, name='report'),
    path('claim/<slug:slug>/', views.business_claim, name='claim'),
    path('<slug:slug>/', views.business_detail, name='detail'),
]
