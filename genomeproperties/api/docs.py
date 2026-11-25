from ninja.openapi.docs import Swagger

from genomeproperties.constants import ApiPath


class RequestRelativeSwagger(Swagger):
    """Load openapi.json as a sibling of the docs page.

    Django reverse() prepends FORCE_SCRIPT_NAME while this app is also mounted
    at ``api/v1``, which becomes ``/genomeproperties/api/api/v1/openapi.json``.
    A relative URL works for local ``/api/v1/docs`` and for the prefixed
    Kubernetes path without depending on script-name rewriting.
    """

    def get_openapi_url(self, api, path_params):
        return ApiPath.OPENAPI.lstrip("/")
