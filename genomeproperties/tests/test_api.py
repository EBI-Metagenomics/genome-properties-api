from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from genomeproperties.schemas import (
    GenomePropertyDetailSchema,
    GenomePropertySummarySchema,
    HierarchyNodeSchema,
)
from genomeproperties.services import GenomePropertyService, HierarchyService


class HealthCheckTests(SimpleTestCase):
    def test_health_returns_ok(self):
        response = self.client.get("/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_versioned_health_returns_ok(self):
        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})


class PrefixedApiTests(SimpleTestCase):
    def test_health_under_script_prefix(self):
        response = self.client.get("/genomeproperties/api/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_list_under_script_prefix(self):
        with patch.object(GenomePropertyService, "list_by_type", return_value=[]):
            response = self.client.get("/genomeproperties/api/v1/genome-properties")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_unknown_property_under_script_prefix_is_404(self):
        with patch.object(GenomePropertyService, "get", return_value=None):
            response = self.client.get("/genomeproperties/api/v1/genome-properties/NOPE")
        self.assertEqual(response.status_code, 404)


class RestApiTests(SimpleTestCase):
    def test_unknown_hierarchy_accession_is_404(self):
        with patch.object(HierarchyService, "get_tree", return_value=None):
            response = self.client.get("/api/v1/hierarchy/NOPE")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "Not found")

    def test_unknown_property_is_404(self):
        with patch.object(GenomePropertyService, "get", return_value=None):
            response = self.client.get("/api/v1/genome-properties/NOPE")
        self.assertEqual(response.status_code, 404)

    def test_list_returns_json_array(self):
        summaries = [GenomePropertySummarySchema(accession="GenProp0001", description="Proline")]
        with patch.object(GenomePropertyService, "list_by_type", return_value=summaries):
            response = self.client.get("/api/v1/genome-properties?type=PATHWAY")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["accession"], "GenProp0001")

    def test_hierarchy_returns_tree(self):
        tree = HierarchyNodeSchema(accession="ROOT", description="root", children=[])
        with patch.object(HierarchyService, "get_tree", return_value=tree):
            response = self.client.get("/api/v1/hierarchy/ROOT")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"accession": "ROOT", "description": "root", "children": []},
        )

    def test_property_detail_uses_camel_case_aliases(self):
        payload = GenomePropertyDetailSchema(
            accession="GenProp0001",
            type="PATHWAY",
            author="Author",
            description="Proline",
            threshold=8,
            comment="comment",
            literature=[],
            database_links=[],
            steps=[],
        )
        with patch.object(GenomePropertyService, "get", return_value=payload):
            response = self.client.get("/api/v1/genome-properties/GenProp0001")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("databaseLinks", body)
        self.assertIn("steps", body)


class OpenApiTests(SimpleTestCase):
    def test_openapi_schema_is_published(self):
        response = self.client.get("/api/v1/openapi.json")
        self.assertEqual(response.status_code, 200)
        schema = response.json()
        self.assertEqual(schema["info"]["title"], "Genome Properties API")
        paths = schema["paths"]
        self.assertIn("/api/v1/health", paths)
        self.assertIn("/api/v1/genome-properties", paths)
        self.assertIn("/api/v1/genome-properties/{accession}", paths)
        self.assertIn("/api/v1/hierarchy/{accession}", paths)

    def test_swagger_ui_is_published(self):
        response = self.client.get("/api/v1/docs")
        self.assertEqual(response.status_code, 200)
        self.assertIn("swagger", response.content.decode().lower())

    @override_settings(FORCE_SCRIPT_NAME="/genomeproperties/api")
    def test_openapi_paths_do_not_repeat_api_under_script_prefix(self):
        response = self.client.get("/api/v1/openapi.json")
        self.assertEqual(response.status_code, 200)
        paths = response.json()["paths"]
        self.assertIn("/genomeproperties/api/v1/health", paths)
        self.assertIn("/genomeproperties/api/v1/genome-properties", paths)
        self.assertNotIn("/genomeproperties/api/api/v1/health", paths)
        self.assertNotIn("/genomeproperties/api/api/v1/genome-properties", paths)
