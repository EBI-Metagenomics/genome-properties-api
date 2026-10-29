from ninja import NinjaAPI

from genomeproperties.api.v1.genome_properties import GenomePropertyAPI
from genomeproperties.api.v1.health import HealthAPI
from genomeproperties.api.v1.hierarchy import HierarchyAPI
from genomeproperties.constants import ApiMeta, ApiPath
from genomeproperties.utils import ScriptPrefix


class GenomePropertiesAPI(NinjaAPI):
    def get_root_path(self, path_params):
        return ScriptPrefix.openapi_root()


class ApiFactory:
    @staticmethod
    def create(urls_namespace: str) -> NinjaAPI:
        api = GenomePropertiesAPI(
            title=ApiMeta.TITLE,
            description=ApiMeta.DESCRIPTION,
            version=ApiMeta.VERSION,
            docs_url=ApiPath.DOCS,
            openapi_url=ApiPath.OPENAPI,
            urls_namespace=urls_namespace,
        )
        HealthAPI().register(api)
        GenomePropertyAPI().register(api)
        HierarchyAPI().register(api)
        return api


def create_api(urls_namespace: str = "gp-api") -> NinjaAPI:
    return ApiFactory.create(urls_namespace)


api = create_api("gp-api")
script_api = create_api("gp-api-script")
prefixed_api = create_api("gp-api-prefixed")
