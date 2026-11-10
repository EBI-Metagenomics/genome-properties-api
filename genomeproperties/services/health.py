from genomeproperties.constants import HealthStatus
from genomeproperties.schemas import HealthSchema


class HealthService:
    def status(self) -> HealthSchema:
        return HealthSchema(status=HealthStatus.OK)
