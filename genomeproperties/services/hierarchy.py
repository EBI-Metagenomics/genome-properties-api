from collections import defaultdict

from genomeproperties.models import GenomeProperty, GpStep, GpStepEvidenceGp
from genomeproperties.schemas import HierarchyNodeSchema
from genomeproperties.utils import OrderedUniqueMap


class HierarchyService:
    def get_tree(self, accession: str) -> HierarchyNodeSchema | None:
        descriptions = dict(GenomeProperty.objects.values_list("accession", "description"))
        if accession not in descriptions:
            return None
        children = self._child_map()
        return self._to_node(accession, descriptions, children, frozenset())

    def _child_map(self) -> dict[str, list[str]]:
        steps = GpStep.objects.order_by("gp_accession_id", "step_number", "auto_step").values(
            "auto_step", "gp_accession_id"
        )
        evidence_by_step: dict[int, list[str]] = defaultdict(list)
        for row in GpStepEvidenceGp.objects.values("auto_step_id", "gp_accession_id"):
            child = row["gp_accession_id"]
            if child:
                evidence_by_step[row["auto_step_id"]].append(child)

        children = OrderedUniqueMap()
        for step in steps:
            parent = step["gp_accession_id"]
            for child in evidence_by_step.get(step["auto_step"], []):
                children.add(parent, child)
        return children.as_dict()

    def _to_node(
        self,
        accession: str,
        descriptions: dict[str, str],
        children: dict[str, list[str]],
        ancestors: frozenset[str],
    ) -> HierarchyNodeSchema:
        next_ancestors = ancestors | {accession}
        nested = []
        for child in children.get(accession, []):
            if child in next_ancestors or child not in descriptions:
                continue
            nested.append(self._to_node(child, descriptions, children, next_ancestors))
        return HierarchyNodeSchema(
            accession=accession,
            description=descriptions[accession],
            children=nested,
        )
