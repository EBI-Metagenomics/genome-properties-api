from ninja import File, Form, NinjaAPI, Router, UploadedFile
from ninja.errors import HttpError

from genomeproperties.constants import ErrorMessage, OpenApiTag, UploadLimit
from genomeproperties.schemas import ErrorSchema
from genomeproperties.services.assignment import AssignError, AssignmentService


class AssignAPI:
    def __init__(self, service: AssignmentService | None = None):
        self.service = service or AssignmentService()

    def register(self, api: NinjaAPI) -> None:
        router = Router(tags=[OpenApiTag.ASSIGNMENT], by_alias=True)
        service = self.service

        @router.post(
            "/assign",
            response={200: dict, 400: ErrorSchema},
            summary="Assign genome properties from an InterPro TSV",
            description=(
                "Accepts InterProScan TSV (`interproscan.sh -f tsv`) or an InterPro "
                "proteome 'Entries matching' TSV. Returns the Viewer `web_json` object."
            ),
        )
        def assign(
            request,
            file: UploadedFile = File(None, description="TSV or gzipped TSV"),
            ipproname: str = Form("", description="Heatmap column label, usually the file name"),
            ipprotsv: str = Form("", description="TSV text if not sending a file"),
        ) -> dict:
            raw, name = self._read_upload(request, file, ipproname, ipprotsv)
            try:
                return service.assign_bytes(raw, name)
            except AssignError as exc:
                raise HttpError(400, str(exc)) from exc

        api.add_router("", router)

    @staticmethod
    def _read_upload(
        request,
        file: UploadedFile | None,
        ipproname: str,
        ipprotsv: str,
    ) -> tuple[bytes, str]:
        name = (ipproname or "").strip()
        fallback = UploadLimit.DEFAULT_ORGANISM
        if file is not None:
            return file.read(), name or (file.name or fallback)
        if ipprotsv:
            return ipprotsv.encode("utf-8"), name or fallback
        uploaded = request.FILES.get("file") or request.FILES.get("ipprotsv")
        if uploaded is not None:
            return uploaded.read(), name or (uploaded.name or fallback)
        raise HttpError(400, ErrorMessage.ASSIGN_EMPTY)
