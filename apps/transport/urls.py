from django.urls import path
from . import views

app_name = 'transport'

urlpatterns = [
    path('', views.transit_overview, name='overview'),
    path('routes/', views.route_list, name='route_list'),
    path('routes/<slug:slug>/', views.route_detail, name='route_detail'),
    path('stations/', views.station_list, name='station_list'),
    path('stations/<slug:slug>/', views.station_detail, name='station_detail'),
    path('guides/', views.guide_list, name='guide_list'),
    path('guides/<slug:slug>/', views.guide_detail, name='guide_detail'),
]
