from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from .hierarchy import build_hierarchy_tree
from .serialize import serialize_genome_property
from .settings import _extend_allowed_hosts


class AllowedHostsTests(SimpleTestCase):
    def test_pod_ip_is_appended_for_kubelet_probes(self):
        self.assertEqual(
            _extend_allowed_hosts(["localhost", "127.0.0.1"], "10.251.74.247"),
            ["localhost", "127.0.0.1", "10.251.74.247"],
        )

    def test_empty_pod_ip_is_ignored(self):
        self.assertEqual(
            _extend_allowed_hosts(["localhost"], "", None),
            ["localhost"],
        )

    @override_settings(ALLOWED_HOSTS=["localhost", "10.251.74.247"])
    def test_health_accepts_pod_ip_host_header(self):
        response = self.client.get("/health/", HTTP_HOST="10.251.74.247:8000")
        self.assertEqual(response.status_code, 200)


class HealthCheckTests(SimpleTestCase):
    def test_health_returns_ok(self):
        response = self.client.get("/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})


class PrefixedApiTests(SimpleTestCase):
    def test_health_under_script_prefix(self):
        response = self.client.get("/genomeproperties/api/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_list_under_script_prefix(self):
        with patch("genomeproperties.views.list_properties", return_value=[]):
            response = self.client.get("/genomeproperties/api/genome-properties/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_unknown_property_under_script_prefix_is_404(self):
        with patch("genomeproperties.views.serialize_genome_property", return_value=None):
            response = self.client.get("/genomeproperties/api/genome-properties/NOPE/")
        self.assertEqual(response.status_code, 404)


class HierarchyTreeTests(SimpleTestCase):
    def test_unknown_accession_is_none(self):
        with patch("genomeproperties.hierarchy.GenomeProperty.objects") as properties:
            properties.values_list.return_value = []
            self.assertIsNone(build_hierarchy_tree("NOPE"))

    def test_assembles_children_in_step_order_and_skips_cycles(self):
        steps = [
            {"auto_step": 1, "gp_accession_id": "ROOT"},
            {"auto_step": 2, "gp_accession_id": "CHILD"},
            {"auto_step": 3, "gp_accession_id": "GRAND"},
        ]
        evidence = [
            {"auto_step_id": 1, "gp_accession_id": "CHILD"},
            {"auto_step_id": 2, "gp_accession_id": "GRAND"},
            {"auto_step_id": 3, "gp_accession_id": "ROOT"},
        ]
        with (
            patch("genomeproperties.hierarchy.GenomeProperty.objects") as properties,
            patch("genomeproperties.hierarchy.GpStep.objects") as gp_steps,
            patch("genomeproperties.hierarchy.GpStepEvidenceGp.objects") as evidence_gp,
        ):
            properties.values_list.return_value = [
                ("ROOT", "root"),
                ("CHILD", "child"),
                ("GRAND", "grand"),
            ]
            gp_steps.order_by.return_value.values.return_value = steps
            evidence_gp.values.return_value = evidence
            tree = build_hierarchy_tree("ROOT")

        self.assertIsNotNone(tree)
        self.assertEqual(tree["accession"], "ROOT")
        self.assertEqual(tree["children"][0]["accession"], "CHILD")
        self.assertEqual(tree["children"][0]["children"][0]["accession"], "GRAND")
        self.assertEqual(tree["children"][0]["children"][0]["children"], [])


class RestApiTests(SimpleTestCase):
    def test_unknown_hierarchy_accession_is_404(self):
        with patch("genomeproperties.views.build_hierarchy_tree", return_value=None):
            response = self.client.get("/hierarchy/NOPE/")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "Not found")

    def test_unknown_property_is_404(self):
        with patch("genomeproperties.views.serialize_genome_property", return_value=None):
            response = self.client.get("/genome-properties/NOPE/")
        self.assertEqual(response.status_code, 404)

    def test_list_returns_json_array(self):
        with patch(
            "genomeproperties.views.list_properties",
            return_value=[{"accession": "GenProp0001", "description": "Proline"}],
        ):
            response = self.client.get("/genome-properties/?type=PATHWAY")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["accession"], "GenProp0001")

    def test_hierarchy_returns_tree(self):
        tree = {"accession": "ROOT", "description": "root", "children": []}
        with patch("genomeproperties.views.build_hierarchy_tree", return_value=tree):
            response = self.client.get("/hierarchy/ROOT/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), tree)

    def test_legacy_graphql_base_still_serves_hierarchy(self):
        tree = {"accession": "ROOT", "description": "root", "children": []}
        with patch("genomeproperties.views.build_hierarchy_tree", return_value=tree):
            response = self.client.get("/graphql/hierarchy/ROOT/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), tree)

    def test_legacy_prefixed_graphql_base_still_serves_hierarchy(self):
        tree = {"accession": "ROOT", "description": "root", "children": []}
        with patch("genomeproperties.views.build_hierarchy_tree", return_value=tree):
            response = self.client.get("/genomeproperties/api/graphql/hierarchy/ROOT/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), tree)


class SerializeTests(SimpleTestCase):
    def test_unknown_accession_is_none(self):
        with patch("genomeproperties.serialize.GenomeProperty.objects") as properties:
            properties.filter.return_value.values.return_value.first.return_value = None
            self.assertIsNone(serialize_genome_property("NOPE"))

    def test_assembles_literature_links_and_steps(self):
        property_row = {
            "accession": "GenProp0001",
            "type": "PATHWAY",
            "author": "Author",
            "description": "Proline",
            "threshold": 8,
            "comment": "comment",
        }
        with (
            patch("genomeproperties.serialize.GenomeProperty.objects") as properties,
            patch("genomeproperties.serialize.GpLitRef.objects") as lit_refs,
            patch("genomeproperties.serialize.GpDatabaseLink.objects") as db_links,
            patch("genomeproperties.serialize.GpStep.objects") as steps,
            patch("genomeproperties.serialize.GpStepEvidenceGp.objects") as evidence_gp,
            patch("genomeproperties.serialize.GpStepEvidenceIpr.objects") as evidence_ipr,
            patch("genomeproperties.serialize.IprStepToGo.objects") as ipr_to_go,
        ):
            properties.filter.return_value.values.return_value.first.return_value = property_row
            lit_refs.filter.return_value.order_by.return_value.values.return_value = [
                {
                    "list_order": 1,
                    "literature_reference_pmid__pmid": 172079,
                    "literature_reference_pmid__title": "Title",
                    "literature_reference_pmid__author": "Smith",
                    "literature_reference_pmid__journal": "Journal",
                }
            ]
            db_links.filter.return_value.values.return_value = [
                {
                    "db_id": "KEGG",
                    "db_link": "map00400",
                    "comment": "KEGG map",
                    "other_params": None,
                }
            ]
            steps.filter.return_value.order_by.return_value.values.return_value = [
                {"auto_step": 1, "step_id": "Step1", "step_number": 1, "required": 1}
            ]
            evidence_gp.filter.return_value.values.return_value = []
            evidence_ipr.filter.return_value.values.return_value = [
                {
                    "auto_step_id": 1,
                    "interpro_acc": "IPR000001",
                    "signature_acc": "PF00001",
                    "auto_ipr_step": 9,
                }
            ]
            ipr_to_go.filter.return_value.values.return_value = [
                {"auto_ipr_step_id": 9, "go_id": "GO:0000105"}
            ]
            payload = serialize_genome_property("GenProp0001")

        self.assertIsNotNone(payload)
        self.assertEqual(payload["accession"], "GenProp0001")
        self.assertEqual(payload["literature"][0]["pmid"], 172079)
        self.assertEqual(payload["databaseLinks"][0]["dbLink"], "map00400")
        self.assertEqual(payload["steps"][0]["evidence"][0]["goId"], "GO:0000105")
