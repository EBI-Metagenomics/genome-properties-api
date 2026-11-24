"""Domain records for Genome Properties assignment.

These are the in-memory graph and parse results used by the assignment
service. They are not HTTP bodies; the viewer payload stays a dict because
each organism name is a dynamic key.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Evidence:
    interpro_acc: str = ""
    signature_acc: str = ""
    sufficient: bool = False
    child_accession: str = ""


@dataclass
class AssignmentStep:
    number: int
    name: str
    required: bool
    evidences: list[Evidence] = field(default_factory=list)


@dataclass
class AssignmentProperty:
    accession: str
    name: str
    type: str
    threshold: int
    steps: list[AssignmentStep] = field(default_factory=list)


@dataclass(frozen=True)
class ParsedMatches:
    mode: str
    tokens: set[str]
    rows: int
