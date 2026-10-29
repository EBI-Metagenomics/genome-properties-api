from collections import defaultdict

from .models import (
    GenomeProperty,
    GpDatabaseLink,
    GpLitRef,
    GpStep,
    GpStepEvidenceGp,
    GpStepEvidenceIpr,
    IprStepToGo,
)


def list_genome_properties(gp_type: str | None = None) -> list[dict]:
    rows = GenomeProperty.objects.order_by("accession").values("accession", "description")
    if gp_type:
        rows = rows.filter(type=gp_type)
    return list(rows)


def serialize_genome_property(accession: str) -> dict | None:
    row = (
        GenomeProperty.objects.filter(pk=accession)
        .values("accession", "type", "author", "description", "threshold", "comment")
        .first()
    )
    if not row:
        return None

    literature = [
        {
            "pmid": item["literature_reference_pmid__pmid"],
            "title": item["literature_reference_pmid__title"],
            "author": item["literature_reference_pmid__author"],
            "journal": item["literature_reference_pmid__journal"],
            "listOrder": item["list_order"],
        }
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

    database_links = [
        {
            "dbId": item["db_id"],
            "dbLink": item["db_link"],
            "comment": item["comment"],
            "otherParams": item["other_params"],
        }
        for item in GpDatabaseLink.objects.filter(gp_accession_id=accession).values(
            "db_id", "db_link", "comment", "other_params"
        )
    ]

    steps = list(
        GpStep.objects.filter(gp_accession_id=accession)
        .order_by("step_number", "auto_step")
        .values("auto_step", "step_id", "step_number", "required")
    )
    step_ids = [step["auto_step"] for step in steps]

    children_by_step: dict[int, str] = {}
    evidence_by_step: dict[int, list[dict]] = defaultdict(list)
    if step_ids:
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
                {
                    "interproAcc": item["interpro_acc"],
                    "signatureAcc": item["signature_acc"],
                    "goId": go_by_ipr.get(item["auto_ipr_step"]),
                }
            )

    return {
        "accession": row["accession"],
        "type": row["type"],
        "author": row["author"],
        "description": row["description"],
        "threshold": row["threshold"],
        "comment": row["comment"],
        "literature": literature,
        "databaseLinks": database_links,
        "steps": [
            {
                "stepId": step["step_id"],
                "stepNumber": step["step_number"],
                "required": step["required"],
                "childAccession": children_by_step.get(step["auto_step"]),
                "evidence": evidence_by_step.get(step["auto_step"], []),
            }
            for step in steps
        ],
    }
