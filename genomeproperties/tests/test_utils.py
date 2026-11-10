from django.test import SimpleTestCase, override_settings

from genomeproperties.utils import HostAllowList, OrderedUniqueMap, ScriptPrefix


class HostAllowListTests(SimpleTestCase):
    def test_pod_ip_is_appended_for_kubelet_probes(self):
        self.assertEqual(
            HostAllowList.extend(["localhost", "127.0.0.1"], "10.251.74.247"),
            ["localhost", "127.0.0.1", "10.251.74.247"],
        )

    def test_empty_pod_ip_is_ignored(self):
        self.assertEqual(HostAllowList.extend(["localhost"], "", None), ["localhost"])

    @override_settings(ALLOWED_HOSTS=["localhost", "10.251.74.247"])
    def test_health_accepts_pod_ip_host_header(self):
        response = self.client.get("/health/", HTTP_HOST="10.251.74.247:8000")
        self.assertEqual(response.status_code, 200)


class OrderedUniqueMapTests(SimpleTestCase):
    def test_keeps_first_seen_order(self):
        values = OrderedUniqueMap()
        values.add("ROOT", "CHILD")
        values.add("ROOT", "OTHER")
        values.add("ROOT", "CHILD")
        self.assertEqual(values.as_dict()["ROOT"], ["CHILD", "OTHER"])


class ScriptPrefixTests(SimpleTestCase):
    def test_includes_default_and_configured_prefix(self):
        with override_settings(FORCE_SCRIPT_NAME="/custom/api"):
            prefixes = ScriptPrefix.public_prefixes()
        self.assertIn("genomeproperties/api", prefixes)
        self.assertIn("custom/api", prefixes)

    def test_openapi_root_uses_api_v1_without_script_name(self):
        with override_settings(FORCE_SCRIPT_NAME=""):
            self.assertEqual(ScriptPrefix.openapi_root(), "api/v1")

    def test_openapi_root_does_not_repeat_api_under_script_name(self):
        with override_settings(FORCE_SCRIPT_NAME="/genomeproperties/api"):
            self.assertEqual(ScriptPrefix.openapi_root(), "genomeproperties/api/v1")
