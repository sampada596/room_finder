from django.shortcuts import render, redirect
from django.contrib import messages
from django.forms import ValidationError
from django.utils import timezone
from functools import wraps
from .forms import (
    BasicInfoForm, LocationForm, PricingForm, FacilitiesForm,
    DocumentForm, ListingImageForm
)
from .models import Listing, Facilities, ListingImage, Document, Favorite, Report, RentalRequest
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required


def landlord_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")
        if request.user.role != "landlord":
            messages.error(request, "Only landlords can access this page.")
            return redirect("login")
        return view_func(request, *args, **kwargs)
    return wrapper


@landlord_required
def listing_step1(request):
    if request.method == "POST":
        form = BasicInfoForm(request.POST)
        if form.is_valid():
            request.session["listing_step1"] = form.cleaned_data
            return redirect("listing_step2")
    else:
        initial = request.session.get("listing_step1", {})
        form = BasicInfoForm(initial=initial)
    return render(request, "listings/step1.html", {"form": form, "step": 1})


@landlord_required
def listing_step2(request):
    if "listing_step1" not in request.session:
        return redirect("listing_step1")
    if request.method == "POST":
        form = LocationForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            request.session["listing_step2"] = {
                "province": data["province"].id,
                "district": data["district"].id,
                "city": data["city"],
                "area": data["area"],
                "ward_number": data["ward_number"],
                "address": data["address"],
                "latitude": str(data["latitude"]) if data["latitude"] else None,
                "longitude": str(data["longitude"]) if data["longitude"] else None,
            }
            return redirect("listing_step3")
    else:
        initial = request.session.get("listing_step2", {})
        form = LocationForm(initial=initial)
    return render(request, "listings/step2.html", {"form": form, "step": 2})


@landlord_required
def listing_step3(request):
    if "listing_step2" not in request.session:
        return redirect("listing_step2")
    if request.method == "POST":
        form = PricingForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            request.session["listing_step3"] = {
                "monthly_rent": data["monthly_rent"],
                "security_deposit": data["security_deposit"],
                "bills_water": data["bills_water"],
                "bills_electricity": data["bills_electricity"],
                "bills_internet": data["bills_internet"],
                "available_date": str(data["available_date"]) if data["available_date"] else None,
                "house_rules": data["house_rules"],
            }
            return redirect("listing_step4")
    else:
        initial = request.session.get("listing_step3", {})
        form = PricingForm(initial=initial)
    return render(request, "listings/step3.html", {"form": form, "step": 3})


@landlord_required
def listing_step4(request):
    if "listing_step3" not in request.session:
        return redirect("listing_step3")
    if request.method == "POST":
        form = FacilitiesForm(request.POST)
        if form.is_valid():
            request.session["listing_step4"] = form.cleaned_data
            return redirect("listing_step5")
    else:
        initial = request.session.get("listing_step4", {})
        form = FacilitiesForm(initial=initial)
    return render(request, "listings/step4.html", {"form": form, "step": 4})


@landlord_required
def listing_step5(request):
    if "listing_step4" not in request.session:
        return redirect("listing_step4")
    if request.method == "POST":
        doc_form = DocumentForm(request.POST, request.FILES)
        image_form = ListingImageForm()
        images = request.FILES.getlist("images")

        try:
            validated_images = image_form.validate_images(images)
            image_error = None
        except ValidationError as e:
            validated_images = None
            image_error = e.message

        if doc_form.is_valid() and validated_images:
            step1 = request.session["listing_step1"]
            step2 = request.session["listing_step2"]
            step3 = request.session["listing_step3"]
            step4 = request.session["listing_step4"]

            listing = Listing.objects.create(
                owner=request.user,
                title=step1["title"],
                description=step1["description"],
                property_type=step1["property_type"],
                province_id=step2["province"],
                district_id=step2["district"],
                city=step2["city"],
                area=step2["area"],
                ward_number=step2["ward_number"],
                address=step2["address"],
                latitude=step2["latitude"],
                longitude=step2["longitude"],
                monthly_rent=step3["monthly_rent"],
                security_deposit=step3["security_deposit"],
                bills_water=step3["bills_water"],
                bills_electricity=step3["bills_electricity"],
                bills_internet=step3["bills_internet"],
                available_date=step3["available_date"],
                house_rules=step3["house_rules"],
                status="pending",
            )

            Facilities.objects.create(listing=listing, **step4)

            for index, image in enumerate(validated_images):
                ListingImage.objects.create(
                    listing=listing,
                    image=image,
                    is_primary=(index == 0),
                )

            Document.objects.update_or_create(
                user=request.user,
                defaults={
                    "citizenship_front": doc_form.cleaned_data["citizenship_front"],
                    "citizenship_back": doc_form.cleaned_data["citizenship_back"],
                    "lalpurja": doc_form.cleaned_data["lalpurja"],
                    "selfie_with_citizenship": doc_form.cleaned_data["selfie_with_citizenship"],
                    "verification_status": "pending",
        
                }
    
            )

            for key in ["listing_step1", "listing_step2", "listing_step3", "listing_step4"]:
                del request.session[key]

            messages.success(request, "Your listing has been submitted for review.")
            return redirect("listing_submitted")
    else:
        doc_form = DocumentForm()
        image_error = None

    return render(request, "listings/step5.html", {
        "doc_form": doc_form,
        "image_error": image_error,
        "step": 5,
    })


@landlord_required
def listing_submitted(request):
    return render(request, "listings/submitted.html")

def listing_detail(request, pk):
    listing = get_object_or_404(
        Listing.objects.select_related(
            "owner", "province", "district"
        ).prefetch_related("images"),
        pk=pk,
        status="approved"
    )

    facilities = None
    try:
        facilities = listing.facilities
    except:
        pass

    phone_revealed = request.session.get(f"phone_revealed_{pk}", False)

    existing_request = None
    if request.user.is_authenticated and request.user.role == "tenant":
        existing_request = RentalRequest.objects.filter(tenant=request.user, listing=listing).first()

    context = {
        "listing": listing,
        "facilities": facilities,
        "phone_revealed": phone_revealed,
        "existing_request": existing_request,
        "masked_phone": listing.owner.phone[:2] + "X" * (len(listing.owner.phone) - 2) if listing.owner.phone else "",

    }
    return render(request, "listings/detail.html", context)

@login_required
def reveal_phone(request, pk):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    
    listing = get_object_or_404(Listing, pk=pk, status="approved")
    request.session[f"phone_revealed_{pk}"] = True
    request.session.modified = True

    return JsonResponse({
        "phone": listing.owner.phone
    })

@login_required
def toggle_favorite(request, pk):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    listing = get_object_or_404(Listing, pk=pk, status="approved")
    favorite, created = Favorite.objects.get_or_create(
        user=request.user,
        listing=listing
    )
    if not created:
        favorite.delete()
        return JsonResponse({"status": "removed"})
    return JsonResponse({"status": "added"})


@login_required
def my_favorites(request):
    favorites = Favorite.objects.filter(
        user=request.user
    ).select_related("listing__province", "listing__district").prefetch_related(
        "listing__images"
    ).order_by("-created_at")
    return render(request, "listings/favorites.html", {"favorites": favorites})


@login_required
def report_listing(request, pk):
    listing = get_object_or_404(Listing, pk=pk, status="approved")
    if request.method == "POST":
        reason = request.POST.get("reason")
        details = request.POST.get("details", "")
        if not reason:
            messages.error(request, "Please select a reason.")
            return redirect("listing_detail", pk=pk)
        _, created = Report.objects.get_or_create(
            reporter=request.user,
            listing=listing,
            defaults={"reason": reason, "details": details}
        )
        if created:
            messages.success(request, "Thank you — your report has been submitted.")
        else:
            messages.info(request, "You have already reported this listing.")
        return redirect("listing_detail", pk=pk)
    return render(request, "listings/report.html", {
        "listing": listing,
        "reasons": Report.REASON_CHOICES
    })


def landlord_dashboard(request):
    if not request.user.is_authenticated:
        return redirect("login")
    if request.user.role != "landlord":
        return redirect("home")

    listings = Listing.objects.filter(
        owner=request.user
    ).prefetch_related("images").order_by("-created_at")

    context = {
        "listings": listings,
        "pending_count": listings.filter(status="pending").count(),
        "approved_count": listings.filter(status="approved").count(),
        "rejected_count": listings.filter(status="rejected").count(),
        "pending_requests_count": RentalRequest.objects.filter(
            listing__owner=request.user, status="pending"
        ).count(),
    }
    return render(request, "listings/landlord_dashboard.html", context)


@login_required
def request_to_rent(request, pk):
    listing = get_object_or_404(Listing, pk=pk, status="approved")

    if request.user.role != "tenant":
        messages.error(request, "Only tenants can request to rent a room.")
        return redirect("listing_detail", pk=pk)

    if listing.owner_id == request.user.id:
        messages.error(request, "You can't request your own listing.")
        return redirect("listing_detail", pk=pk)

    if request.method == "POST":
        message = request.POST.get("message", "").strip()
        obj, created = RentalRequest.objects.get_or_create(
            tenant=request.user,
            listing=listing,
            defaults={"message": message}
        )
        if created:
            messages.success(request, "Your request has been sent to the landlord.")
        else:
            messages.info(request, "You've already requested this room.")

    return redirect("listing_detail", pk=pk)


@login_required
def landlord_requests(request):
    if request.user.role != "landlord":
        messages.error(request, "Only landlords can view rental requests.")
        return redirect("home")

    status_filter = request.GET.get("status", "")
    requests_qs = RentalRequest.objects.filter(
        listing__owner=request.user
    ).select_related("tenant", "listing").order_by("-created_at")

    if status_filter:
        requests_qs = requests_qs.filter(status=status_filter)

    context = {
        "requests": requests_qs,
        "status_filter": status_filter,
        "pending_count": RentalRequest.objects.filter(listing__owner=request.user, status="pending").count(),
        "accepted_count": RentalRequest.objects.filter(listing__owner=request.user, status="accepted").count(),
        "declined_count": RentalRequest.objects.filter(listing__owner=request.user, status="declined").count(),
    }
    return render(request, "listings/landlord_requests.html", context)


@login_required
def respond_to_request(request, pk):
    if request.method != "POST":
        return redirect("landlord_requests")

    rental_request = get_object_or_404(RentalRequest, pk=pk, listing__owner=request.user)
    action = request.POST.get("action")

    if action == "accept":
        rental_request.status = "accepted"
        rental_request.responded_at = timezone.now()
        rental_request.save()
        messages.success(request, f"You accepted {rental_request.tenant.first_name}'s request.")
    elif action == "decline":
        rental_request.status = "declined"
        rental_request.responded_at = timezone.now()
        rental_request.save()
        messages.success(request, f"You declined {rental_request.tenant.first_name}'s request.")

    return redirect("landlord_requests")


@login_required
def my_requests(request):
    if request.user.role != "tenant":
        messages.error(request, "Only tenants can view their rental requests.")
        return redirect("home")

    requests_qs = RentalRequest.objects.filter(
        tenant=request.user
    ).select_related("listing", "listing__district").prefetch_related("listing__images").order_by("-created_at")

    return render(request, "listings/my_requests.html", {"requests": requests_qs})
