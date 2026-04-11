from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import User, PatientProfile, DoctorProfile

class UserRegistrationForm(UserCreationForm):
    REGISTRATION_ROLES = (
        ('patient', 'Patient'),
        ('doctor', 'Doctor'),
    )
    email = forms.EmailField(required=True, help_text="Only Gmail accounts are allowed (must end with @gmail.com)")
    role = forms.ChoiceField(choices=REGISTRATION_ROLES, required=True)
    phone = forms.CharField(max_length=20, required=False)
    doctor_certificate = forms.FileField(required=False, widget=forms.FileInput(attrs={'accept': 'application/pdf,image/*'}))
    
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'role', 'phone', 'doctor_certificate', 'password1', 'password2')
    
    def clean_doctor_certificate(self):
        role = self.cleaned_data.get('role')
        certificate = self.cleaned_data.get('doctor_certificate')
        if role == 'doctor' and not certificate:
            raise ValidationError('Doctor certificate is required for doctor registration.')
        return certificate
    
    def clean_email(self):
        email = self.cleaned_data.get('email').lower()
        if not email.endswith('@gmail.com'):
            raise ValidationError('Only Gmail accounts are allowed. Please use an email ending with @gmail.com')
        
        # Check if email already exists (case-insensitive)
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('An account with this email already exists. Please use a different email or sign in.')
        return email
    
    def save(self, commit=True):
        user = super().save(commit=False)  # This handles password properly
        user.email = self.cleaned_data['email']
        user.username = self.cleaned_data['email']  # Set username to email for compatibility
        user.role = self.cleaned_data['role']
        user.phone = self.cleaned_data['phone']
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')
        if commit:
            user.save()
        return user

class PatientProfileForm(forms.ModelForm):
    class Meta:
        model = PatientProfile
        fields = ['date_of_birth', 'gender', 'address']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }

class DoctorProfileForm(forms.ModelForm):
    class Meta:
        model = DoctorProfile
        fields = ['specialization', 'qualification', 'experience_years', 'license_number', 'consultation_fee', 'bio', 'is_available']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        }

class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField(required=True, help_text="Only Gmail accounts are allowed (must end with @gmail.com)")
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'avatar']
        widgets = {
            'avatar': forms.FileInput(attrs={'accept': 'image/*'}),
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email').lower()
        if not email.endswith('@gmail.com'):
            raise ValidationError('Only Gmail accounts are allowed. Please use an email ending with @gmail.com')
        
        # If the email hasn't changed, it's definitely valid
        if self.instance and self.instance.email and email == self.instance.email.lower():
            return email
            
        # Check if email already exists for another user
        if User.objects.filter(email__iexact=email).exclude(id=self.instance.id).exists():
            raise ValidationError('An account with this email already exists.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        # Keep username in sync with email
        user.username = user.email
        if commit:
            user.save()
        return user
