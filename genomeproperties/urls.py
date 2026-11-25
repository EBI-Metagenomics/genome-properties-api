from django.contrib import admin
from django.urls import path

from genomeproperties.api.app import api, create_api, script_api
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

# One NinjaAPI per prefix. Reusing a single instance registers its namespace
# twice and Django Ninja refuses to start when FORCE_SCRIPT_NAME adds a prefix.
for index, prefix in enumerate(ScriptPrefix.public_prefixes()):
    urlpatterns.extend(
        [
            path(f"{prefix}/health/", health),
            path(
                f"{prefix}/{ApiPath.VERSION}/",
                create_api(f"gp-api-public-{index}").urls,
            ),
        ]
    )
