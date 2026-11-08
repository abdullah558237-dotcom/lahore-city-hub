from django import forms
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from apps.core.models import Locality
from .models import (
    Business,
    BusinessCategory,
    BusinessEditRequest,
    BusinessReport,
    BusinessClaim,
    BusinessPromotionRequest,
    validate_image_extension,
)


class BusinessSubmissionForm(forms.ModelForm):
    """
    Public and member submission form for onboarding businesses to Lahore City Hub.
    Strictly whitelists safe fields to prevent privilege escalation.
    All submissions are saved as unpublished (is_active=False) and pending audit.
    """
    category = forms.ModelChoiceField(
        queryset=BusinessCategory.objects.filter(is_active=True),
        empty_label="Select Business Category",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    locality = forms.ModelChoiceField(
        queryset=Locality.objects.all().select_related('zone').order_by('zone__name', 'name'),
        empty_label="Select Locality / Neighborhood",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    website = forms.URLField(
        required=False,
        error_messages={'invalid': 'Please enter a valid website URL starting with http:// or https://.'},
        widget=forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://www.yourbusiness.pk'})
    )
    source_url = forms.URLField(
        required=False,
        error_messages={'invalid': 'Please enter a valid source URL starting with http:// or https://.'},
        widget=forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://lcci.com.pk/directory or social/register proof URL'})
    )

    class Meta:
        model = Business
        fields = (
            'title',
            'title_ur',
            'category',
            'locality',
            'address',
            'landmark',
            'phone_number',
            'email',
            'website',
            'whatsapp_number',
            'operating_hours',
            'registration_number',
            'source_url',
            'summary',
            'description',
            'primary_image',
        )
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Butt Karahi or Gulberg Solar Solutions'}),
            'title_ur': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'اردو نام (اختیاری)'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Street address, shop/plaza number, floor'}),
            'landmark': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Near Siddique Trade Centre, Opposite Liberty Market'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. +92-42-35789901 or 0300-1234567'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'info@yourbusiness.pk'}),
            'website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://www.yourbusiness.pk'}),
            'whatsapp_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. +923001234567'}),
            'operating_hours': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Mon-Sat: 10:00 AM - 9:00 PM, Sun: Closed'}),
            'registration_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. SECP CUIN / LCCI Membership No.'}),
            'source_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://lcci.com.pk/directory or social/register proof URL'}),
            'summary': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Concise 1-2 sentence overview for directory cards...'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Detailed business profile, services offered, history, products, and specialties...'}),
            'primary_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'title': 'Business Name (English) *',
            'title_ur': 'Business Name (Urdu)',
            'category': 'Category *',
            'locality': 'Locality / Area *',
            'address': 'Physical Address *',
            'landmark': 'Nearby Landmark',
            'phone_number': 'Official Telephone / Mobile *',
            'email': 'Official Email Address',
            'website': 'Official Website (https://)',
            'whatsapp_number': 'Customer WhatsApp Contact',
            'operating_hours': 'Operating Timings',
            'registration_number': 'SECP / Chamber Registration No.',
            'source_url': 'Verification Source URL',
            'summary': 'Short Overview Summary *',
            'description': 'Comprehensive Description *',
            'primary_image': 'Storefront Banner / Logo (Max 5MB)',
        }

    def clean_primary_image(self):
        image = self.cleaned_data.get('primary_image')
        if image:
            if hasattr(image, 'size') and image.size > 5 * 1024 * 1024:
                raise ValidationError('Image file size cannot exceed 5MB.')
            validate_image_extension(image)
        return image

    def clean_website(self):
        website = self.cleaned_data.get('website')
        if website:
            validator = URLValidator(schemes=['http', 'https'])
            try:
                validator(website)
            except ValidationError:
                raise ValidationError('Please enter a valid website URL starting with http:// or https://.')
        return website

    def clean_source_url(self):
        source_url = self.cleaned_data.get('source_url')
        if source_url:
            validator = URLValidator(schemes=['http', 'https'])
            try:
                validator(source_url)
            except ValidationError:
                raise ValidationError('Please enter a valid source URL starting with http:// or https://.')
        return source_url


class BusinessEditForm(forms.ModelForm):
    """
    Direct edit form for business owners updating unpublished drafts.
    Guarantees that sensitive status and privilege flags cannot be modified.
    """
    category = forms.ModelChoiceField(
        queryset=BusinessCategory.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    locality = forms.ModelChoiceField(
        queryset=Locality.objects.all().select_related('zone').order_by('zone__name', 'name'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Business
        fields = (
            'title',
            'title_ur',
            'category',
            'locality',
            'address',
            'landmark',
            'phone_number',
            'email',
            'website',
            'whatsapp_number',
            'operating_hours',
            'registration_number',
            'summary',
            'description',
            'primary_image',
        )
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'title_ur': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'landmark': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'whatsapp_number': forms.TextInput(attrs={'class': 'form-control'}),
            'operating_hours': forms.TextInput(attrs={'class': 'form-control'}),
            'registration_number': forms.TextInput(attrs={'class': 'form-control'}),
            'summary': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'primary_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def clean_primary_image(self):
        image = self.cleaned_data.get('primary_image')
        if image:
            if hasattr(image, 'size') and image.size > 5 * 1024 * 1024:
                raise ValidationError('Image file size cannot exceed 5MB.')
            validate_image_extension(image)
        return image

    def clean_website(self):
        website = self.cleaned_data.get('website')
        if website:
            validator = URLValidator(schemes=['http', 'https'])
            try:
                validator(website)
            except ValidationError:
                raise ValidationError('Please enter a valid website URL starting with http:// or https://.')
        return website


class BusinessEditRequestForm(forms.ModelForm):
    """
    Form for owners of published businesses to submit modifications.
    Changes enter an audit queue as a BusinessEditRequest, ensuring published records
    are never altered without editorial moderation.
    """
    class Meta:
        model = BusinessEditRequest
        fields = (
            'title',
            'summary',
            'description',
            'address',
            'phone_number',
            'website',
            'operating_hours',
        )
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'summary': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'operating_hours': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'title': 'Business Title *',
            'summary': 'Short Summary *',
            'description': 'Full Description *',
            'address': 'Physical Address *',
            'phone_number': 'Phone Number',
            'website': 'Official Website (https://)',
            'operating_hours': 'Operating Timings',
        }

    def clean_website(self):
        website = self.cleaned_data.get('website')
        if website:
            validator = URLValidator(schemes=['http', 'https'])
            try:
                validator(website)
            except ValidationError:
                raise ValidationError('Please enter a valid website URL starting with http:// or https://.')
        return website


class BusinessReportForm(forms.ModelForm):
    """
    Public form for reporting inaccuracies, closures, or fraudulent entries.
    """
    class Meta:
        model = BusinessReport
        fields = ('reporter_name', 'reporter_email', 'reason', 'details')
        widgets = {
            'reporter_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Full Name'}),
            'reporter_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'name@example.com'}),
            'reason': forms.Select(attrs={'class': 'form-select'}),
            'details': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Please specify the exact discrepancy (e.g. incorrect phone number, permanently closed, relocated to new plaza, etc.). Provide evidence or alternate contact if available.'
            }),
        }
        labels = {
            'reporter_name': 'Your Name *',
            'reporter_email': 'Your Email Address *',
            'reason': 'Primary Issue *',
            'details': 'Details & Evidence *',
        }

    def clean_details(self):
        details = self.cleaned_data.get('details', '').strip()
        if len(details) < 10:
            raise ValidationError('Please provide a detailed explanation (at least 10 characters) to help our verification desk.')
        return details


class BusinessClaimForm(forms.ModelForm):
    """
    Form for verified business owners or executives to claim their business.
    """
    class Meta:
        model = BusinessClaim
        fields = ('claimant_role', 'official_email', 'contact_phone', 'proof_document')
        widgets = {
            'claimant_role': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Managing Director, Founder, General Manager'}),
            'official_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'official@yourcompany.pk'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+92-300-1234567'}),
            'proof_document': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'claimant_role': 'Your Official Role / Title *',
            'official_email': 'Official Business Email *',
            'contact_phone': 'Direct Verification Phone *',
            'proof_document': 'Proof Document (Visiting Card, Utility Bill, SECP Certificate)',
        }

    def clean_proof_document(self):
        doc = self.cleaned_data.get('proof_document')
        if doc and hasattr(doc, 'name'):
            if hasattr(doc, 'size') and doc.size > 10 * 1024 * 1024:
                raise ValidationError("Proof document file size cannot exceed 10MB.")
            ext = os.path.splitext(doc.name)[1].lower()
            valid_exts = ['.pdf', '.jpg', '.jpeg', '.png', '.webp']
            if ext not in valid_exts:
                raise ValidationError(f"Unsupported file format '{ext}'. Allowed document formats: PDF, JPG, PNG, WEBP.")
        return doc



class BusinessPromotionRequestForm(forms.ModelForm):
    """
    Business owner promotion request form for Lahore City Hub sponsorship campaigns.
    Strictly collects campaign coordination parameters without requesting live payment cards.
    """
    class Meta:
        model = BusinessPromotionRequest
        fields = ('target_tier', 'duration_days', 'contact_phone', 'contact_email', 'campaign_goals')
        widgets = {
            'target_tier': forms.Select(attrs={'class': 'form-select'}),
            'duration_days': forms.Select(attrs={'class': 'form-select'}),
            'contact_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. +92-300-1234567 or 042-35789901'
            }),
            'contact_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'accounts@yourbusiness.pk'
            }),
            'campaign_goals': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Tell our team about your campaign objectives, special deals, or preferred launch dates (optional).'
            }),
        }
        labels = {
            'target_tier': 'Select Promotion Tier *',
            'duration_days': 'Campaign Duration *',
            'contact_phone': 'Coordination Phone / WhatsApp *',
            'contact_email': 'Billing Coordination Email *',
            'campaign_goals': 'Promotion Campaign Notes (Optional)',
        }

    def clean_contact_phone(self):
        phone = self.cleaned_data.get('contact_phone', '').strip()
        if len(phone) < 8:
            raise ValidationError('Please enter a valid telephone or WhatsApp contact number.')
        return phone

