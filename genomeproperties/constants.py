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


class PropertyType:
    CATEGORY = "CATEGORY"
    ROOT = "ROOT"
    SUMMARY = "SUMMARY"
    SKIPPED = frozenset({CATEGORY, ROOT, SUMMARY})


class AssignmentMode:
    SIGNATURES = "signatures"
    ENTRIES = "entries"


class AssignmentResult:
    YES = "YES"
    PARTIAL = "PARTIAL"
    NO = "NO"
    TOTAL = "TOTAL"


class UploadLimit:
    MEGABYTE = 1024 * 1024
    MAX_BYTES = 50 * MEGABYTE
    BINARY_PROBE_BYTES = 4096
    ORGANISM_LABEL_MAX = 80
    DEFAULT_ORGANISM = "upload"
    GZIP_MAGIC = b"\x1f\x8b"


class InterProTsv:
    """Column layout shared by InterProScan TSV and InterPro entry exports."""

    COMMENT = "#"
    HEADER_ACCESSION = "Accession"
    HEADER_NAME = "Name"
    MISSING_SIGNATURE = "-"
    PANTHER_PREFIX = "PTHR"
    SIGNATURE_INDEX = 4
    MIN_SIGNATURE_COLUMNS = 5
    MIN_SCAN_COLUMNS = 11
    MD5_INDEX = 1
    LENGTH_INDEX = 2
    START_INDEX = 6
    STOP_INDEX = 7


class ErrorMessage:
    NOT_FOUND = "Not found"
    ASSIGN_EMPTY = (
        "Upload an InterProScan TSV or an InterPro entry export (file field or ipprotsv)."
    )
    ASSIGN_NOT_LOADED = (
        "Genome Properties data is not loaded. Set DATABASE_PATH to the SQLite database."
    )
    ASSIGN_FILE_EMPTY = "This file is empty."
    ASSIGN_GZIP_INVALID = "This gzipped file could not be read."
    ASSIGN_DECOMPRESSED_TOO_LARGE = "The decompressed file is larger than the upload limit."
    ASSIGN_BINARY = "This looks like a binary file, not a tab-separated text file."
    ASSIGN_UNKNOWN_FORMAT = (
        "This is not an InterProScan TSV or an InterPro entry export. "
        "Upload InterProScan TSV (interproscan.sh -f tsv) or the InterPro "
        "proteome Entries matching TSV."
    )

    @staticmethod
    def assign_file_too_large(size: int) -> str:
        return (
            f"This file is {size / UploadLimit.MEGABYTE:.1f} MB. "
            f"The limit is {UploadLimit.MAX_BYTES // UploadLimit.MEGABYTE} MB."
        )


class OpenApiTag:
    HEALTH = "Health"
    GENOME_PROPERTIES = "Genome properties"
    HIERARCHY = "Hierarchy"
    ASSIGNMENT = "Assignment"
