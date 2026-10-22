from django.contrib.staticfiles.handlers import StaticFilesHandler
from django.test import RequestFactory, SimpleTestCase, override_settings

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


class GraphiqlStaticTests(SimpleTestCase):
    @override_settings(
        DEBUG=True,
        STATIC_URL="/genomeproperties/api/static/",
        FORCE_SCRIPT_NAME="/genomeproperties/api",
    )
    def test_graphiql_js_is_served_from_prefixed_path_info(self):
        handler = StaticFilesHandler(lambda *_args, **_kwargs: None)
        request = RequestFactory().get("/genomeproperties/api/static/graphene_django/graphiql.js")
        request.path = "/genomeproperties/api/genomeproperties/api/static/graphene_django/graphiql.js"
        request.path_info = "/genomeproperties/api/static/graphene_django/graphiql.js"
        response = handler.serve(request)
        self.assertEqual(response.status_code, 200)
        body = b"".join(response.streaming_content)
        self.assertIn(b"GraphiQL", body)


class HealthCheckTests(SimpleTestCase):
    def test_health_returns_ok(self):
        response = self.client.get("/health/")
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
