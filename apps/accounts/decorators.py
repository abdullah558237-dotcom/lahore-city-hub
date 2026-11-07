from functools import wraps
from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied
from django.conf import settings


def role_required(allowed_roles):
    """
    Decorator for views that checks whether the logged-in user belongs to one
    of the allowed roles. If not authenticated, redirects to the login page.
    If authenticated but role not in allowed_roles (and not superuser), raises PermissionDenied (403).
    """
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                login_url = getattr(settings, 'LOGIN_URL', 'accounts:login')
                return redirect(f"{login_url}?next={request.get_full_path()}")

            # Superusers and staff always bypass role checks
            if request.user.is_superuser or request.user.is_staff:
                return view_func(request, *args, **kwargs)

            # Check user role
            if getattr(request.user, 'role', None) in allowed_roles:
                return view_func(request, *args, **kwargs)

            raise PermissionDenied("You do not have the required permissions to access this resource.")
        return _wrapped_view
    return decorator


def business_owner_required(view_func):
    """Restricts view access to authenticated business owners and administrators."""
    return role_required(['business_owner', 'admin'])(view_func)


def moderator_required(view_func):
    """Restricts view access to editorial moderators and administrators."""
    return role_required(['moderator', 'admin'])(view_func)


def admin_required(view_func):
    """Restricts view access strictly to platform administrators."""
    return role_required(['admin'])(view_func)
