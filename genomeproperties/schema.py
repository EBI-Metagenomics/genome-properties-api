import graphene
from graphene_django.debug import DjangoDebug

import web.schema


class Query(web.schema.Query, graphene.ObjectType):
    debug = graphene.Field(DjangoDebug, name="_debug")


schema = graphene.Schema(query=Query)
