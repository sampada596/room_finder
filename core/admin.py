from django.contrib import admin
from .models import Province, District

@admin.register(Province)
class ProvinceAdmin(admin.ModelAdmin):
    list_display = ("name", "order")

@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ("name", "province")
    list_filter = ("province",)
