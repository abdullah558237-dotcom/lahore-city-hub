from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, F, Count
from django.contrib.contenttypes.models import ContentType

from apps.core.models import Locality
from apps.core.services import get_cached_localities
from apps.reviews.models import Review
from .models import Hospital, MedicalSpecialty


def hospital_list(request):
    """
    Searchable, filterable, and paginated healthcare directory view for Lahore hospitals and clinics.
    Supports filtering by facility type, area/locality, medical specialty, verified 24/7 emergency care,
    trauma center, blood bank, and keyword search.
    """
    hospitals_qs = Hospital.objects.filter(is_active=True).select_related(
        'locality', 'locality__zone'
    ).prefetch_related('specialties')

    # 1. Filter: Facility Type
    selected_type = request.GET.get('type', '').strip()
    if selected_type:
        hospitals_qs = hospitals_qs.filter(hospital_type=selected_type)

    # 2. Filter: Area / Locality / Zone
    selected_area_slug = (request.GET.get('area') or request.GET.get('locality') or '').strip()
    selected_locality = None
    if selected_area_slug:
        hospitals_qs = hospitals_qs.filter(
            Q(locality__slug=selected_area_slug) | Q(locality__zone__slug=selected_area_slug)
        )
        selected_locality = Locality.objects.filter(slug=selected_area_slug).first()

    # 3. Filter: Medical Specialty / Service
    selected_specialty_slug = request.GET.get('specialty', '').strip()
    selected_specialty = None
    if selected_specialty_slug:
        hospitals_qs = hospitals_qs.filter(specialties__slug=selected_specialty_slug)
        selected_specialty = MedicalSpecialty.objects.filter(slug=selected_specialty_slug).first()

    # 4. Filter: Keyword Search
    search_query = request.GET.get('q', '').strip()
    if search_query:
        hospitals_qs = hospitals_qs.filter(
            Q(title__icontains=search_query) |
            Q(title_ur__icontains=search_query) |
            Q(summary__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(address__icontains=search_query) |
            Q(landmark__icontains=search_query) |
            Q(specialties__name__icontains=search_query)
        )

    # 5. Filter: Verified Emergency Facilities
    emergency_only = request.GET.get('emergency') == '1'
    if emergency_only:
        # Verified emergency only - never claim emergency without verification
        hospitals_qs = hospitals_qs.filter(
            is_24_7_emergency=True,
            verification_status__in=['verified', 'claimed']
        )

    # 6. Filter: Clinical Infrastructure
    trauma_only = request.GET.get('trauma') == '1'
    if trauma_only:
        hospitals_qs = hospitals_qs.filter(has_trauma_center=True)

    blood_bank_only = request.GET.get('blood_bank') == '1'
    if blood_bank_only:
        hospitals_qs = hospitals_qs.filter(has_blood_bank=True)

    pharmacy_only = request.GET.get('pharmacy') == '1'
    if pharmacy_only:
        hospitals_qs = hospitals_qs.filter(has_24_7_pharmacy=True)

    # 7. Filter: Verified Only
    verified_only = request.GET.get('verified_only') == '1'
    if verified_only:
        hospitals_qs = hospitals_qs.filter(verification_status__in=['verified', 'claimed'])

    # Distinct results when filtering across ManyToMany relations
    hospitals_qs = hospitals_qs.distinct()

    # 8. Sorting
    sort_by = request.GET.get('sort', 'recommended').strip()
    if sort_by == 'emergency':
        hospitals_qs = hospitals_qs.order_by('-is_24_7_emergency', '-has_trauma_center', 'title')
    elif sort_by == 'title':
        hospitals_qs = hospitals_qs.order_by('title')
    elif sort_by == 'beds':
        hospitals_qs = hospitals_qs.order_by('-bed_capacity', 'title')
    elif sort_by == 'views':
        hospitals_qs = hospitals_qs.order_by('-view_count')
    elif sort_by == 'newest':
        hospitals_qs = hospitals_qs.order_by('-created_at')
    else:  # recommended
        hospitals_qs = hospitals_qs.order_by('-is_featured', 'title')

    total_results = hospitals_qs.count()

    # 9. Pagination (9 facilities per page)
    paginator = Paginator(hospitals_qs, 9)
    page_number = request.GET.get('page', 1)
    try:
        page_obj = paginator.get_page(page_number)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.get_page(1)

    # 10. Sidebar Taxonomies & Counts
    specialties = MedicalSpecialty.objects.filter(is_active=True).annotate(
        active_hospitals_count=Count('hospitals', filter=Q(hospitals__is_active=True))
    )
    localities = get_cached_localities()
    verified_emergency_count = Hospital.objects.filter(
        is_active=True, is_24_7_emergency=True, verification_status__in=['verified', 'claimed']
    ).count()

    # Query string builder for pagination links
    query_params = request.GET.copy()
    if 'page' in query_params:
        query_params.pop('page')
    extra_query_string = f"&{query_params.urlencode()}" if query_params else ""

    # Dynamic SEO Metadata
    if selected_type:
        type_dict = dict(Hospital.HOSPITAL_TYPES)
        type_name = type_dict.get(selected_type, selected_type.title())
        page_title = f"{type_name}s in Lahore | Healthcare Directory"
        meta_desc = f"Directory of verified {type_name.lower()}s across Lahore, Pakistan. Emergency contacts, bed capacities, specialties, and locations."
    elif selected_specialty:
        page_title = f"{selected_specialty.name} Hospitals & Clinics in Lahore | Lahore City Hub"
        meta_desc = f"Find verified hospitals and clinics offering {selected_specialty.name.lower()} in Lahore, Pakistan. Check verified phone numbers and doctors."
    elif selected_locality:
        page_title = f"Hospitals & Clinics in {selected_locality.name}, Lahore | Emergency Guide"
        meta_desc = f"Explore medical centers, 24/7 hospitals, and clinics in {selected_locality.name}, Lahore. Verified emergency numbers and directions."
    elif search_query:
        page_title = f"Search Results for '{search_query}' – Hospitals in Lahore"
        meta_desc = f"Search results for healthcare facilities matching '{search_query}' in Lahore."
    elif emergency_only:
        page_title = "24/7 Emergency Hospitals in Lahore | Urgent Care Directory"
        meta_desc = "Verified 24/7 emergency hospitals, trauma centers, and direct ambulance helplines in Lahore, Pakistan."
    else:
        page_title = "Hospitals & Medical Clinics in Lahore | Lahore Healthcare Directory"
        meta_desc = "Verified directory of Lahore hospitals, 24/7 emergency medical centers, trauma units, blood banks, and diagnostic clinics across all zones."

    context = {
        'page_title': page_title,
        'meta_description': meta_desc,
        'canonical_url': request.build_absolute_uri(request.path),
        'page_obj': page_obj,
        'hospitals': page_obj.object_list,
        'total_results': total_results,
        'hospital_types': Hospital.HOSPITAL_TYPES,
        'specialties': specialties,
        'localities': localities,
        'selected_type': selected_type,
        'selected_specialty': selected_specialty_slug,
        'selected_specialty_obj': selected_specialty,
        'selected_area': selected_area_slug,
        'selected_locality_obj': selected_locality,
        'emergency_only': emergency_only,
        'trauma_only': trauma_only,
        'blood_bank_only': blood_bank_only,
        'pharmacy_only': pharmacy_only,
        'verified_only': verified_only,
        'sort_by': sort_by,
        'search_query': search_query,
        'extra_query_string': extra_query_string,
        'verified_emergency_count': verified_emergency_count,
    }
    return render(request, 'hospitals/hospital_list.html', context)


def hospital_detail(request, slug):
    """
    Detailed healthcare facility profile in Lahore.
    Includes verified emergency operations, ambulance contacts, clinical specialties,
    trauma capabilities, blood bank, official website links, and civic emergency guidance.
    """
    hospital = get_object_or_404(
        Hospital.objects.select_related(
            'locality', 'locality__zone'
        ).prefetch_related('specialties'),
        slug=slug,
        is_active=True
    )

    # Increment view count
    Hospital.objects.filter(pk=hospital.pk).update(view_count=F('view_count') + 1)

    # Related medical facilities (same area or sharing specialties, excluding self)
    specialty_ids = hospital.specialties.values_list('id', flat=True)
    related_facilities = (
        Hospital.objects.filter(is_active=True)
        .filter(Q(locality=hospital.locality) | Q(specialties__in=specialty_ids))
        .exclude(pk=hospital.pk)
        .select_related('locality')
        .prefetch_related('specialties')
        .distinct()[:3]
    )

    # Approved Visitor Reviews
    hospital_ct = ContentType.objects.get_for_model(Hospital)
    reviews = Review.objects.filter(
        content_type=hospital_ct,
        object_id=hospital.pk,
        moderation_status=Review.STATUS_APPROVED
    ).select_related('user').order_by('-created_at')

    # SEO metadata
    meta_title = hospital.meta_title or f"{hospital.title} – Emergency, Doctors & Services | Lahore"
    meta_desc = hospital.meta_description or hospital.summary
    canonical_url = request.build_absolute_uri(hospital.get_absolute_url())

    context = {
        'hospital': hospital,
        'item': hospital,
        'related_facilities': related_facilities,
        'reviews': reviews,
        'page_title': meta_title,
        'meta_description': meta_desc,
        'canonical_url': canonical_url,
    }
    return render(request, 'hospitals/hospital_detail.html', context)
