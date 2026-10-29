from django.conf import settings
from django.contrib import admin
from django.urls import path

from . import views


def _rest_routes(prefix="", named=False):
    root = f"{prefix}/" if prefix else ""
    health_kwargs = {"name": "health"} if named else {}
    return [
        path(f"{root}health/", views.health, **health_kwargs),
        path(f"{root}genome-properties/", views.list_genome_properties),
        path(f"{root}genome-properties/<str:accession>/", views.genome_property_detail),
        path(f"{root}hierarchy/<str:accession>/", views.hierarchy_detail),
    ]


urlpatterns = [
    path("admin/", admin.site.urls),
    *_rest_routes(named=True),
    # Leftover VITE_API_URL values still end in /graphql/
    *_rest_routes("graphql"),
]

# NodePort has no ingress rewrite, so the public script prefix must be routed too.
_prefixes = ["genomeproperties/api"]
configured = (settings.FORCE_SCRIPT_NAME or "").strip("/")
if configured and configured not in _prefixes:
    _prefixes.append(configured)

for prefix in _prefixes:
    urlpatterns.extend(_rest_routes(prefix))
    urlpatterns.extend(_rest_routes(f"{prefix}/graphql"))
