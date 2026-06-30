import re
from django import forms
from .models import User

class RegistrationForm(forms.Form):
    first_name = forms.CharField(min_length=2, max_length=100)
    last_name = forms.CharField(min_length=2, max_length=100)
    email = forms.EmailField()
    phone = forms.CharField(max_length=20)
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email
    
    def clean_phone(self):
        phone = self.cleaned_data["phone"]
        if not re.match(r"^9\d{9}$", phone):
            raise forms.ValidationError("Enter a valid Nepal phone number")
        return phone
    
    def clean_password(self):
        password = self.cleaned_data["password"]
        if len(password) < 8:
            raise forms.ValidationError("Password must be at least 8 characters long.")
        if not re.search(r"[A-Z]", password):
            raise forms.ValidationError("Password must contain at least one uppercase letter.")
        if not re.search(r"[0-9]", password):
            raise forms.ValidationError("Password must contain at least one number.")
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data
