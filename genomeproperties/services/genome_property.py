from collections import defaultdict

from genomeproperties.models import (
    GenomeProperty,
    GpDatabaseLink,
    GpLitRef,
    GpStep,
    GpStepEvidenceGp,
    GpStepEvidenceIpr,
    IprStepToGo,
)
from genomeproperties.schemas import (
    DatabaseLinkSchema,
    GenomePropertyDetailSchema,
    GenomePropertySummarySchema,
    LiteratureSchema,
    StepEvidenceSchema,
    StepSchema,
)


class GenomePropertyService:
    def list_by_type(self, gp_type: str | None = None) -> list[GenomePropertySummarySchema]:
        rows = GenomeProperty.objects.order_by("accession").values("accession", "description")
        if gp_type:
            rows = rows.filter(type=gp_type)
        return [GenomePropertySummarySchema(**row) for row in rows]

    def get(self, accession: str) -> GenomePropertyDetailSchema | None:
        row = (
            GenomeProperty.objects.filter(pk=accession)
            .values("accession", "type", "author", "description", "threshold", "comment")
            .first()
        )
        if not row:
            return None
        return GenomePropertyDetailSchema(
            accession=row["accession"],
            type=row["type"],
            author=row["author"],
            description=row["description"],
            threshold=row["threshold"],
            comment=row["comment"],
            literature=self._literature(accession),
            database_links=self._database_links(accession),
            steps=self._steps(accession),
        )

    def _literature(self, accession: str) -> list[LiteratureSchema]:
        return [
            LiteratureSchema(
                pmid=item["literature_reference_pmid__pmid"],
                title=item["literature_reference_pmid__title"],
                author=item["literature_reference_pmid__author"],
                journal=item["literature_reference_pmid__journal"],
                list_order=item["list_order"],
            )
            for item in GpLitRef.objects.filter(gp_accession_id=accession)
            .order_by("list_order")
            .values(
                "list_order",
                "literature_reference_pmid__pmid",
                "literature_reference_pmid__title",
                "literature_reference_pmid__author",
                "literature_reference_pmid__journal",
            )
        ]

    def _database_links(self, accession: str) -> list[DatabaseLinkSchema]:
        return [
            DatabaseLinkSchema(
                db_id=item["db_id"],
                db_link=item["db_link"],
                comment=item["comment"],
                other_params=item["other_params"],
            )
            for item in GpDatabaseLink.objects.filter(gp_accession_id=accession).values(
                "db_id", "db_link", "comment", "other_params"
            )
        ]

    def _steps(self, accession: str) -> list[StepSchema]:
        steps = list(
            GpStep.objects.filter(gp_accession_id=accession)
            .order_by("step_number", "auto_step")
            .values("auto_step", "step_id", "step_number", "required")
        )
        step_ids = [step["auto_step"] for step in steps]
        children_by_step, evidence_by_step = self._step_relations(step_ids)
        return [
            StepSchema(
                step_id=step["step_id"],
                step_number=step["step_number"],
                required=step["required"],
                child_accession=children_by_step.get(step["auto_step"]),
                evidence=evidence_by_step.get(step["auto_step"], []),
            )
            for step in steps
        ]

    def _step_relations(
        self, step_ids: list[int]
    ) -> tuple[dict[int, str], dict[int, list[StepEvidenceSchema]]]:
        children_by_step: dict[int, str] = {}
        evidence_by_step: dict[int, list[StepEvidenceSchema]] = defaultdict(list)
        if not step_ids:
            return children_by_step, evidence_by_step

        for item in GpStepEvidenceGp.objects.filter(auto_step_id__in=step_ids).values(
            "auto_step_id", "gp_accession_id"
        ):
            children_by_step.setdefault(item["auto_step_id"], item["gp_accession_id"])

        ipr_rows = list(
            GpStepEvidenceIpr.objects.filter(auto_step_id__in=step_ids).values(
                "auto_step_id", "interpro_acc", "signature_acc", "auto_ipr_step"
            )
        )
        go_by_ipr: dict[int, str] = {}
        ipr_ids = [item["auto_ipr_step"] for item in ipr_rows]
        if ipr_ids:
            for item in IprStepToGo.objects.filter(auto_ipr_step_id__in=ipr_ids).values(
                "auto_ipr_step_id", "go_id"
            ):
                go_by_ipr.setdefault(item["auto_ipr_step_id"], item["go_id"])
        for item in ipr_rows:
            evidence_by_step[item["auto_step_id"]].append(
                StepEvidenceSchema(
                    interpro_acc=item["interpro_acc"],
                    signature_acc=item["signature_acc"],
                    go_id=go_by_ipr.get(item["auto_ipr_step"]),
                )
            )
        return children_by_step, evidence_by_step
