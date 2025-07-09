from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm as BasePasswordChangeForm
from django.core.exceptions import ValidationError
from decimal import Decimal
from .models import User, UserProfile, UserVerification


class UserRegistrationForm(UserCreationForm):
    """User registration form"""

    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    phone_number = forms.CharField(max_length=20, required=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone_number', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("User with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone_number = self.cleaned_data.get('phone_number', '')
        if commit:
            user.save()
        return user


class UserProfileForm(forms.ModelForm):
    """User profile form"""

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'avatar', 'bio', 'phone_number',
            'address_line1', 'address_line2', 'city', 'state', 'postal_code', 'country',
            'email_notifications', 'telegram_notifications', 'web_notifications'
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
            'avatar': forms.FileInput(attrs={'accept': 'image/*'}),
        }


class PasswordChangeForm(BasePasswordChangeForm):
    """Custom password change form"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})


class UserVerificationForm(forms.ModelForm):
    """User verification form"""

    class Meta:
        model = UserVerification
        fields = ['verification_type', 'verification_data']
        widgets = {
            'verification_data': forms.Textarea(attrs={'rows': 3}),
        }


class BalanceAddForm(forms.Form):
    """Form for adding balance"""

    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('0.01'),
        max_value=Decimal('10000.00'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': 'Enter amount'
        })
    )

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount <= 0:
            raise ValidationError("Amount must be positive.")
        if amount > 10000:
            raise ValidationError("Maximum amount is $10,000 per transaction.")
        return amount
