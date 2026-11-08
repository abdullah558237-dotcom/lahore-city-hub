from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, F, Count
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404

from apps.core.models import Locality
from .models import (
    Business,
    BusinessCategory,
    BusinessEditRequest,
    BusinessReport,
    BusinessClaim,
    BusinessPromotionRequest,
)
from .forms import (
    BusinessSubmissionForm,
    BusinessEditForm,
    BusinessEditRequestForm,
    BusinessReportForm,
    BusinessClaimForm,
    BusinessPromotionRequestForm,
)


def business_list(request):
    """
    Searchable, filterable, and paginated directory view for Lahore local businesses.
    Enforces that ONLY approved and active listings (is_active=True) are visible to the public.
    Supports category filtering, area/locality filtering, verified-only toggle, and keyword search.
    """
    businesses_qs = Business.objects.filter(is_active=True).select_related(
        'category', 'locality', 'locality__zone'
    )

    # 1. Category Filter
    selected_category_slug = request.GET.get('category', '').strip()
    selected_category = None
    if selected_category_slug:
        businesses_qs = businesses_qs.filter(category__slug=selected_category_slug)
        selected_category = BusinessCategory.objects.filter(slug=selected_category_slug).first()

    # 2. Area / Locality Filter
    selected_area_slug = (request.GET.get('area') or request.GET.get('locality') or '').strip()
    selected_locality = None
    if selected_area_slug:
        businesses_qs = businesses_qs.filter(
            Q(locality__slug=selected_area_slug) | Q(locality__zone__slug=selected_area_slug)
        )
        selected_locality = Locality.objects.filter(slug=selected_area_slug).first()

    # 3. Verified Only Filter
    verified_only = request.GET.get('verified_only') == '1'
    if verified_only:
        businesses_qs = businesses_qs.filter(verification_status__in=['verified', 'claimed'])

    # 4. Keyword Search
    search_query = request.GET.get('q', '').strip()
    if search_query:
        businesses_qs = businesses_qs.filter(
            Q(title__icontains=search_query) |
            Q(title_ur__icontains=search_query) |
            Q(summary__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(address__icontains=search_query) |
            Q(landmark__icontains=search_query) |
            Q(category__name__icontains=search_query) |
            Q(registration_number__icontains=search_query)
        )

    businesses_qs = businesses_qs.distinct()

    # 5. Sorting
    sort_by = request.GET.get('sort', 'recommended').strip()
    if sort_by == 'title':
        businesses_qs = businesses_qs.order_by('title')
    elif sort_by == 'views':
        businesses_qs = businesses_qs.order_by('-view_count', 'title')
    elif sort_by == 'newest':
        businesses_qs = businesses_qs.order_by('-created_at')
    else:  # recommended
        businesses_qs = businesses_qs.order_by('-is_featured', 'title')

    total_results = businesses_qs.count()

    # 6. Pagination (9 per page)
    paginator = Paginator(businesses_qs, 9)
    page_number = request.GET.get('page', 1)
    try:
        page_obj = paginator.get_page(page_number)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.get_page(1)

    # 7. Sidebar Taxonomies
    categories = BusinessCategory.objects.filter(is_active=True).annotate(
        active_count=Count('businesses', filter=Q(businesses__is_active=True))
    )
    localities = Locality.objects.all().select_related('zone').order_by('zone__name', 'name')

    # 8. Featured Spotlight
    featured_businesses = Business.objects.filter(
        is_active=True, is_featured=True
    ).select_related('category', 'locality')[:3]

    # Query string builder for pagination links
    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']
    pagination_querystring = query_params.urlencode()

    page_title = "Local Businesses in Lahore | Commercial Directory"
    meta_description = "Explore verified local businesses, retail outlets, professional services, solar contractors, and artisan studios across Lahore."
    if selected_category:
        page_title = f"{selected_category.name} in Lahore | Business Directory"
        meta_description = f"Verified listings for {selected_category.name} across Gulberg, DHA, Johar Town, and Lahore."
    elif search_query:
        page_title = f"Search Results for '{search_query}' | Lahore Business Directory"

    context = {
        'page_title': f"{page_title} | Lahore City Hub",
        'meta_description': meta_description,
        'canonical_url': request.build_absolute_uri(request.path),
        'businesses': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'total_results': total_results,
        'selected_category': selected_category,
        'selected_category_slug': selected_category_slug,
        'selected_locality': selected_locality,
        'selected_area_slug': selected_area_slug,
        'verified_only': verified_only,
        'search_query': search_query,
        'sort_by': sort_by,
        'categories': categories,
        'localities': localities,
        'featured_businesses': featured_businesses,
        'pagination_querystring': pagination_querystring,
    }
    return render(request, 'businesses/business_list.html', context)


def business_detail(request, slug):
    """
    Detailed profile view for an approved business.
    Unpublished businesses (is_active=False) return 404 to public users,
    but can be previewed by the listing owner or staff members.
    """
    business = get_object_or_404(
        Business.objects.select_related('category', 'locality', 'locality__zone', 'claimed_by', 'submitted_by'),
        slug=slug
    )

    is_owner = request.user.is_authenticated and (
        business.claimed_by == request.user or
        business.submitted_by == request.user or
        request.user.is_staff
    )

    # Security check: if listing is not active and visitor is not owner/staff, 404
    if not business.is_active and not is_owner:
        raise Http404("This business listing is currently pending editorial audit or is inactive.")

    # Increment view count
    if business.is_active:
        Business.objects.filter(pk=business.pk).update(view_count=F('view_count') + 1)
        business.view_count += 1

    # Related businesses in same category
    related_businesses = Business.objects.filter(
        category=business.category,
        is_active=True
    ).exclude(pk=business.pk).select_related('locality')[:3]

    report_form = BusinessReportForm()
    claim_form = BusinessClaimForm()

    page_title = f"{business.title} | {business.category.name} in Lahore"
    meta_description = business.summary or f"{business.title} located at {business.address}, Lahore."

    context = {
        'page_title': f"{page_title} | Lahore City Hub",
        'meta_description': meta_description,
        'canonical_url': request.build_absolute_uri(business.get_absolute_url()),
        'business': business,
        'is_owner': is_owner,
        'related_businesses': related_businesses,
        'report_form': report_form,
        'claim_form': claim_form,
    }
    return render(request, 'businesses/business_detail.html', context)


def business_submit(request):
    """
    Onboarding view for new business submissions.
    Enforces security guarantees:
    - Anyone can view the onboarding submission form (HTTP 200).
    - Submitting (POST) requires an authenticated account to tie ownership (redirects to login).
    - New submissions MUST remain unpublished (is_active=False) until approved.
    - Verification status is explicitly set to 'pending'.
    - Submitted_by is bound to request.user.
    - Form whitelisting prevents privilege escalation.
    """
    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.info(request, "Please log in or register to submit and manage your business listing.")
            return redirect(f"{reverse('accounts:login')}?next={request.path}")

        form = BusinessSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            business = form.save(commit=False)
            business.is_active = False
            business.verification_status = 'pending'
            business.is_featured = False
            business.submitted_by = request.user
            business.save()
            form.save_m2m()

            messages.success(
                request,
                f"Your business listing '{business.title}' has been submitted for editorial audit! "
                "It will remain unpublished until reviewed and approved by our moderation team."
            )
            return redirect('businesses:dashboard')
        else:
            messages.error(request, "Please correct the errors indicated below.")
    else:
        form = BusinessSubmissionForm()

    context = {
        'page_title': 'Submit or Claim a Business Listing | Lahore City Hub',
        'meta_description': 'Submit your Lahore business listing for editorial verification and directory inclusion.',
        'form': form,
    }
    return render(request, 'businesses/business_submit.html', context)


@login_required(login_url='accounts:login')
def owner_dashboard(request):
    """
    Owner portal displaying listings, edit requests, and claims belonging to the authenticated user.
    Security guarantee: Users can only see and manage their own submissions/claims.
    """
    user_businesses = Business.objects.filter(
        Q(claimed_by=request.user) | Q(submitted_by=request.user)
    ).select_related('category', 'locality').order_by('-created_at')

    total_count = user_businesses.count()
    active_count = user_businesses.filter(is_active=True).count()
    pending_count = user_businesses.filter(is_active=False).count()

    edit_requests = BusinessEditRequest.objects.filter(
        requested_by=request.user
    ).select_related('business').order_by('-created_at')

    claims = BusinessClaim.objects.filter(
        claimant=request.user
    ).select_related('business').order_by('-created_at')

    promotion_requests = BusinessPromotionRequest.objects.filter(
        requested_by=request.user
    ).select_related('business').order_by('-created_at')

    context = {
        'page_title': 'Owner Dashboard | Lahore City Hub',
        'meta_description': 'Manage your Lahore business listings, submit edit requests, and review verification status.',
        'businesses': user_businesses,
        'total_count': total_count,
        'active_count': active_count,
        'pending_count': pending_count,
        'edit_requests': edit_requests,
        'claims': claims,
        'promotion_requests': promotion_requests,
    }
    return render(request, 'businesses/owner_dashboard.html', context)


@login_required(login_url='accounts:login')
def business_request_promotion(request, slug):
    """
    Self-service promotion / tier upgrade request endpoint for business owners.
    Security guarantees:
    - Only the listing owner (claimed_by or submitted_by) or staff can request promotion.
    - Non-owners are denied access (HTTP 403 Forbidden).
    - Unauthenticated requests are redirected to login (HTTP 302).
    - No payment details or live financial transactions are processed in this phase.
    """
    business = get_object_or_404(Business, slug=slug)

    is_owner = (business.claimed_by == request.user or business.submitted_by == request.user)
    if not is_owner and not request.user.is_staff:
        raise PermissionDenied("You do not have permission to manage promotions for this business.")

    if request.method == 'POST':
        form = BusinessPromotionRequestForm(request.POST)
        if form.is_valid():
            promo_req = form.save(commit=False)
            promo_req.business = business
            promo_req.requested_by = request.user
            promo_req.status = 'pending'
            promo_req.save()
            messages.success(
                request,
                f"Your promotion request for '{business.title}' has been submitted! "
                "Our business partnerships desk will contact you to coordinate verification and placement."
            )
            return redirect('businesses:dashboard')
        else:
            messages.error(request, "Please correct the errors in the promotion request form.")
    else:
        initial_data = {
            'contact_email': request.user.email,
            'contact_phone': business.phone_number or getattr(request.user, 'phone_number', ''),
            'target_tier': Business.PROMOTION_TIER_FEATURED,
        }
        form = BusinessPromotionRequestForm(initial=initial_data)

    context = {
        'page_title': f"Promote Listing - {business.title} | Lahore City Hub",
        'meta_description': f"Request sponsored spotlight promotion or verified partner status for {business.title}.",
        'business': business,
        'form': form,
    }
    return render(request, 'businesses/business_promotion_request.html', context)


@login_required(login_url='accounts:login')
def business_edit(request, slug):
    """
    Edit view for business owners.
    Security guarantees:
    - Only the listing owner (claimed_by or submitted_by) or staff can access (HTTP 403 on failure).
    - If the listing is active/published: Edits are submitted as a BusinessEditRequest for audit.
      This prevents live records from being defaced or altered without editorial moderation.
    - If the listing is unpublished/pending: The owner can directly update the draft, which remains
      is_active=False and verification_status='pending'.
    """
    business = get_object_or_404(Business, slug=slug)

    is_owner = (business.claimed_by == request.user or business.submitted_by == request.user)
    if not is_owner and not request.user.is_staff:
        raise PermissionDenied("You do not have permission to edit this business listing.")

    if business.is_active and not request.user.is_staff:
        # Published business: changes must go through edit request audit workflow
        if request.method == 'POST':
            form = BusinessEditRequestForm(request.POST)
            if form.is_valid():
                edit_req = form.save(commit=False)
                edit_req.business = business
                edit_req.requested_by = request.user
                edit_req.status = 'pending'
                edit_req.save()
                messages.success(
                    request,
                    f"Your edit request for '{business.title}' has been submitted for moderation review. "
                    "The live listing will be updated upon admin approval."
                )
                return redirect('businesses:dashboard')
            else:
                messages.error(request, "Please correct the errors in your edit request.")
        else:
            initial_data = {
                'title': business.title,
                'summary': business.summary,
                'description': business.description,
                'address': business.address,
                'phone_number': business.phone_number,
                'website': business.website,
                'operating_hours': business.operating_hours,
            }
            form = BusinessEditRequestForm(initial=initial_data)
        is_edit_request = True
    else:
        # Unpublished draft: direct update to draft
        if request.method == 'POST':
            form = BusinessEditForm(request.POST, request.FILES, instance=business)
            if form.is_valid():
                updated_biz = form.save(commit=False)
                if not request.user.is_staff:
                    updated_biz.is_active = False
                    updated_biz.verification_status = 'pending'
                updated_biz.save()
                form.save_m2m()
                messages.success(request, f"Listing draft for '{updated_biz.title}' has been updated.")
                return redirect('businesses:dashboard')
            else:
                messages.error(request, "Please correct the errors in the draft form.")
        else:
            form = BusinessEditForm(instance=business)
        is_edit_request = False

    context = {
        'page_title': f"Edit Listing - {business.title} | Lahore City Hub",
        'business': business,
        'form': form,
        'is_edit_request': is_edit_request,
    }
    return render(request, 'businesses/business_edit.html', context)


@login_required(login_url='accounts:login')
def business_delete(request, slug):
    """
    Secure deletion/deactivation endpoint for business owners.
    Security guarantee: Non-owners cannot delete or deactivate listings (HTTP 403).
    """
    business = get_object_or_404(Business, slug=slug)

    is_owner = (business.claimed_by == request.user or business.submitted_by == request.user)
    if not is_owner and not request.user.is_staff:
        raise PermissionDenied("You do not have permission to delete this business listing.")

    if request.method == 'POST':
        title = business.title
        business.delete()
        messages.success(request, f"Listing '{title}' has been permanently deleted.")
        return redirect('businesses:dashboard')

    context = {
        'page_title': f"Delete {business.title} | Lahore City Hub",
        'business': business,
    }
    return render(request, 'businesses/business_confirm_delete.html', context)


def report_listing(request, slug):
    """
    Public endpoint for submitting inaccuracy/discrepancy reports on a business listing.
    """
    business = get_object_or_404(Business, slug=slug, is_active=True)

    if request.method == 'POST':
        form = BusinessReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.business = business
            if request.user.is_authenticated:
                report.reported_by = request.user
            report.status = 'pending'
            report.save()
            messages.success(
                request,
                "Thank you for reporting this issue. Our editorial desk will investigate and update the record."
            )
        else:
            messages.error(request, "Could not submit report. Please fill in all required fields accurately.")

    return redirect('businesses:detail', slug=slug)


@login_required(login_url='accounts:login')
def business_claim(request, slug):
    """
    Submission endpoint for claiming ownership of an existing business listing.
    """
    business = get_object_or_404(Business, slug=slug, is_active=True)

    if business.claimed_by:
        messages.warning(request, "This business has already been claimed and verified.")
        return redirect('businesses:detail', slug=slug)

    if request.method == 'POST':
        form = BusinessClaimForm(request.POST, request.FILES)
        if form.is_valid():
            claim = form.save(commit=False)
            claim.business = business
            claim.claimant = request.user
            claim.status = 'pending'
            claim.save()
            messages.success(
                request,
                "Your ownership claim has been submitted with supporting credentials. "
                "Our verification desk will review it shortly."
            )
            return redirect('businesses:dashboard')
        else:
            messages.error(request, "Please provide complete ownership verification details.")

    return redirect('businesses:detail', slug=slug)
