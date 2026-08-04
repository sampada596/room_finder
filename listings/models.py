import uuid
from django.db import models
from django.conf import settings
from core.models import Province, District

class Listing(models.Model):

    PROPERTY_TYPE_CHOICES = (
        ("single_room", "Single Room"),
        ("two_rooms", "Two Rooms"),
        ("flat", "Flat"),
        ("apartment", "Apartment"),
        ("house", "House"),
        ("hostel", "Hostel"),
        ("office_space", "Office Space"),
        ("shutter", "Shutter"),
    )

    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="listings"
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPE_CHOICES)

    province = models.ForeignKey(
        Province,
        on_delete=models.SET_NULL,
        null=True,
        related_name="listings"
    )
    district = models.ForeignKey(
        District,
        on_delete=models.SET_NULL,
        null=True,
        related_name="listings"
    )
    city = models.CharField(max_length=100)
    area = models.CharField(max_length=200)
    ward_number = models.CharField(max_length=10, blank=True)
    address = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    monthly_rent = models.PositiveIntegerField()
    security_deposit = models.PositiveIntegerField(default=0)
    bills_water = models.BooleanField(default=False)
    bills_electricity = models.BooleanField(default=False)
    bills_internet = models.BooleanField(default=False)

    available_date = models.DateField(null=True, blank=True)
    house_rules = models.TextField(blank=True)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    rejection_reason = models.TextField(blank=True)

    verified_owner = models.BooleanField(default=False)
    verified_property = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
    
class Facilities(models.Model):
    listing = models.OneToOneField(
        Listing,
        on_delete=models.CASCADE,
        related_name="facilities"
    )
    car_parking = models.BooleanField(default=False)
    bike_parking = models.BooleanField(default=False)
    wifi = models.BooleanField(default=False)
    drinking_water = models.BooleanField(default=False)
    water_24_7 = models.BooleanField(default=False)
    attached_bathroom = models.BooleanField(default=False)
    balcony = models.BooleanField(default=False)
    furnished = models.BooleanField(default=False)
    cctv = models.BooleanField(default=False)
    security_guard = models.BooleanField(default=False)
    pet_allowed = models.BooleanField(default=False)
    laundry = models.BooleanField(default=False)

    def __str__(self):
        return f"Facilities for {self.listing.title}"
    
class ListingImage(models.Model):
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name="images"
    )
    image = models.ImageField(upload_to="listings/images/")
    is_primary = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_primary", "uploaded_at"]

    def __str__(self):
        return f"Image for {self.listing.title}"
    
class Document(models.Model):
    VERIFICATION_STATUS_CHOICES = (
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="documents"
    )
    citizenship_front = models.ImageField(upload_to="documents/citizenship/")
    citizenship_back = models.ImageField(upload_to="documents/citizenship/")
    lalpurja = models.ImageField(upload_to="documents/lalpurja/")
    selfie_with_citizenship = models.ImageField(upload_to="documents/selfie/")
    verification_status = models.CharField(
        max_length=10,
        choices=VERIFICATION_STATUS_CHOICES,
        default="pending"
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Documents for {self.user.email}"

class Favorite(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="favorites"
    )
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name="favorited_by"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "listing")

    def __str__(self):
        return f"{self.user.email} saved {self.listing.title}"

class Report(models.Model):
    REASON_CHOICES = (
        ("fake", "Fake or fraudulent listing"),
        ("wrong_info", "Wrong or misleading information"),
        ("already_rented", "Room already rented"),
        ("spam", "Spam"),
        ("other", "Other"),
    )

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reports"
    )
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name="reports"
    )
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_reviewed = models.BooleanField(default=False)

    class Meta:
        unique_together = ("reporter", "listing")

    def __str__(self):
        return f"Report on {self.listing.title} by {self.reporter.email}"

class RentalRequest(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("declined", "Declined"),
    )
 
    tenant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="rental_requests"
    )
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name="rental_requests"
    )
    message = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
 
    class Meta:
        unique_together = ("tenant", "listing")
        ordering = ["-created_at"]
 
    def __str__(self):
        return f"{self.tenant.email} → {self.listing.title} ({self.status})"




