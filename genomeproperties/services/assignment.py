"""Assign Genome Properties from InterProScan TSV or InterPro entry exports."""

from __future__ import annotations

import gzip
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import lru_cache

from genomeproperties.models import (
    GenomeProperty,
    GpStep,
    GpStepEvidenceGp,
    GpStepEvidenceIpr,
)

SKIP_TYPES = frozenset({"CATEGORY", "ROOT", "SUMMARY"})
MODE_SIGNATURES = "signatures"
MODE_ENTRIES = "entries"
MAX_UPLOAD_BYTES = 50 * 1024 * 1024
IPR_RE = re.compile(r"^IPR\d{6}$")
MD5_RE = re.compile(r"^[A-Fa-f0-9]{32}$")
YES, PARTIAL, NO = "YES", "PARTIAL", "NO"


class AssignError(ValueError):
    """User-facing upload or parse failure."""


@dataclass(frozen=True)
class Evidence:
    interpro_acc: str = ""
    signature_acc: str = ""
    sufficient: bool = False
    child_accession: str = ""


@dataclass
class StepDef:
    number: int
    name: str
    required: bool
    evidences: list[Evidence] = field(default_factory=list)


@dataclass
class PropertyDef:
    accession: str
    name: str
    type: str
    threshold: int
    steps: list[StepDef] = field(default_factory=list)


@dataclass
class ParsedMatches:
    mode: str
    tokens: set[str]
    rows: int


@lru_cache(maxsize=1)
def load_property_graph() -> dict[str, PropertyDef]:
    properties = {
        row["accession"]: PropertyDef(
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
        raise AssignError(
            "Genome Properties data is not loaded. Set DATABASE_PATH to the SQLite database."
        )
    steps_by_id: dict[int, StepDef] = {}
    for row in GpStep.objects.order_by(
        "gp_accession_id", "step_number", "auto_step"
    ).values("auto_step", "gp_accession_id", "step_number", "step_id", "required"):
        prop = properties.get(row["gp_accession_id"])
        if prop is None:
            continue
        step = StepDef(
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


def decode_upload(raw: bytes) -> str:
    if len(raw) > MAX_UPLOAD_BYTES:
        raise AssignError(
            f"This file is {len(raw) / (1024 * 1024):.1f} MB. "
            f"The limit is {MAX_UPLOAD_BYTES // (1024 * 1024)} MB."
        )
    if not raw:
        raise AssignError("This file is empty.")
    if raw[:2] == b"\x1f\x8b":
        try:
            raw = gzip.decompress(raw)
        except OSError as exc:
            raise AssignError("This gzipped file could not be read.") from exc
        if len(raw) > MAX_UPLOAD_BYTES:
            raise AssignError("The decompressed file is larger than the upload limit.")
    if b"\x00" in raw[:4096]:
        raise AssignError("This looks like a binary file, not a tab-separated text file.")
    return raw.decode("utf-8-sig", errors="replace")


def parse_matches(text: str) -> ParsedMatches:
    mode = None
    tokens: set[str] = set()
    rows = 0
    for raw in text.splitlines():
        line = raw[:-1] if raw.endswith("\r") else raw
        if not line or line[0] == "#":
            continue
        cols = line.split("\t")
        if mode is None:
            mode = _detect_mode(cols)
            if mode == MODE_ENTRIES and cols[0] == "Accession":
                continue
        if mode == MODE_ENTRIES:
            if IPR_RE.match(cols[0] or ""):
                tokens.add(cols[0])
                rows += 1
            continue
        if len(cols) < 5:
            continue
        signature = cols[4].strip()
        if not signature or signature == "-":
            continue
        tokens.add(signature)
        if signature.startswith("PTHR") and ":" in signature:
            tokens.add(signature.split(":", 1)[0])
        rows += 1
    if not mode or rows == 0:
        raise AssignError(
            "This is not an InterProScan TSV or an InterPro entry export. "
            "Upload InterProScan TSV (interproscan.sh -f tsv) or the InterPro "
            "proteome Entries matching TSV."
        )
    return ParsedMatches(mode=mode, tokens=tokens, rows=rows)


def _detect_mode(cols: list[str]) -> str:
    if cols and cols[0] == "Accession" and len(cols) > 1 and cols[1] == "Name":
        return MODE_ENTRIES
    if len(cols) >= 11 and MD5_RE.match(cols[1] or ""):
        return MODE_SIGNATURES
    if (
        len(cols) >= 11
        and cols[2].isdigit()
        and cols[6].isdigit()
        and cols[7].isdigit()
    ):
        return MODE_SIGNATURES
    if IPR_RE.match(cols[0] or ""):
        return MODE_ENTRIES
    raise AssignError(
        "This is not an InterProScan TSV or an InterPro entry export. "
        "Upload InterProScan TSV (interproscan.sh -f tsv) or the InterPro "
        "proteome Entries matching TSV."
    )


def evidence_hit(evidence: Evidence, tokens: set[str], mode: str) -> bool:
    if evidence.child_accession:
        return False
    if mode == MODE_SIGNATURES:
        return bool(evidence.signature_acc) and evidence.signature_acc in tokens
    return bool(evidence.interpro_acc) and evidence.interpro_acc in tokens


def evaluate_step(
    step: StepDef,
    tokens: set[str],
    mode: str,
    child_result: Callable[[str], str],
) -> bool | None:
    if not step.evidences:
        return None
    sufficient: list[bool] = []
    other: list[bool] = []
    for evidence in step.evidences:
        if evidence.child_accession:
            child = child_result(evidence.child_accession)
            other.append(child in (YES, PARTIAL))
            continue
        hit = evidence_hit(evidence, tokens, mode)
        if evidence.sufficient:
            sufficient.append(hit)
        else:
            other.append(hit)
    if sufficient:
        return any(sufficient)
    if other:
        return all(other)
    return False


def evaluate_property(
    prop: PropertyDef,
    tokens: set[str],
    mode: str,
    child_result: Callable[[str], str],
) -> tuple[str, list[tuple[StepDef, bool]]]:
    found_required = 0
    required_total = 0
    all_found = 0
    all_total = 0
    step_hits: list[tuple[StepDef, bool]] = []
    for step in prop.steps:
        found = evaluate_step(step, tokens, mode, child_result)
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
            result = YES
        elif found_required > prop.threshold:
            result = PARTIAL
        else:
            result = NO
    elif all_total == 0 or all_found == 0:
        result = NO
    elif all_found == all_total:
        result = YES
    else:
        result = PARTIAL
    return result, step_hits


def assign_properties(
    graph: dict[str, PropertyDef],
    parsed: ParsedMatches,
) -> dict[str, tuple[str, list[tuple[StepDef, bool]]]]:
    results: dict[str, tuple[str, list[tuple[StepDef, bool]]]] = {}
    busy: set[str] = set()

    def child_result(accession: str) -> str:
        if accession in results:
            return results[accession][0]
        child = graph.get(accession)
        if child is None or child.type in SKIP_TYPES:
            return NO
        return assign_one(child)[0]

    def assign_one(prop: PropertyDef) -> tuple[str, list[tuple[StepDef, bool]]]:
        if prop.accession in results:
            return results[prop.accession]
        if prop.accession in busy:
            return NO, []
        busy.add(prop.accession)
        outcome = evaluate_property(prop, parsed.tokens, parsed.mode, child_result)
        busy.discard(prop.accession)
        results[prop.accession] = outcome
        return outcome

    for prop in graph.values():
        if prop.type not in SKIP_TYPES:
            assign_one(prop)
    return results


def to_viewer_json(
    graph: dict[str, PropertyDef],
    assigned: dict[str, tuple[str, list[tuple[StepDef, bool]]]],
    organism: str,
) -> dict:
    payload = {}
    for accession, (result, step_hits) in assigned.items():
        prop = graph[accession]
        if prop.type in SKIP_TYPES:
            continue
        payload[accession] = {
            "property": accession,
            "name": prop.name,
            "values": {
                organism: result,
                "TOTAL": {
                    YES: int(result == YES),
                    PARTIAL: int(result == PARTIAL),
                    NO: int(result == NO),
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


class AssignmentService:
    def __init__(self, graph: dict[str, PropertyDef] | None = None):
        self._graph = graph

    @property
    def graph(self) -> dict[str, PropertyDef]:
        if self._graph is None:
            self._graph = load_property_graph()
        return self._graph

    def assign_text(self, text: str, organism: str) -> dict:
        name = _clean_organism(organism)
        parsed = parse_matches(text)
        assigned = assign_properties(self.graph, parsed)
        return to_viewer_json(self.graph, assigned, name)

    def assign_bytes(self, raw: bytes, organism: str) -> dict:
        return self.assign_text(decode_upload(raw), organism)


def _clean_organism(name: str) -> str:
    cleaned = re.sub(r"[\u0000-\u001f\u007f]", " ", name or "").strip()
    cleaned = re.sub(r"(\.(tsv|txt|gz))+$", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\s+", " ", cleaned)[:80]
    return cleaned or "upload"
