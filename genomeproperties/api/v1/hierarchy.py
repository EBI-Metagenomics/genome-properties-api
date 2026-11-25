from ninja import NinjaAPI, Router
from ninja.errors import HttpError

from genomeproperties.constants import ErrorMessage, OpenApiTag
from genomeproperties.schemas import ErrorSchema, HierarchyNodeSchema
from genomeproperties.services import HierarchyService


class HierarchyAPI:
    def __init__(self, service: HierarchyService | None = None):
        self.service = service or HierarchyService()

    def register(self, api: NinjaAPI) -> None:
        router = Router(tags=[OpenApiTag.HIERARCHY], by_alias=True)
        service = self.service

        @router.get(
            "/hierarchy/{accession}",
            response={200: HierarchyNodeSchema, 404: ErrorSchema},
            summary="Get the child-property tree",
            description="CATEGORY properties nested under the given accession.",
        )
        def get_hierarchy(request, accession: str) -> HierarchyNodeSchema:
            tree = service.get_tree(accession)
            if tree is None:
                raise HttpError(404, ErrorMessage.NOT_FOUND)
            return tree

        api.add_router("", router)
