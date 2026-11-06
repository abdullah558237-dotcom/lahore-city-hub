from django.urls import path
from . import views

app_name = 'hospitals'

urlpatterns = [
    path('', views.hospital_list, name='list'),
    path('<slug:slug>/', views.hospital_detail, name='detail'),
]
