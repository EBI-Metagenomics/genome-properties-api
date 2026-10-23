from django.conf import settings
from django.contrib import admin
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from graphene_django.views import GraphQLView

from .views import health

# Unprefixed routes: kubelet /health/ and local /graphql/.
urlpatterns = [
    path("health/", health, name="health"),
    path("admin/", admin.site.urls),
    path("graphql/", csrf_exempt(GraphQLView.as_view(graphiql=True))),
]

# NodePort has no ingress rewrite, so the public script prefix must be routed too.
_prefixes = ["genomeproperties/api"]
configured = (settings.FORCE_SCRIPT_NAME or "").strip("/")
if configured and configured not in _prefixes:
    _prefixes.append(configured)

for prefix in _prefixes:
    urlpatterns.extend(
        [
            path(f"{prefix}/health/", health),
            path(f"{prefix}/graphql/", csrf_exempt(GraphQLView.as_view(graphiql=True))),
        ]
    )
