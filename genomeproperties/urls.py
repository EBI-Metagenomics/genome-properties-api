from django.contrib import admin
from django.urls import path

from genomeproperties.api.app import api, prefixed_api, script_api
from genomeproperties.api.v1.health import HealthAPI
from genomeproperties.constants import ApiPath
from genomeproperties.utils import ScriptPrefix

health = HealthAPI().as_django_view()

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health, name="health"),
    path(f"{ApiPath.ROOT}/", api.urls),
    # FORCE_SCRIPT_NAME=/genomeproperties/api leaves PATH_INFO as /v1/...
    path(f"{ApiPath.VERSION}/", script_api.urls),
]

for prefix in ScriptPrefix.public_prefixes():
    urlpatterns.extend(
        [
            path(f"{prefix}/health/", health),
            path(f"{prefix}/{ApiPath.VERSION}/", prefixed_api.urls),
        ]
    )
