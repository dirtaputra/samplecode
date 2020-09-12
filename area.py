from django.db.models import F, Q, Value
from django.db.models.functions import Concat

from bolu.models.area import Village, Subdistrict

class AreaService:
    """AreaService."""

    def get_custom_village(self, area):
        """Get custom area."""
        return Village.objects.filter(Q(subdistrict__name=area) | Q(subdistrict__city__name=area))\
            .values(village_id=F("id"), subdistrict_name=F("subdistrict__name"),
            city=F("subdistrict__city__name"), province=F("subdistrict__city__province__name"))

    def get_custom_subdistrict(self, area):
        """Get custom subdistrict."""
        return Subdistrict.objects.filter(Q(name__icontains=area) | Q(city__name__icontains=area))\
            .values(subdistrict_id=F("id"), subdistrict_name=F("name"), city_name=F("city__name"),
            province=F("city__province__name"))

    def get_by_subdistrict(self, id):
        """Get by subdistrict."""
        return Subdistrict.objects.filter(Q(id=id))\
            .values(subdistrict_id=F("id"), subdistrict_name=F("name"), city_name=F("city__name"),
            province=F("city__province__name"))

    def get_custom_area(self, area):
        """Get custom area."""
        return Village.objects.filter(Q(subdistrict__name=area) | Q(subdistrict__city__name=area))\
            .values(village_id=F("id"), village=F("name"), subdistrict_name=F("subdistrict__name"),\
            city=F("subdistrict__city__name"), province=F("subdistrict__city__province__name"))

    def get_city_subdistrict(self, keyword):
        """Get City Subdistrict."""
        return Subdistrict.objects.select_related('city').filter(Q(name__icontains=keyword) | Q(city__name__icontains=keyword))


area_service = AreaService()
