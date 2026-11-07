import os
from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.text import slugify

from .models import UserProfile

User = get_user_model()


class UserRegistrationForm(forms.Form):
    """
    Public registration form for new Lahore City Hub members and business owners.
    Security protections:
    - Restricts selectable roles strictly to 'member' or 'business_owner'
    - Prevents privilege escalation to 'admin' or 'moderator'
    - Enforces Django strong password validation
    - Enforces case-insensitive email uniqueness
    """
    PUBLIC_ROLE_CHOICES = [
        ('member', 'Community Member / Resident (Save places, submit reviews)'),
        ('business_owner', 'Business Owner / Manager (List and manage businesses)'),
    ]

    full_name = forms.CharField(
        max_length=150,
        required=True,
        label="Full Name",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. Ahmad Raza Khan',
            'autocomplete': 'name',
        })
    )
    email = forms.EmailField(
        max_length=254,
        required=True,
        label="Email Address",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. ahmad@example.pk',
            'autocomplete': 'email',
        })
    )
    phone_number = forms.CharField(
        max_length=25,
        required=False,
        label="Phone Number (Optional)",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. +92 300 1234567',
            'autocomplete': 'tel',
        })
    )
    home_locality = forms.CharField(
        max_length=120,
        required=False,
        label="Home Locality (Optional)",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. Johar Town, Gulberg III, DHA',
        })
    )
    role = forms.ChoiceField(
        choices=PUBLIC_ROLE_CHOICES,
        required=True,
        initial='member',
        label="Account Type",
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Minimum 8 characters with letters and numbers',
            'autocomplete': 'new-password',
        })
    )
    confirm_password = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Re-enter your password',
            'autocomplete': 'new-password',
        })
    )
    terms_accepted = forms.BooleanField(
        required=True,
        label="I agree to the Terms of Service & Privacy Policy",
        error_messages={'required': 'You must accept the terms and conditions to register.'},
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email address is already registered.")
        return email

    def clean_role(self):
        role = self.cleaned_data.get('role', 'member')
        allowed_roles = ['member', 'business_owner']
        # Explicitly deny administrator or moderator assignment from user input
        if role not in allowed_roles:
            raise ValidationError("Invalid account type selected. You cannot assign privileged administrative roles.")
        return role

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password:
            if password != confirm_password:
                self.add_error('confirm_password', "The two password fields did not match.")
            else:
                # Apply Django password strength validation
                try:
                    validate_password(password)
                except ValidationError as e:
                    self.add_error('password', e)

        return cleaned_data

    def save(self):
        """Constructs and returns the newly registered CustomUser."""
        email = self.cleaned_data['email']
        full_name = self.cleaned_data['full_name'].strip()
        name_parts = full_name.split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        # Derive a safe unique username
        base_username = slugify(first_name) or email.split('@')[0]
        base_username = base_username.replace('-', '_')[:25]
        username = base_username
        counter = 1
        while User.objects.filter(username__iexact=username).exists():
            username = f"{base_username}_{counter}"
            counter += 1

        user = User.objects.create_user(
            email=email,
            username=username,
            password=self.cleaned_data['password'],
            first_name=first_name,
            last_name=last_name,
            phone_number=self.cleaned_data.get('phone_number', '').strip(),
            role=self.cleaned_data['role'],
            is_staff=False,
            is_superuser=False,
            is_active=True,
            is_verified=False,
        )

        # Update associated profile
        if hasattr(user, 'profile'):
            user.profile.home_locality = self.cleaned_data.get('home_locality', '').strip()
            user.profile.save()

        return user


class UserLoginForm(forms.Form):
    """
    Secure login form supporting authentication by either email address or username.
    Protects against inactive accounts and invalid credentials.
    """
    username_or_email = forms.CharField(
        max_length=254,
        required=True,
        label="Email or Username",
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'e.g. yourname@example.pk',
            'autocomplete': 'username',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        required=True,
        label="Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password',
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        initial=True,
        label="Remember my session on this device",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        username_or_email = cleaned_data.get('username_or_email', '').strip()
        password = cleaned_data.get('password')

        if username_or_email and password:
            self.user_cache = authenticate(
                self.request,
                username=username_or_email,
                password=password
            )
            if self.user_cache is None:
                raise ValidationError("Invalid email/username or password. Please verify your credentials and try again.")
            elif not self.user_cache.is_active:
                raise ValidationError("This account has been disabled. Please contact the administrator.")

        return cleaned_data

    def get_user(self):
        return self.user_cache


class UserProfileForm(forms.ModelForm):
    """
    Profile editing form for the authenticated user.
    Security: Only allows editing non-privileged fields on the user's own profile.
    Validates uploaded avatar images (size <= 5MB and whitelisted formats).
    """
    bio = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Tell the community about yourself or your favorite Lahore neighborhoods...',
        })
    )
    home_locality = forms.CharField(
        max_length=120,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. Model Town, Gulberg, Cantt',
        })
    )
    receive_smog_alerts = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    receive_event_digests = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number', 'avatar']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and hasattr(self.instance, 'profile'):
            profile = self.instance.profile
            self.fields['bio'].initial = profile.bio
            self.fields['home_locality'].initial = profile.home_locality
            self.fields['receive_smog_alerts'].initial = profile.receive_smog_alerts
            self.fields['receive_event_digests'].initial = profile.receive_event_digests

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if avatar and hasattr(avatar, 'size'):
            if avatar.size > 5 * 1024 * 1024:
                raise ValidationError("Profile image size cannot exceed 5MB.")
            ext = os.path.splitext(avatar.name)[1].lower()
            if ext not in ['.jpg', '.jpeg', '.png', '.webp']:
                raise ValidationError("Only JPG, PNG, and WEBP image formats are supported for avatars.")
        return avatar

    def save(self, commit=True):
        user = super().save(commit=commit)
        if hasattr(user, 'profile'):
            profile = user.profile
            profile.bio = self.cleaned_data.get('bio', '')
            profile.home_locality = self.cleaned_data.get('home_locality', '')
            profile.receive_smog_alerts = self.cleaned_data.get('receive_smog_alerts', False)
            profile.receive_event_digests = self.cleaned_data.get('receive_event_digests', False)
            if commit:
                profile.save()
        return user
