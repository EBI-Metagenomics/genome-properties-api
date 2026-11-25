"""Assign Genome Properties from InterProScan TSV or InterPro entry exports."""

from __future__ import annotations

import gzip
import re
from functools import lru_cache

from genomeproperties.constants import (
    AssignmentMode,
    AssignmentResult,
    ErrorMessage,
    InterProTsv,
    PropertyType,
    UploadLimit,
)
from genomeproperties.models import (
    GenomeProperty,
    GpStep,
    GpStepEvidenceGp,
    GpStepEvidenceIpr,
)
from genomeproperties.schemas.assignment import (
    AssignmentProperty,
    AssignmentStep,
    Evidence,
    ParsedMatches,
)


class AssignError(ValueError):
    """User-facing upload or parse failure."""


class OrganismLabel:
    """Heatmap column name derived from the uploaded file name."""

    _CONTROL = re.compile(r"[\u0000-\u001f\u007f]")
    _SUFFIX = re.compile(r"(\.(tsv|txt|gz))+$", re.IGNORECASE)
    _WHITESPACE = re.compile(r"\s+")

    @classmethod
    def clean(cls, name: str) -> str:
        cleaned = cls._CONTROL.sub(" ", name or "").strip()
        cleaned = cls._SUFFIX.sub("", cleaned)
        cleaned = cls._WHITESPACE.sub(" ", cleaned)[: UploadLimit.ORGANISM_LABEL_MAX]
        return cleaned or UploadLimit.DEFAULT_ORGANISM


class InterProMatchParser:
    """Decode an upload and collect the InterPro accessions or signatures it contains."""

    _IPR_ACCESSION = re.compile(r"^IPR\d{6}$")
    _MD5 = re.compile(r"^[A-Fa-f0-9]{32}$")

    def decode(self, raw: bytes) -> str:
        if len(raw) > UploadLimit.MAX_BYTES:
            raise AssignError(ErrorMessage.assign_file_too_large(len(raw)))
        if not raw:
            raise AssignError(ErrorMessage.ASSIGN_FILE_EMPTY)
        if raw[:2] == UploadLimit.GZIP_MAGIC:
            try:
                raw = gzip.decompress(raw)
            except OSError as exc:
                raise AssignError(ErrorMessage.ASSIGN_GZIP_INVALID) from exc
            if len(raw) > UploadLimit.MAX_BYTES:
                raise AssignError(ErrorMessage.ASSIGN_DECOMPRESSED_TOO_LARGE)
        if b"\x00" in raw[: UploadLimit.BINARY_PROBE_BYTES]:
            raise AssignError(ErrorMessage.ASSIGN_BINARY)
        return raw.decode("utf-8-sig", errors="replace")

    def parse(self, text: str) -> ParsedMatches:
        mode: str | None = None
        tokens: set[str] = set()
        rows = 0
        for raw in text.splitlines():
            line = raw[:-1] if raw.endswith("\r") else raw
            if not line or line[0] == InterProTsv.COMMENT:
                continue
            cols = line.split("\t")
            if mode is None:
                mode = self._mode(cols)
                if mode == AssignmentMode.ENTRIES and cols[0] == InterProTsv.HEADER_ACCESSION:
                    continue
            if mode == AssignmentMode.ENTRIES:
                if self._IPR_ACCESSION.match(cols[0] or ""):
                    tokens.add(cols[0])
                    rows += 1
                continue
            if len(cols) < InterProTsv.MIN_SIGNATURE_COLUMNS:
                continue
            signature = cols[InterProTsv.SIGNATURE_INDEX].strip()
            if not signature or signature == InterProTsv.MISSING_SIGNATURE:
                continue
            tokens.add(signature)
            if signature.startswith(InterProTsv.PANTHER_PREFIX) and ":" in signature:
                tokens.add(signature.split(":", 1)[0])
            rows += 1
        if not mode or rows == 0:
            raise AssignError(ErrorMessage.ASSIGN_UNKNOWN_FORMAT)
        return ParsedMatches(mode=mode, tokens=tokens, rows=rows)

    def _mode(self, cols: list[str]) -> str:
        if (
            cols
            and cols[0] == InterProTsv.HEADER_ACCESSION
            and len(cols) > 1
            and cols[1] == InterProTsv.HEADER_NAME
        ):
            return AssignmentMode.ENTRIES
        if len(cols) >= InterProTsv.MIN_SCAN_COLUMNS and self._MD5.match(
            cols[InterProTsv.MD5_INDEX] or ""
        ):
            return AssignmentMode.SIGNATURES
        if (
            len(cols) >= InterProTsv.MIN_SCAN_COLUMNS
            and cols[InterProTsv.LENGTH_INDEX].isdigit()
            and cols[InterProTsv.START_INDEX].isdigit()
            and cols[InterProTsv.STOP_INDEX].isdigit()
        ):
            return AssignmentMode.SIGNATURES
        if self._IPR_ACCESSION.match(cols[0] or ""):
            return AssignmentMode.ENTRIES
        raise AssignError(ErrorMessage.ASSIGN_UNKNOWN_FORMAT)


class PropertyGraph:
    """Genome Property steps and evidence loaded once per process."""

    @staticmethod
    @lru_cache(maxsize=1)
    def load() -> dict[str, AssignmentProperty]:
        properties = {
            row["accession"]: AssignmentProperty(
                accession=row["accession"],
                name=row["description"],
                type=row["type"],
                threshold=int(row["threshold"] or 0),
            )
            for row in GenomeProperty.objects.values(
                "accession", "description", "type", "threshold"
            )
        }
        if not properties:
            raise AssignError(ErrorMessage.ASSIGN_NOT_LOADED)
        steps_by_id: dict[int, AssignmentStep] = {}
        for row in GpStep.objects.order_by("gp_accession_id", "step_number", "auto_step").values(
            "auto_step", "gp_accession_id", "step_number", "step_id", "required"
        ):
            prop = properties.get(row["gp_accession_id"])
            if prop is None:
                continue
            step = AssignmentStep(
                number=int(row["step_number"]),
                name=row["step_id"] or "",
                required=bool(row["required"]),
            )
            prop.steps.append(step)
            steps_by_id[row["auto_step"]] = step

        for row in GpStepEvidenceIpr.objects.values(
            "auto_step_id", "interpro_acc", "signature_acc", "sufficient"
        ):
            step = steps_by_id.get(row["auto_step_id"])
            if step is None:
                continue
            step.evidences.append(
                Evidence(
                    interpro_acc=row["interpro_acc"] or "",
                    signature_acc=row["signature_acc"] or "",
                    sufficient=bool(row["sufficient"]),
                )
            )

        for row in GpStepEvidenceGp.objects.values("auto_step_id", "gp_accession_id"):
            step = steps_by_id.get(row["auto_step_id"])
            if step is None:
                continue
            step.evidences.append(Evidence(child_accession=row["gp_accession_id"] or ""))

        return properties


class _AssignmentRun:
    """One upload evaluated against the property graph, including child properties."""

    def __init__(self, graph: dict[str, AssignmentProperty], parsed: ParsedMatches):
        self._graph = graph
        self._tokens = parsed.tokens
        self._mode = parsed.mode
        self._results: dict[str, tuple[str, list[tuple[AssignmentStep, bool]]]] = {}
        self._busy: set[str] = set()

    def results(self) -> dict[str, tuple[str, list[tuple[AssignmentStep, bool]]]]:
        for prop in self._graph.values():
            if prop.type not in PropertyType.SKIPPED:
                self._assign(prop)
        return self._results

    def _child_result(self, accession: str) -> str:
        if accession in self._results:
            return self._results[accession][0]
        child = self._graph.get(accession)
        if child is None or child.type in PropertyType.SKIPPED:
            return AssignmentResult.NO
        return self._assign(child)[0]

    def _assign(self, prop: AssignmentProperty) -> tuple[str, list[tuple[AssignmentStep, bool]]]:
        if prop.accession in self._results:
            return self._results[prop.accession]
        if prop.accession in self._busy:
            return AssignmentResult.NO, []
        self._busy.add(prop.accession)
        outcome = self._evaluate(prop)
        self._busy.discard(prop.accession)
        self._results[prop.accession] = outcome
        return outcome

    def _evidence_hit(self, evidence: Evidence) -> bool:
        if evidence.child_accession:
            return False
        if self._mode == AssignmentMode.SIGNATURES:
            return bool(evidence.signature_acc) and evidence.signature_acc in self._tokens
        return bool(evidence.interpro_acc) and evidence.interpro_acc in self._tokens

    def _evaluate_step(self, step: AssignmentStep) -> bool | None:
        if not step.evidences:
            return None
        sufficient: list[bool] = []
        other: list[bool] = []
        for evidence in step.evidences:
            if evidence.child_accession:
                child = self._child_result(evidence.child_accession)
                other.append(child in (AssignmentResult.YES, AssignmentResult.PARTIAL))
                continue
            hit = self._evidence_hit(evidence)
            if evidence.sufficient:
                sufficient.append(hit)
            else:
                other.append(hit)
        if sufficient:
            return any(sufficient)
        if other:
            return all(other)
        return False

    def _evaluate(self, prop: AssignmentProperty) -> tuple[str, list[tuple[AssignmentStep, bool]]]:
        found_required = 0
        required_total = 0
        all_found = 0
        all_total = 0
        step_hits: list[tuple[AssignmentStep, bool]] = []
        for step in prop.steps:
            found = self._evaluate_step(step)
            if found is None:
                continue
            step_hits.append((step, found))
            all_total += 1
            if found:
                all_found += 1
            if step.required:
                required_total += 1
                if found:
                    found_required += 1
        if required_total > 0:
            if found_required == required_total:
                result = AssignmentResult.YES
            elif found_required > prop.threshold:
                result = AssignmentResult.PARTIAL
            else:
                result = AssignmentResult.NO
        elif all_total == 0 or all_found == 0:
            result = AssignmentResult.NO
        elif all_found == all_total:
            result = AssignmentResult.YES
        else:
            result = AssignmentResult.PARTIAL
        return result, step_hits


class AssignmentService:
    def __init__(
        self,
        graph: dict[str, AssignmentProperty] | None = None,
        parser: InterProMatchParser | None = None,
    ):
        self._graph = graph
        self._parser = parser or InterProMatchParser()

    @property
    def graph(self) -> dict[str, AssignmentProperty]:
        if self._graph is None:
            self._graph = PropertyGraph.load()
        return self._graph

    def assign_text(self, text: str, organism: str) -> dict:
        label = OrganismLabel.clean(organism)
        parsed = self._parser.parse(text)
        assigned = _AssignmentRun(self.graph, parsed).results()
        return self._viewer_payload(assigned, label)

    def assign_bytes(self, raw: bytes, organism: str) -> dict:
        return self.assign_text(self._parser.decode(raw), organism)

    def _viewer_payload(
        self,
        assigned: dict[str, tuple[str, list[tuple[AssignmentStep, bool]]]],
        organism: str,
    ) -> dict:
        payload = {}
        for accession, (result, step_hits) in assigned.items():
            prop = self.graph[accession]
            if prop.type in PropertyType.SKIPPED:
                continue
            payload[accession] = {
                "property": accession,
                "name": prop.name,
                "values": {
                    organism: result,
                    AssignmentResult.TOTAL: {
                        AssignmentResult.YES: int(result == AssignmentResult.YES),
                        AssignmentResult.PARTIAL: int(result == AssignmentResult.PARTIAL),
                        AssignmentResult.NO: int(result == AssignmentResult.NO),
                    },
                },
                "steps": [
                    {
                        "step": step.number,
                        "step_name": step.name,
                        "required": int(step.required),
                        "values": {organism: bool(found)},
                    }
                    for step, found in step_hits
                ],
            }
        return payload
