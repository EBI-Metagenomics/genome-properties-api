class ApiMeta:
    TITLE = "Genome Properties API"
    DESCRIPTION = "REST API for the EMBL-EBI Genome Properties resource."
    VERSION = "1.0.0"


class ApiPath:
    VERSION = "v1"
    ROOT = "api/v1"
    SCRIPT_PREFIX = "genomeproperties/api"
    DOCS = "/docs"
    OPENAPI = "/openapi.json"


class HealthStatus:
    OK = "ok"


class ErrorMessage:
    NOT_FOUND = "Not found"


class OpenApiTag:
    HEALTH = "Health"
    GENOME_PROPERTIES = "Genome properties"
    HIERARCHY = "Hierarchy"
