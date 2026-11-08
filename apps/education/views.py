from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, F, Count
from django.contrib.contenttypes.models import ContentType

from apps.core.models import Locality
from apps.core.services import get_cached_localities
from apps.reviews.models import Review
from .models import Institution, EducationType, AccreditationBoard


def education_list(request):
    """
    Searchable, filterable, and paginated directory view for Lahore educational institutions.
    Supports filtering by institution type (schools, colleges, universities, training institutes),
    campus area/locality, gender policy, accreditation, verification status, and keyword search.
    """
    institutions_qs = Institution.objects.filter(is_active=True).select_related(
        'locality', 'locality__zone', 'education_type'
    ).prefetch_related('accreditations')

    # 1. Filter: Institution / Education Type
    selected_type_slug = request.GET.get('type', '').strip()
    selected_type = None
    if selected_type_slug:
        institutions_qs = institutions_qs.filter(education_type__slug=selected_type_slug)
        selected_type = EducationType.objects.filter(slug=selected_type_slug).first()

    # 2. Filter: Area / Locality / Zone
    selected_area_slug = (request.GET.get('area') or request.GET.get('locality') or '').strip()
    selected_locality = None
    if selected_area_slug:
        institutions_qs = institutions_qs.filter(
            Q(locality__slug=selected_area_slug) | Q(locality__zone__slug=selected_area_slug)
        )
        selected_locality = Locality.objects.filter(slug=selected_area_slug).first()

    # 3. Filter: Gender Policy
    selected_gender = request.GET.get('gender', '').strip()
    if selected_gender:
        institutions_qs = institutions_qs.filter(gender_policy=selected_gender)

    # 4. Filter: Accreditation Board
    selected_board_abbr = request.GET.get('board', '').strip()
    if selected_board_abbr:
        institutions_qs = institutions_qs.filter(accreditations__abbreviation__iexact=selected_board_abbr)

    # 5. Filter: Keyword Search
    search_query = request.GET.get('q', '').strip()
    if search_query:
        institutions_qs = institutions_qs.filter(
            Q(title__icontains=search_query) |
            Q(title_ur__icontains=search_query) |
            Q(summary__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(address__icontains=search_query) |
            Q(landmark__icontains=search_query) |
            Q(programs_offered__icontains=search_query) |
            Q(admission_info__icontains=search_query) |
            Q(education_type__name__icontains=search_query)
        )

    # 6. Filter: Verified Only
    verified_only = request.GET.get('verified_only') == '1'
    if verified_only:
        institutions_qs = institutions_qs.filter(verification_status__in=['verified', 'claimed'])

    institutions_qs = institutions_qs.distinct()

    # 7. Sorting
    sort_by = request.GET.get('sort', 'recommended').strip()
    if sort_by == 'title':
        institutions_qs = institutions_qs.order_by('title')
    elif sort_by == 'established':
        institutions_qs = institutions_qs.order_by('established_year', 'title')
    elif sort_by == 'views':
        institutions_qs = institutions_qs.order_by('-view_count')
    elif sort_by == 'newest':
        institutions_qs = institutions_qs.order_by('-created_at')
    else:  # recommended
        institutions_qs = institutions_qs.order_by('-is_featured', 'title')

    total_results = institutions_qs.count()

    # 8. Pagination (9 institutions per page)
    paginator = Paginator(institutions_qs, 9)
    page_number = request.GET.get('page', 1)
    try:
        page_obj = paginator.get_page(page_number)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.get_page(1)

    # 9. Sidebar Taxonomies & Facet Counts
    education_types = EducationType.objects.filter(is_active=True).annotate(
        active_institutions_count=Count('institutions', filter=Q(institutions__is_active=True))
    )
    localities = get_cached_localities()
    accreditations = AccreditationBoard.objects.filter(is_active=True)

    # Query string builder for pagination links
    query_params = request.GET.copy()
    if 'page' in query_params:
        query_params.pop('page')
    extra_query_string = f"&{query_params.urlencode()}" if query_params else ""

    # Dynamic SEO Metadata
    if selected_type:
        page_title = f"{selected_type.name}s in Lahore | Education Directory"
        meta_desc = f"Discover verified {selected_type.name.lower()}s in Lahore, Pakistan. Check recognized degree programs, admission criteria, official websites, and campus locations."
    elif selected_locality:
        page_title = f"Schools, Colleges & Universities in {selected_locality.name}, Lahore"
        meta_desc = f"Find top educational institutes, schools, and colleges in {selected_locality.name}, Lahore. Verified contacts and admission links."
    elif search_query:
        page_title = f"Search Results for '{search_query}' – Education in Lahore"
        meta_desc = f"Search results for academic programs and institutions matching '{search_query}' in Lahore."
    else:
        page_title = "Education in Lahore | Universities, Colleges, Schools & Training Institutes"
        meta_desc = "Comprehensive directory of educational institutions in Lahore: HEC-recognized universities, intermediate colleges, Cambridge schools, and vocational training centers."

    context = {
        'page_title': page_title,
        'meta_description': meta_desc,
        'canonical_url': request.build_absolute_uri(request.path),
        'page_obj': page_obj,
        'institutions': page_obj.object_list,
        'total_results': total_results,
        'education_types': education_types,
        'localities': localities,
        'accreditations': accreditations,
        'gender_policies': Institution.GENDER_POLICIES,
        'selected_type': selected_type_slug,
        'selected_type_obj': selected_type,
        'selected_area': selected_area_slug,
        'selected_locality_obj': selected_locality,
        'selected_gender': selected_gender,
        'selected_board': selected_board_abbr,
        'verified_only': verified_only,
        'sort_by': sort_by,
        'search_query': search_query,
        'extra_query_string': extra_query_string,
    }
    return render(request, 'education/education_list.html', context)


def education_detail(request, slug):
    """
    Detailed educational institution profile view in Lahore.
    Includes degree programs, admission guidelines, official portal links,
    accreditation bodies, contact numbers, campus map, and peer institutions.
    """
    institution = get_object_or_404(
        Institution.objects.select_related(
            'locality', 'locality__zone', 'education_type'
        ).prefetch_related('accreditations'),
        slug=slug,
        is_active=True
    )

    # Increment view count
    Institution.objects.filter(pk=institution.pk).update(view_count=F('view_count') + 1)

    # Related institutions (same education type or same locality, excluding self)
    related_institutions = (
        Institution.objects.filter(is_active=True)
        .filter(Q(education_type=institution.education_type) | Q(locality=institution.locality))
        .exclude(pk=institution.pk)
        .select_related('locality', 'education_type')
        .distinct()[:3]
    )

    # Approved Visitor Reviews
    institution_ct = ContentType.objects.get_for_model(Institution)
    reviews = Review.objects.filter(
        content_type=institution_ct,
        object_id=institution.pk,
        moderation_status=Review.STATUS_APPROVED
    ).select_related('user').order_by('-created_at')

    # SEO metadata
    meta_title = institution.meta_title or f"{institution.title} – Admissions, Programs & Campus | Lahore"
    meta_desc = institution.meta_description or institution.summary
    canonical_url = request.build_absolute_uri(institution.get_absolute_url())

    context = {
        'institution': institution,
        'item': institution,
        'related_institutions': related_institutions,
        'reviews': reviews,
        'page_title': meta_title,
        'meta_description': meta_desc,
        'canonical_url': canonical_url,
    }
    return render(request, 'education/education_detail.html', context)
