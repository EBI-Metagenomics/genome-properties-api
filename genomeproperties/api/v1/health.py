from django.http import JsonResponse
from ninja import NinjaAPI, Router

from genomeproperties.constants import OpenApiTag
from genomeproperties.schemas import HealthSchema
from genomeproperties.services import HealthService


class HealthAPI:
    def __init__(self, service: HealthService | None = None):
        self.service = service or HealthService()

    def as_django_view(self):
        def view(request):
            payload = self.service.status()
            return JsonResponse(payload.model_dump())

        return view

    def register(self, api: NinjaAPI) -> None:
        router = Router(tags=[OpenApiTag.HEALTH], by_alias=True)
        service = self.service

        @router.get("/health", response=HealthSchema, summary="Liveness probe")
        def get_health(request) -> HealthSchema:
            return service.status()

        api.add_router("", router)
