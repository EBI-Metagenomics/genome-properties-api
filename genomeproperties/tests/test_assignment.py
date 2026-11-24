import gzip
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase

from genomeproperties.services.assignment import (
    NO,
    PARTIAL,
    YES,
    AssignError,
    AssignmentService,
    Evidence,
    PropertyDef,
    StepDef,
    assign_properties,
    parse_matches,
    to_viewer_json,
)

MD5 = "a" * 32


def _graph() -> dict[str, PropertyDef]:
    child = PropertyDef(
        accession="GenProp0002",
        name="Child",
        type="PATHWAY",
        threshold=0,
        steps=[
            StepDef(
                number=1,
                name="child-step",
                required=True,
                evidences=[
                    Evidence(
                        interpro_acc="IPR000002",
                        signature_acc="PF00002",
                        sufficient=False,
                    )
                ],
            )
        ],
    )
    parent = PropertyDef(
        accession="GenProp0001",
        name="Parent",
        type="PATHWAY",
        threshold=0,
        steps=[
            StepDef(
                number=1,
                name="signature-step",
                required=True,
                evidences=[
                    Evidence(
                        interpro_acc="IPR000001",
                        signature_acc="PF00001",
                        sufficient=False,
                    )
                ],
            ),
            StepDef(
                number=2,
                name="sufficient-step",
                required=True,
                evidences=[
                    Evidence(
                        interpro_acc="IPR000009",
                        signature_acc="PF00009",
                        sufficient=False,
                    ),
                    Evidence(
                        interpro_acc="IPR000010",
                        signature_acc="PF00010",
                        sufficient=True,
                    ),
                ],
            ),
            StepDef(
                number=3,
                name="child-step",
                required=True,
                evidences=[Evidence(child_accession="GenProp0002")],
            ),
        ],
    )
    skipped = PropertyDef(
        accession="GenProp0099",
        name="Category",
        type="CATEGORY",
        threshold=0,
        steps=[],
    )
    return {
        parent.accession: parent,
        child.accession: child,
        skipped.accession: skipped,
    }


def _scan_line(signature: str) -> str:
    return "\t".join(
        [
            "prot1",
            MD5,
            "100",
            "Pfam",
            signature,
            "desc",
            "1",
            "50",
            "1e-5",
            "T",
            "01-01-2020",
            "-",
            "-",
        ]
    )


class ParseMatchesTests(SimpleTestCase):
    def test_interproscan_uses_signature_column(self):
        parsed = parse_matches(_scan_line("PF00001") + "\n" + _scan_line("PTHR12345:SF1"))
        self.assertEqual(parsed.mode, "signatures")
        self.assertIn("PF00001", parsed.tokens)
        self.assertIn("PTHR12345:SF1", parsed.tokens)
        self.assertIn("PTHR12345", parsed.tokens)

    def test_entries_matching_uses_ipr_accessions(self):
        text = "Accession\tName\nIPR000001\tKringle\nnot-an-ipr\tSkip\n"
        parsed = parse_matches(text)
        self.assertEqual(parsed.mode, "entries")
        self.assertEqual(parsed.tokens, {"IPR000001"})

    def test_headerless_ipr_export_is_entries(self):
        parsed = parse_matches("IPR000001\tKringle\tInterPro\n")
        self.assertEqual(parsed.mode, "entries")
        self.assertEqual(parsed.tokens, {"IPR000001"})

    def test_unknown_format_is_rejected(self):
        with self.assertRaises(AssignError):
            parse_matches("GenProp0001\tName\tYES\n")


class EvaluationTests(SimpleTestCase):
    def test_interproscan_yes_when_required_steps_and_child_hit(self):
        parsed = parse_matches(
            "\n".join([_scan_line("PF00001"), _scan_line("PF00010"), _scan_line("PF00002")])
        )
        assigned = assign_properties(_graph(), parsed)
        self.assertEqual(assigned["GenProp0001"][0], YES)
        self.assertEqual(assigned["GenProp0002"][0], YES)
        self.assertNotIn("GenProp0099", assigned)

    def test_partial_when_some_required_steps_hit(self):
        parsed = parse_matches(_scan_line("PF00001"))
        assigned = assign_properties(_graph(), parsed)
        self.assertEqual(assigned["GenProp0001"][0], PARTIAL)
        self.assertEqual(assigned["GenProp0002"][0], NO)

    def test_sufficient_evidence_satisfies_the_step(self):
        parsed = parse_matches(
            "\n".join([_scan_line("PF00001"), _scan_line("PF00010"), _scan_line("PF00002")])
        )
        steps = assign_properties(_graph(), parsed)["GenProp0001"][1]
        hits = {step.number: found for step, found in steps}
        self.assertTrue(hits[2])

    def test_entries_mode_matches_interpro_accessions(self):
        parsed = parse_matches("Accession\tName\nIPR000001\tA\nIPR000010\tB\nIPR000002\tC\n")
        assigned = assign_properties(_graph(), parsed)
        self.assertEqual(assigned["GenProp0001"][0], YES)

    def test_viewer_json_uses_filename_as_column(self):
        parsed = parse_matches(_scan_line("PF00001"))
        graph = _graph()
        payload = to_viewer_json(graph, assign_properties(graph, parsed), "demo")
        self.assertEqual(payload["GenProp0001"]["values"]["demo"], PARTIAL)
        self.assertEqual(payload["GenProp0001"]["values"]["TOTAL"][PARTIAL], 1)
        self.assertNotIn("GenProp0099", payload)

    def test_service_assigns_from_gzipped_bytes(self):
        raw = gzip.compress(_scan_line("PF00001").encode())
        payload = AssignmentService(graph=_graph()).assign_bytes(raw, "demo.tsv.gz")
        self.assertEqual(payload["GenProp0001"]["values"]["demo"], PARTIAL)


class AssignApiTests(SimpleTestCase):
    def test_urlencoded_interproscan_returns_viewer_json(self):
        payload = {
            "GenProp0001": {
                "property": "GenProp0001",
                "name": "Parent",
                "values": {"demo": YES, "TOTAL": {YES: 1, PARTIAL: 0, NO: 0}},
                "steps": [],
            }
        }
        with patch(
            "genomeproperties.services.assignment.AssignmentService.assign_bytes",
            return_value=payload,
        ):
            response = self.client.post(
                "/api/v1/assign",
                {"ipproname": "demo.tsv", "ipprotsv": _scan_line("PF00001")},
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["GenProp0001"]["values"]["demo"], YES)

    def test_multipart_file_is_accepted(self):
        payload = {
            "GenProp0001": {
                "property": "GenProp0001",
                "name": "Parent",
                "values": {"sara": PARTIAL, "TOTAL": {YES: 0, PARTIAL: 1, NO: 0}},
                "steps": [],
            }
        }
        upload = SimpleUploadedFile(
            "entries.tsv",
            b"Accession\tName\nIPR000001\tKringle\n",
            content_type="text/tab-separated-values",
        )
        with patch(
            "genomeproperties.services.assignment.AssignmentService.assign_bytes",
            return_value=payload,
        ):
            response = self.client.post(
                "/api/v1/assign",
                {"ipproname": "sara.tsv", "file": upload},
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["GenProp0001"]["values"]["sara"], PARTIAL)

    def test_gzipped_file_is_accepted(self):
        payload = {
            "GenProp0001": {
                "property": "GenProp0001",
                "name": "Parent",
                "values": {"demo": PARTIAL, "TOTAL": {YES: 0, PARTIAL: 1, NO: 0}},
                "steps": [],
            }
        }
        upload = SimpleUploadedFile(
            "demo.tsv.gz",
            gzip.compress(_scan_line("PF00001").encode()),
            content_type="application/gzip",
        )
        with patch(
            "genomeproperties.services.assignment.AssignmentService.assign_bytes",
            return_value=payload,
        ) as assign_bytes:
            response = self.client.post(
                "/api/v1/assign",
                {"ipproname": "demo.tsv.gz", "file": upload},
            )
        self.assertEqual(response.status_code, 200)
        raw = assign_bytes.call_args.args[0]
        self.assertEqual(raw[:2], b"\x1f\x8b")

    def test_unknown_format_is_400(self):
        response = self.client.post(
            "/api/v1/assign",
            {"ipproname": "summary.gp", "ipprotsv": "GenProp0001\tName\tYES\n"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("InterProScan", response.json()["detail"])

    def test_empty_upload_is_400(self):
        response = self.client.post("/api/v1/assign", {})
        self.assertEqual(response.status_code, 400)
