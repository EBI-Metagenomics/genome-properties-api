from .common import APISchema


class GenomePropertySummarySchema(APISchema):
    accession: str
    description: str


class LiteratureSchema(APISchema):
    pmid: int
    title: str | None = None
    author: str | None = None
    journal: str | None = None
    list_order: int


class DatabaseLinkSchema(APISchema):
    db_id: str
    db_link: str
    comment: str | None = None
    other_params: str | None = None


class StepEvidenceSchema(APISchema):
    interpro_acc: str
    signature_acc: str
    go_id: str | None = None


class StepSchema(APISchema):
    step_id: str
    step_number: int
    required: int
    child_accession: str | None = None
    evidence: list[StepEvidenceSchema] = []


class GenomePropertyDetailSchema(APISchema):
    accession: str
    type: str
    author: str
    description: str
    threshold: int
    comment: str | None = None
    literature: list[LiteratureSchema] = []
    database_links: list[DatabaseLinkSchema] = []
    steps: list[StepSchema] = []
