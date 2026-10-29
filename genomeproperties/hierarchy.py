from collections import defaultdict

from .models import GenomeProperty, GpStep, GpStepEvidenceGp


def build_hierarchy_tree(accession: str) -> dict | None:
    """Build the child-property tree under accession in a few SQL queries.

    Children come from gp_step → gp_step_evidence_gp (another genome property).
    """
    descriptions = dict(GenomeProperty.objects.values_list("accession", "description"))
    if accession not in descriptions:
        return None

    steps = list(
        GpStep.objects.order_by("gp_accession_id", "step_number", "auto_step").values(
            "auto_step", "gp_accession_id"
        )
    )

    evidence_by_step: dict[int, list[str]] = defaultdict(list)
    for row in GpStepEvidenceGp.objects.values("auto_step_id", "gp_accession_id"):
        child = row["gp_accession_id"]
        if child:
            evidence_by_step[row["auto_step_id"]].append(child)

    children: dict[str, list[str]] = {}
    seen: dict[str, set[str]] = defaultdict(set)
    for step in steps:
        parent = step["gp_accession_id"]
        for child in evidence_by_step.get(step["auto_step"], []):
            if child in seen[parent]:
                continue
            seen[parent].add(child)
            children.setdefault(parent, []).append(child)

    def to_node(acc: str, ancestors: frozenset[str]) -> dict:
        next_ancestors = ancestors | {acc}
        nested = []
        for child in children.get(acc, []):
            if child in next_ancestors or child not in descriptions:
                continue
            nested.append(to_node(child, next_ancestors))
        return {
            "accession": acc,
            "description": descriptions[acc],
            "children": nested,
        }

    return to_node(accession, frozenset())
