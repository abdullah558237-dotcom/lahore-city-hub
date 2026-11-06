from django.shortcuts import render, redirect
from django.contrib import messages
from apps.core.views import login_view, register_view, dashboard_view

# Direct references to established account workflows
user_login = login_view
user_register = register_view
user_dashboard = dashboard_view
