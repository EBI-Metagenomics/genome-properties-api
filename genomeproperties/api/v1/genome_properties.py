from ninja import NinjaAPI, Query, Router
from ninja.errors import HttpError

from genomeproperties.constants import ErrorMessage, OpenApiTag
from genomeproperties.schemas import (
    ErrorSchema,
    GenomePropertyDetailSchema,
    GenomePropertySummarySchema,
)
from genomeproperties.services import GenomePropertyService


class GenomePropertyAPI:
    def __init__(self, service: GenomePropertyService | None = None):
        self.service = service or GenomePropertyService()

    def register(self, api: NinjaAPI) -> None:
        router = Router(tags=[OpenApiTag.GENOME_PROPERTIES], by_alias=True)
        service = self.service

        @router.get(
            "/genome-properties",
            response=list[GenomePropertySummarySchema],
            summary="List genome properties",
            description="Optionally filter by type such as PATHWAY, CATEGORY, or SYSTEM.",
        )
        def list_properties(
            request,
            property_type: str | None = Query(
                None, alias="type", description="Property type, e.g. PATHWAY"
            ),
        ) -> list[GenomePropertySummarySchema]:
            return service.list_by_type(property_type)

        @router.get(
            "/genome-properties/{accession}",
            response={200: GenomePropertyDetailSchema, 404: ErrorSchema},
            summary="Get a genome property",
            description="Literature, database links, and steps for one accession.",
        )
        def get_property(request, accession: str) -> GenomePropertyDetailSchema:
            payload = service.get(accession)
            if payload is None:
                raise HttpError(404, ErrorMessage.NOT_FOUND)
            return payload

        api.add_router("", router)
