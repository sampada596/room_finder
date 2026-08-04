from django.contrib import admin
from .models import Listing, Facilities, ListingImage, Document, Favorite, Report

class FacilitiesInline(admin.StackedInline):
    model = Facilities
    extra = 0

class ListingImageInline(admin.TabularInline):
    model = ListingImage
    extra = 0

@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "property_type", "status", "verified_owner", "verified_property", "created_at")
    list_filter = ("status", "property_type", "province__name")
    search_fields = ("title", "owner__email", "city")
    inlines = [FacilitiesInline, ListingImageInline]

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("user", "verification_status", "submitted_at", "reviewed_at")
    list_filter = ("verification_status",)

from .models import Listing, Facilities, ListingImage, Document, Favorite, Report

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("listing", "reporter", "reason", "is_reviewed", "created_at")
    list_filter = ("reason", "is_reviewed")
    actions = ["mark_reviewed"]

    def mark_reviewed(self, request, queryset):
        queryset.update(is_reviewed=True)
    mark_reviewed.short_description = "Mark selected reports as reviewed"
