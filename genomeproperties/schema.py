import graphene
from graphene import ObjectType, relay
from graphene_django import DjangoObjectType
from graphene_django.debug import DjangoDebug
from graphene_django.filter import DjangoFilterConnectionField

from .models import (
    GenomeProperty,
    GoTerms,
    GpDatabaseLink,
    GpLitRef,
    GpStep,
    GpStepEvidenceGp,
    GpStepEvidenceIpr,
    GpStepToGo,
    IprStepToGo,
    LiteratureReference,
)


class GenomePropertyNode(DjangoObjectType):
    class Meta:
        model = GenomeProperty
        fields = "__all__"
        filter_fields = {
            "accession": ["exact"],
            "description": ["exact"],
            "type": ["exact", "icontains", "istartswith"],
            "author": ["exact"],
            "threshold": ["lt", "gt"],
        }
        interfaces = (relay.Node,)


class GoTermsNode(DjangoObjectType):
    class Meta:
        model = GoTerms
        fields = "__all__"
        filter_fields = ["go_id", "term", "category"]
        interfaces = (relay.Node,)


class GpDatabaseLinkNode(DjangoObjectType):
    class Meta:
        model = GpDatabaseLink
        fields = "__all__"
        filter_fields = ["gp_accession", "db_id", "db_link"]
        interfaces = (relay.Node,)


class GpLitRefNode(DjangoObjectType):
    class Meta:
        model = GpLitRef
        fields = "__all__"
        filter_fields = ["gp_accession", "literature_reference_pmid", "list_order"]
        interfaces = (relay.Node,)


class GpStepNode(DjangoObjectType):
    class Meta:
        model = GpStep
        fields = "__all__"
        filter_fields = ["gp_accession", "auto_step", "step_number", "step_id", "step_display_name"]
        interfaces = (relay.Node,)


class GpStepEvidenceGpNode(DjangoObjectType):
    class Meta:
        model = GpStepEvidenceGp
        fields = "__all__"
        filter_fields = ["auto_step", "gp_accession", "auto_gp_step"]
        interfaces = (relay.Node,)


class GpStepEvidenceIprNode(DjangoObjectType):
    class Meta:
        model = GpStepEvidenceIpr
        fields = "__all__"
        filter_fields = [
            "auto_step",
            "interpro_acc",
            "signature_acc",
            "sufficient",
            "auto_ipr_step",
        ]
        interfaces = (relay.Node,)


class GpStepToGoNode(DjangoObjectType):
    class Meta:
        model = GpStepToGo
        fields = "__all__"
        filter_fields = ["auto_gp_step", "go"]
        interfaces = (relay.Node,)


class IprStepToGoNode(DjangoObjectType):
    class Meta:
        model = IprStepToGo
        fields = "__all__"
        filter_fields = ["auto_ipr_step", "go"]
        interfaces = (relay.Node,)


class LiteratureReferenceNode(DjangoObjectType):
    class Meta:
        model = LiteratureReference
        fields = "__all__"
        filter_fields = ["pmid", "title", "author", "journal"]
        interfaces = (relay.Node,)


class Query(ObjectType):
    debug = graphene.Field(DjangoDebug, name="_debug")

    genome_property = relay.Node.Field(GenomePropertyNode)
    genome_properties = DjangoFilterConnectionField(GenomePropertyNode)

    go_term = relay.Node.Field(GoTermsNode)
    go_terms = DjangoFilterConnectionField(GoTermsNode)

    gp_database_link = relay.Node.Field(GpDatabaseLinkNode)
    gp_database_links = DjangoFilterConnectionField(GpDatabaseLinkNode)

    gp_lit_ref = relay.Node.Field(GpLitRefNode)
    gp_lit_refs = DjangoFilterConnectionField(GpLitRefNode)

    gp_step = relay.Node.Field(GpStepNode)
    gp_steps = DjangoFilterConnectionField(GpStepNode)

    gp_step_evidence_gp = relay.Node.Field(GpStepEvidenceGpNode)
    all_gp_step_evidence_gp = DjangoFilterConnectionField(GpStepEvidenceGpNode)

    gp_step_evidence_ipr = relay.Node.Field(GpStepEvidenceIprNode)
    all_gp_step_evidence_ipr = DjangoFilterConnectionField(GpStepEvidenceIprNode)

    gp_step_to_go = relay.Node.Field(GpStepToGoNode)
    all_gp_step_to_go = DjangoFilterConnectionField(GpStepToGoNode)

    ipr_step_to_go = relay.Node.Field(IprStepToGoNode)
    all_ipr_step_to_go = DjangoFilterConnectionField(IprStepToGoNode)

    literature_reference = relay.Node.Field(LiteratureReferenceNode)
    literature_references = DjangoFilterConnectionField(LiteratureReferenceNode)


schema = graphene.Schema(query=Query)
