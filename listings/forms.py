from typing import Any

from django import forms
from .models import Listing, Facilities, Document
from core.models import Province, District

class BasicInfoForm(forms.Form):
    title = forms.CharField(
        max_length=255,
        min_length=5,
    )
    description = forms.CharField(
        widget=forms.Textarea,
        min_length=100,
    )
    property_type = forms.ChoiceField(
        choices=Listing.PROPERTY_TYPE_CHOICES
    )
class LocationForm(forms.Form):
    province = forms.ModelChoiceField(
        queryset=Province.objects.all()
    )
    district = forms.ModelChoiceField(
        queryset=District.objects.all()
    )
    city = forms.CharField(max_length=100)
    area = forms.CharField(max_length=200)
    ward_number = forms.CharField(max_length=10, required=False)
    address = forms.CharField(max_length=255)
    latitude = forms.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False,
        widget=forms.HiddenInput()
    )
    longitude = forms.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False,
        widget=forms.HiddenInput()
    )

class PricingForm(forms.Form):
    monthly_rent = forms.IntegerField(min_value=0)
    security_deposit = forms.IntegerField(min_value=0)
    bills_water = forms.BooleanField(required=False)
    bills_electricity = forms.BooleanField(required=False)
    bills_internet = forms.BooleanField(required=False)
    available_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"})
    )
    house_rules = forms.CharField(
        widget=forms.Textarea,
        required=False
    )

class FacilitiesForm(forms.Form):
    car_parking = forms.BooleanField(required=False)
    bike_parking = forms.BooleanField(required=False)
    wifi = forms.BooleanField(required=False)
    drinking_water = forms.BooleanField(required=False)
    water_24_7 = forms.BooleanField(required=False)
    attached_bathroom = forms.BooleanField(required=False)
    balcony = forms.BooleanField(required=False)
    furnished = forms.BooleanField(required=False)
    cctv = forms.BooleanField(required=False)
    security_guard = forms.BooleanField(required=False)
    pet_allowed = forms.BooleanField(required=False)
    laundry = forms.BooleanField(required=False)

class DocumentForm(forms.Form):
    citizenship_front = forms.ImageField()
    citizenship_back = forms.ImageField()
    lalpurja = forms.ImageField()
    selfie_with_citizenship = forms.ImageField()

    def clean_citizenship_front(self):
        return self._validate_image(self.cleaned_data["citizenship_front"])
    
    def clean_citizenship_back(self):
        return self._validate_image(self.cleaned_data["citizenship_back"])
    
    def clean_lalpurja(self):
        return self._validate_image(self.cleaned_data["lalpurja"])
    
    def clean_selfie_with_citizenship(self):
        return self._validate_image(self.cleaned_data["selfie_with_citizenship"])
    
    def _validate_image(self, image):
        if image:
            if image.size > 5 * 1024 * 1024:
                raise forms.ValidationError("Image must be under 5MB.")
            if not image.content_type in ["image/jpeg", "image/png"]:
                raise forms.ValidationError("Only JPG and PNG files are allowed.")
        return image
    
class ListingImageForm(forms.Form):
    def validate_images(self, files):
        if len(files) < 3:
            raise forms.ValidationError("Please upload at least 3 images.")
        if len(files) > 15:
            raise forms.ValidationError("You can upload a maximum of 15 images.")
        for image in files:
            if image.size > 5 * 1024 * 1024:
                raise forms.ValidationError(f"{image.name} exceeds the 5MB limit.")
            if image.content_type not in ["image/jpeg", "image/png"]:
                raise forms.ValidationError(f"{image.name} must be JPG or PNG.")
        return files
    





