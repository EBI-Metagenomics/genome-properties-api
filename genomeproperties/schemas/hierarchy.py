from .common import APISchema


class HierarchyNodeSchema(APISchema):
    accession: str
    description: str
    children: list["HierarchyNodeSchema"] = []


HierarchyNodeSchema.model_rebuild()
