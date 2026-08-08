from django.shortcuts import render, redirect, get_list_or_404, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q, Count
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from functools import wraps
from .models import District, Province
from listings.models import Listing, Document
from accounts.models import User

def home(request):
    listings = Listing.objects.filter(status="approved").select_related(
        "province", "district", "facilities"
    ).prefetch_related("images")

    query = request.GET.get("q", "")
    if query:
        listings = listings.filter(
            Q(title__icontains=query) |
            Q(city__icontains=query) |
            Q(area__icontains=query) |
            Q(description__icontains=query)
        )

    province_id = request.GET.get("province", "")
    district_id = request.GET.get("district", "")
    property_type = request.GET.get("property_type", "")
    min_price = request.GET.get("min_price", "")
    max_price = request.GET.get("max_price", "")

    if province_id:
        listings = listings.filter(province_id=province_id)
    if district_id:
        listings = listings.filter(district_id=district_id)
    if property_type:
        listings = listings.filter(property_type=property_type)
    if min_price:
        listings = listings.filter(monthly_rent__gte=min_price)
    if max_price:
        listings = listings.filter(monthly_rent__lte=max_price)

    sort = request.GET.get("sort", "latest")
    if sort == "price_low":
        listings = listings.order_by("monthly_rent")
    elif sort == "price_high":
        listings = listings.order_by("-monthly_rent")
    else:
        listings = listings.order_by("-created_at")

    provinces = Province.objects.all()
    districts = District.objects.filter(
        province_id=province_id
    ) if province_id else District.objects.none()

    context = {
        "listings": listings,
        "provinces": provinces,
        "districts": districts,
        "query": query,
        "selected_province": province_id,
        "selected_district": district_id,
        "selected_property_type": property_type,
        "min_price": min_price,
        "max_price": max_price,
        "sort": sort,
        "property_types": Listing.PROPERTY_TYPE_CHOICES,
        # Stats bar
        "total_listings_all": Listing.objects.filter(status="approved").count(),
        "total_districts": District.objects.count(),
        "verified_landlords": User.objects.filter(
            role="landlord", documents__verification_status="approved"
        ).count(),
        "total_tenants": User.objects.filter(role="tenant").count(),
    }
    return render(request, "core/home.html", context)


def get_districts(request):
    province_id = request.GET.get("province_id")
    if not province_id:
        return JsonResponse({"districts": []})
    districts = District.objects.filter(
        province_id= province_id
    ).values("id", "name")
    return JsonResponse({"districts": list(districts)})

def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")
        if request.user.role != "admin" and not request.user.is_staff:
            messages.error(request, "You do not have permission to access this page.")
            return redirect("home")
        return view_func(request, *args, **kwargs)
    return wrapper

@admin_required
def dashboard_home(request):
    context = {
        "total_listings": Listing.objects.count(),
        "pending_listings": Listing.objects.filter(status="pending").count(),
        "approved_listings": Listing.objects.filter(status="approved").count(),
        "rejected_listings": Listing.objects.filter(status="rejected").count(),
        "total_users": User.objects.count(),
        "total_landlords": User.objects.filter(role="landlord").count(),
        "total_tenants": User.objects.filter(role="tenant").count(),
        "recent_listings": Listing.objects.select_related(
            "owner", "province", "district"
        ).order_by("-created_at")[:5],
    }
    return render(request, "core/dashboard/home.html", context)

@admin_required
def dashboard_pending(request):
    listings = Listing.objects.filter(
        status="pending"
    ).select_related("owner", "province", "district").order_by("-created_at")
    return render(request, "core/dashboard/pending.html", {"listings": listings})


@admin_required
def dashboard_approved(request):
    listings = Listing.objects.filter(
        status="approved"
    ).select_related("owner", "province", "district").order_by("-created_at")
    return render(request, "core/dashboard/approved.html", {"listings": listings})

@admin_required
def dashboard_rejected(request):
    listings = Listing.objects.filter(
        status="rejected"
    ).select_related("owner", "province", "district").order_by("-created_at")
    return render(request, "core/dashboard/rejected.html", {"listings": listings})

@admin_required
def dashboard_review_listing(request, pk):
    listing = get_object_or_404(
        Listing.objects.select_related(
            "owner", "province", "district"
        ).prefetch_related("images"),
        pk=pk
    )
    document = None
    try:
        document = listing.owner.documents
    except:
        pass

    facilities = None
    try:
        facilities = listing.facilities
    except:
        pass

    return render(request, "core/dashboard/review.html", {
        "listing": listing,
        "document": document,
        "facilities": facilities,
    })

@admin_required
def dashboard_approve_listing(request, pk):
    if request.method != "POST":
        return redirect("dashboard_review_listing", pk=pk)

    listing = get_object_or_404(Listing, pk=pk)
    verified_owner = request.POST.get("verified_owner") == "on"
    verified_property = request.POST.get("verified_property") == "on"

    listing.status = "approved"
    listing.verified_owner = verified_owner
    listing.verified_property = verified_property
    listing.rejection_reason = ""
    listing.save()

    try:
        listing.owner.documents.verification_status = "approved"
        listing.owner.documents.save()
    except Document.DoesNotExist:
        pass

    messages.success(request, f"Listing '{listing.title}' has been approved.")
    return redirect("dashboard_pending")


@admin_required
def dashboard_reject_listing(request, pk):
    if request.method != "POST":
        return redirect("dashboard_review_listing", pk=pk)

    listing = get_object_or_404(Listing, pk=pk)
    reason = request.POST.get("reason", "").strip()

    if not reason:
        messages.error(request, "Please provide a rejection reason.")
        return redirect("dashboard_review_listing", pk=pk)

    listing.status = "rejected"
    listing.rejection_reason = reason
    listing.verified_owner = False
    listing.verified_property = False
    listing.save()

    try:
        listing.owner.documents.verification_status = "rejected"
        listing.owner.documents.save()
    except:
        pass

    messages.success(request, f"Listing '{listing.title}' has been rejected.")
    return redirect("dashboard_pending")

@admin_required
def dashboard_users(request):
    users = User.objects.all().order_by("-date_joined")
    return render(request, "core/dashboard/users.html", {"users": users})


@admin_required
def dashboard_toggle_user(request, pk):
    if request.method != "POST":
        return redirect("dashboard_users")
    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        messages.error(request, "You cannot deactivate your own account.")
        return redirect("dashboard_users")
    user.is_active = not user.is_active
    user.save()
    status = "activated" if user.is_active else "deactivated"
    messages.success(request, f"User {user.email} has been {status}.")
    return redirect("dashboard_users")

def browse_rooms(request):
    listings = Listing.objects.filter(status="approved").select_related(
        "province", "district", "facilities"
    ).prefetch_related("images")

    query = request.GET.get("q", "")
    if query:
        listings = listings.filter(
            Q(title__icontains=query) |
            Q(city__icontains=query) |
            Q(area__icontains=query) |
            Q(description__icontains=query)
        )

    province_id = request.GET.get("province", "")
    district_id = request.GET.get("district", "")
    property_type = request.GET.get("property_type", "")
    min_price = request.GET.get("min_price", "")
    max_price = request.GET.get("max_price", "")

    if province_id:
        listings = listings.filter(province_id=province_id)
    if district_id:
        listings = listings.filter(district_id=district_id)
    if property_type:
        listings = listings.filter(property_type=property_type)
    if min_price:
        listings = listings.filter(monthly_rent__gte=min_price)
    if max_price:
        listings = listings.filter(monthly_rent__lte=max_price)

    sort = request.GET.get("sort", "latest")
    if sort == "price_low":
        listings = listings.order_by("monthly_rent")
    elif sort == "price_high":
        listings = listings.order_by("-monthly_rent")
    else:
        listings = listings.order_by("-created_at")

    provinces = Province.objects.all()
    districts = District.objects.filter(
        province_id=province_id
    ) if province_id else District.objects.none()

    context = {
        "listings": listings,
        "provinces": provinces,
        "districts": districts,
        "query": query,
        "selected_province": province_id,
        "selected_district": district_id,
        "selected_property_type": property_type,
        "min_price": min_price,
        "max_price": max_price,
        "sort": sort,
        "property_types": Listing.PROPERTY_TYPE_CHOICES,
    }
    return render(request, "core/browse.html", context)
