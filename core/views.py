from django.http import JsonResponse
from .models import District

def get_districts(request):
    province_id = request.GET.get("province_id")
    if not province_id:
        return JsonResponse({"districts": []})
    districts = District.objects.filter(
        province_id= province_id
    ).values("id", "name")
    return JsonResponse({"districts": list(districts)})
