from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class APISchema(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class HealthSchema(APISchema):
    status: str = Field(description="Liveness indicator")


class ErrorSchema(APISchema):
    detail: str
