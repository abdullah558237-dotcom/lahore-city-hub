from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
try:
    from django.utils.http import url_has_allowed_host_and_scheme
except ImportError:
    from django.utils.http import is_safe_url as url_has_allowed_host_and_scheme
from django.db.models import Q
from django.views.decorators.http import require_http_methods
from django.urls import reverse_lazy

from apps.businesses.models import Business, BusinessEditRequest, BusinessClaim
from .models import UserBookmark
from .forms import UserRegistrationForm, UserLoginForm, UserProfileForm


def register_view(request):
    """
    Public registration view with strict role enforcement and anti-privilege escalation.
    Creates account and automatically signs user in upon successful validation.
    """
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Explicitly specify authentication backend to avoid AmbiguousBackend error
            login(request, user, backend='apps.accounts.backends.EmailOrUsernameModelBackend')
            messages.success(
                request,
                f"Welcome to Lahore City Hub, {user.first_name or user.username}! Your account has been registered successfully."
            )
            return redirect('accounts:dashboard')
        else:
            messages.error(request, "Please correct the errors indicated below.")
    else:
        form = UserRegistrationForm()

    context = {
        'page_title': 'Create a Member Account | Lahore City Hub',
        'meta_description': 'Join Lahore City Hub to bookmark favorite spots, submit verified reviews, and manage business listings.',
        'form': form,
    }
    return render(request, 'accounts/register.html', context)


def login_view(request):
    """
    Secure authentication view supporting email or username sign-in.
    Protects against Open Redirect attacks by validating the 'next' URL parameter.
    """
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    next_url = request.GET.get('next') or request.POST.get('next') or ''

    if request.method == 'POST':
        form = UserLoginForm(request=request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # Manage session expiry based on 'Remember Me'
            if not form.cleaned_data.get('remember_me'):
                request.session.set_expiry(0)  # Browser close expiration
            else:
                request.session.set_expiry(1209600)  # 2 weeks

            messages.success(request, f"Welcome back, {user.first_name or user.username}!")

            # Validate next URL against allowed hosts to prevent open redirects
            if next_url and url_has_allowed_host_and_scheme(url=next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
            return redirect('accounts:dashboard')
        else:
            messages.error(request, "Invalid sign-in credentials. Please try again.")
    else:
        form = UserLoginForm(request=request)

    context = {
        'page_title': 'Sign In to Your Account | Lahore City Hub',
        'meta_description': 'Access your saved bookmarks, submitted reviews, and claimed business listings on Lahore City Hub.',
        'form': form,
        'next': next_url,
    }
    return render(request, 'accounts/login.html', context)


@require_http_methods(["GET", "POST"])
def logout_view(request):
    """Securely terminates user session and clears authentication state."""
    if request.user.is_authenticated:
        logout(request)
        messages.info(request, "You have been securely signed out. See you soon!")
    return redirect('core:home')


@login_required(login_url='accounts:login')
def dashboard_view(request):
    """
    Private user dashboard displaying profile summary, content submission status,
    business management portals, and saved directory bookmarks.
    Enforces strict server-side authorization: users can only see their own records.
    """
    user = request.user

    # Content Submission Status: User's businesses, edit requests, and claims
    user_businesses = Business.objects.filter(
        Q(submitted_by=user) | Q(claimed_by=user)
    ).select_related('category', 'locality').order_by('-created_at')

    user_edit_requests = BusinessEditRequest.objects.filter(
        requested_by=user
    ).select_related('business').order_by('-created_at')

    user_claims = BusinessClaim.objects.filter(
        claimant=user
    ).select_related('business').order_by('-created_at')

    # Metrics
    total_submissions = user_businesses.count()
    active_count = user_businesses.filter(is_active=True).count()
    pending_count = user_businesses.filter(is_active=False).count()
    verified_count = user_businesses.filter(verification_status__in=['verified', 'claimed']).count()

    # User bookmarks
    bookmarks = UserBookmark.objects.filter(user=user).select_related('content_type')[:10]

    context = {
        'page_title': f"{user.get_full_name() or user.username}'s Dashboard | Lahore City Hub",
        'meta_description': 'Manage your Lahore business listings, submit edit requests, and review verification status.',
        'user': user,
        'businesses': user_businesses,
        'edit_requests': user_edit_requests,
        'claims': user_claims,
        'bookmarks': bookmarks,
        'total_submissions': total_submissions,
        'active_count': active_count,
        'pending_count': pending_count,
        'verified_count': verified_count,
        'is_business_owner': user.role in ['business_owner', 'admin'] or user.is_staff,
    }
    return render(request, 'accounts/dashboard.html', context)


@login_required(login_url='accounts:login')
def profile_view(request):
    """
    Private user profile view for editing personal details, avatar, and notification settings.
    Users are strictly restricted to updating their own profile.
    """
    user = request.user
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile details have been updated successfully.")
            return redirect('accounts:profile')
        else:
            messages.error(request, "Please correct the errors indicated below.")
    else:
        form = UserProfileForm(instance=user)

    context = {
        'page_title': 'My Profile & Preferences | Lahore City Hub',
        'meta_description': 'Update your personal details, home locality, and notification settings.',
        'form': form,
        'user': user,
    }
    return render(request, 'accounts/profile.html', context)


@login_required(login_url='accounts:login')
def password_change_view(request):
    """
    Secure password change view requiring current password verification.
    Preserves active user session using update_session_auth_hash.
    """
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            # Prevent user from being logged out after password change
            update_session_auth_hash(request, user)
            messages.success(request, "Your password has been changed successfully.")
            return redirect('accounts:dashboard')
        else:
            messages.error(request, "Please correct the errors indicated below.")
    else:
        form = PasswordChangeForm(user=request.user)

    context = {
        'page_title': 'Change Your Password | Lahore City Hub',
        'form': form,
    }
    return render(request, 'accounts/password_change.html', context)


# Direct references for backward-compatible routing
user_login = login_view
user_register = register_view
user_dashboard = dashboard_view
