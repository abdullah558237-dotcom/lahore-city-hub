from datetime import timedelta
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Count
from django.utils import timezone

from apps.core.models import Locality
from apps.core.services import get_cached_localities
from .models import JobListing, JobCategory, Employer


def job_list(request):
    """
    Searchable, filterable, and paginated directory view for Lahore employment opportunities.
    Supports filtering by category, employment type, experience, locality, deadline urgency,
    keyword search, and expired status handling.
    """
    today = timezone.now().date()
    jobs_qs = JobListing.objects.filter(is_active=True).select_related(
        'employer', 'category', 'locality', 'locality__zone'
    )

    # 1. Expired / Deadline Status Handling
    status_filter = request.GET.get('status', 'active').strip()
    include_expired = request.GET.get('include_expired') == '1'

    if status_filter == 'expired':
        jobs_qs = jobs_qs.filter(deadline__lt=today)
    elif status_filter in ['all', 'any'] or include_expired:
        # Show all jobs regardless of deadline
        pass
    else:  # default 'active'
        jobs_qs = jobs_qs.filter(deadline__gte=today)

    # 2. Deadline Urgency Filter
    deadline_filter = request.GET.get('deadline', '').strip()
    if deadline_filter == 'closing_soon':
        seven_days_later = today + timedelta(days=7)
        jobs_qs = jobs_qs.filter(deadline__gte=today, deadline__lte=seven_days_later)
    elif deadline_filter == 'this_month':
        thirty_days_later = today + timedelta(days=30)
        jobs_qs = jobs_qs.filter(deadline__gte=today, deadline__lte=thirty_days_later)

    # 3. Category Filter
    selected_category_slug = request.GET.get('category', '').strip()
    selected_category = None
    if selected_category_slug:
        jobs_qs = jobs_qs.filter(category__slug=selected_category_slug)
        selected_category = JobCategory.objects.filter(slug=selected_category_slug).first()

    # 4. Employment Type Filter
    selected_type = request.GET.get('type', '').strip()
    if selected_type:
        jobs_qs = jobs_qs.filter(employment_type=selected_type)

    # 5. Experience Level Filter
    selected_experience = request.GET.get('experience', '').strip()
    if selected_experience:
        jobs_qs = jobs_qs.filter(experience_level=selected_experience)

    # 6. Locality / Area Filter
    selected_area_slug = (request.GET.get('area') or request.GET.get('locality') or '').strip()
    selected_locality = None
    if selected_area_slug:
        jobs_qs = jobs_qs.filter(
            Q(locality__slug=selected_area_slug) | Q(locality__zone__slug=selected_area_slug)
        )
        selected_locality = Locality.objects.filter(slug=selected_area_slug).first()

    # 7. Employer Filter
    selected_employer_slug = request.GET.get('employer', '').strip()
    selected_employer = None
    if selected_employer_slug:
        jobs_qs = jobs_qs.filter(employer__slug=selected_employer_slug)
        selected_employer = Employer.objects.filter(slug=selected_employer_slug).first()

    # 8. Keyword Search
    search_query = request.GET.get('q', '').strip()
    if search_query:
        jobs_qs = jobs_qs.filter(
            Q(title__icontains=search_query) |
            Q(employer__name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(requirements__icontains=search_query) |
            Q(qualifications__icontains=search_query) |
            Q(locality__name__icontains=search_query)
        )

    # 9. Verified Only Filter
    verified_only = request.GET.get('verified_only') == '1'
    if verified_only:
        jobs_qs = jobs_qs.filter(
            Q(verification_status='verified') | Q(employer__is_verified=True)
        )

    # 10. Sorting
    sort_by = request.GET.get('sort', 'default').strip()
    if sort_by == 'deadline':
        jobs_qs = jobs_qs.order_by('deadline', '-created_at')
    elif sort_by == 'newest':
        jobs_qs = jobs_qs.order_by('-created_at')
    elif sort_by == 'salary':
        jobs_qs = jobs_qs.order_by('-salary_max_pkr', '-created_at')
    elif sort_by == 'title':
        jobs_qs = jobs_qs.order_by('title')
    else:  # default: featured first, then imminent deadlines, then newest
        jobs_qs = jobs_qs.order_by('-is_featured', 'deadline', '-created_at')

    total_results = jobs_qs.count()

    # 11. Pagination (10 jobs per page)
    paginator = Paginator(jobs_qs, 10)
    page_number = request.GET.get('page', 1)
    try:
        page_obj = paginator.get_page(page_number)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.get_page(1)

    # 12. Taxonomy & Sidebar Statistics
    categories = JobCategory.objects.filter(is_active=True).annotate(
        active_jobs_count=Count(
            'jobs',
            filter=Q(jobs__is_active=True, jobs__deadline__gte=today)
        )
    )

    # High-performance single GROUP BY query for all employment types (replaces N+1 loop queries)
    raw_type_counts = dict(
        JobListing.objects.filter(is_active=True, deadline__gte=today)
        .values('employment_type')
        .annotate(total=Count('id'))
        .values_list('employment_type', 'total')
    )
    employment_type_counts = {
        code: {'label': label, 'count': raw_type_counts.get(code, 0)}
        for code, label in JobListing.EMPLOYMENT_TYPES
    }

    localities = get_cached_localities()
    active_jobs_total = sum(raw_type_counts.values())
    expired_jobs_total = JobListing.objects.filter(is_active=True, deadline__lt=today).count()

    # Preserve URL params for pagination
    query_params = request.GET.copy()
    if 'page' in query_params:
        query_params.pop('page')
    extra_query_string = f"&{query_params.urlencode()}" if query_params else ""

    # Dynamic SEO Metadata
    if selected_category:
        page_title = f"{selected_category.name} in Lahore | Lahore Jobs Portal"
        meta_desc = f"Browse the latest verified {selected_category.name.lower()} in Lahore, Pakistan. Competitive salaries, direct application links, and verified employers."
    elif selected_employer:
        page_title = f"Jobs at {selected_employer.name} | Lahore City Hub"
        meta_desc = f"Explore current job vacancies and career opportunities at {selected_employer.name} in Lahore."
    elif selected_locality:
        page_title = f"Jobs in {selected_locality.name}, Lahore | Careers Directory"
        meta_desc = f"Find verified jobs and career openings in {selected_locality.name}, Lahore, Pakistan."
    elif search_query:
        page_title = f"Search Results for '{search_query}' – Lahore Jobs"
        meta_desc = f"Find job openings for '{search_query}' across top employers in Lahore."
    else:
        page_title = "Jobs in Lahore | Verified Careers & Employment Opportunities"
        meta_desc = "Discover verified jobs in Lahore across IT, healthcare, education, retail, and corporate sectors. Direct employer links and confirmed salary ranges."

    context = {
        'page_title': page_title,
        'meta_description': meta_desc,
        'canonical_url': request.build_absolute_uri(request.path),
        'page_obj': page_obj,
        'jobs': page_obj.object_list,
        'total_results': total_results,
        'categories': categories,
        'employment_types': JobListing.EMPLOYMENT_TYPES,
        'employment_type_counts': employment_type_counts,
        'experience_levels': JobListing.EXPERIENCE_LEVELS,
        'localities': localities,
        'selected_category': selected_category_slug,
        'selected_category_obj': selected_category,
        'selected_type': selected_type,
        'selected_experience': selected_experience,
        'selected_area': selected_area_slug,
        'selected_locality_obj': selected_locality,
        'selected_employer': selected_employer_slug,
        'selected_employer_obj': selected_employer,
        'status_filter': status_filter,
        'include_expired': include_expired,
        'deadline_filter': deadline_filter,
        'search_query': search_query,
        'verified_only': verified_only,
        'sort_by': sort_by,
        'extra_query_string': extra_query_string,
        'active_jobs_total': active_jobs_total,
        'expired_jobs_total': expired_jobs_total,
        'today': today,
    }
    return render(request, 'jobs/job_list.html', context)


def job_detail(request, slug):
    """
    Comprehensive job detail view displaying job description, qualifications,
    experience requirements, salary, verified employer profile, official application link,
    source URL, and related job opportunities.
    """
    today = timezone.now().date()
    job = get_object_or_404(
        JobListing.objects.select_related('employer', 'category', 'locality', 'locality__zone'),
        slug=slug,
        is_active=True
    )

    # Related Jobs: Same category or same employer or same employment type (active & unexpired, excluding self)
    related_jobs = (
        JobListing.objects.filter(is_active=True, deadline__gte=today)
        .filter(Q(category=job.category) | Q(employer=job.employer) | Q(employment_type=job.employment_type))
        .exclude(pk=job.pk)
        .select_related('employer', 'category', 'locality')
        .distinct()[:3]
    )

    # SEO metadata
    page_title = job.meta_title or f"{job.title} at {job.employer.name} – Jobs in Lahore"
    meta_desc = job.meta_description or (job.description[:155] if job.description else "")
    canonical_url = request.build_absolute_uri(job.get_absolute_url())

    context = {
        'job': job,
        'related_jobs': related_jobs,
        'is_expired': job.is_expired,
        'page_title': page_title,
        'meta_description': meta_desc,
        'canonical_url': canonical_url,
        'today': today,
    }
    return render(request, 'jobs/job_detail.html', context)
