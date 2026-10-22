from django.test import SimpleTestCase, override_settings
from django.urls import reverse

from genomeproperties.schema import schema
from genomeproperties.settings import _extend_allowed_hosts


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
        response = self.client.get(reverse("health"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})


class SchemaTests(SimpleTestCase):
    def test_query_type_exposes_genome_properties(self):
        query_type = schema.graphql_schema.get_type("Query")
        field_names = set(query_type.fields)
        self.assertIn("genomeProperties", field_names)
        self.assertIn("goTerms", field_names)
        self.assertIn("literatureReferences", field_names)

    @override_settings(DEBUG=True)
    def test_graphql_rejects_malformed_query(self):
        response = self.client.post(
            "/graphql/",
            data={"query": "{ genomeProperties { edges { node { notAField } } } }"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("errors", response.json())
