from graphene import relay, ObjectType
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField

from web.models import GenomeProperty, GoTerms, GpDatabaseLink, GpLitRef, GpStep, GpStepEvidenceGp, GpStepEvidenceIpr, \
    GpStepToGo, IprStepToGo, LiteratureReference, PropDef, PropGoLink, PropLink, PropRef, PropStep, StepEvLink


class GenomePropertyNode(DjangoObjectType):
    class Meta:
        model = GenomeProperty
        filter_fields = {
            'accession': ['exact'],
            'description': ['exact'],
            'type': ['exact', 'icontains', 'istartswith'],
            'author': ['exact'],
            'threshold': ['lt', 'gt'],
        }
        interfaces = (relay.Node, )


class GoTermsNode(DjangoObjectType):
    class Meta:
        model = GoTerms
        filter_fields = ['go_id', 'term', 'category']
        interfaces = (relay.Node, )


class GpDatabaseLinkNode(DjangoObjectType):
    class Meta:
        model = GpDatabaseLink
        filter_fields = ['gp_accession', 'db_id', 'db_link']
        interfaces = (relay.Node, )


class GpLitRefNode(DjangoObjectType):
    class Meta:
        model = GpLitRef
        filter_fields = ['gp_accession', 'literature_reference_pmid', 'list_order']
        interfaces = (relay.Node, )


class GpStepNode(DjangoObjectType):
    class Meta:
        model = GpStep
        filter_fields = ['gp_accession', 'auto_step', 'step_number', 'step_id', 'step_display_name']
        interfaces = (relay.Node, )


class GpStepEvidenceGpNode(DjangoObjectType):
    class Meta:
        model = GpStepEvidenceGp
        filter_fields = ['auto_step', 'gp_accession', 'auto_gp_step']
        interfaces = (relay.Node, )


class GpStepEvidenceIprNode(DjangoObjectType):
    class Meta:
        model = GpStepEvidenceIpr
        filter_fields = ['auto_step', 'interpro_acc', 'signature_acc', 'sufficient', 'auto_ipr_step']
        interfaces = (relay.Node, )


class GpStepToGoNode(DjangoObjectType):
    class Meta:
        model = GpStepToGo
        filter_fields = ['auto_gp_step', 'go']
        interfaces = (relay.Node, )


class IprStepToGoNode(DjangoObjectType):
    class Meta:
        model = IprStepToGo
        filter_fields = ['auto_ipr_step', 'go']
        interfaces = (relay.Node, )


class LiteratureReferenceNode(DjangoObjectType):
    class Meta:
        model = LiteratureReference
        filter_fields = ['pmid', 'title', 'author', 'journal']
        interfaces = (relay.Node, )


class PropDefNode(DjangoObjectType):
    class Meta:
        model = PropDef
        filter_fields = ['prop_def_id', 'property', 'prop_type', 'prop_acc', 'thresh', 'ispublic']
        interfaces = (relay.Node, )


class PropGoLinkNode(DjangoObjectType):
    class Meta:
        model = PropGoLink
        filter_fields = ['prop_def', 'go_id']
        interfaces = (relay.Node, )


class PropLinkNode(DjangoObjectType):
    class Meta:
        model = PropLink
        filter_fields = ['parent', 'child']
        interfaces = (relay.Node, )


class PropRefNode(DjangoObjectType):
    class Meta:
        model = PropRef
        filter_fields = ['prop_def']
        interfaces = (relay.Node, )


class PropStepNode(DjangoObjectType):
    class Meta:
        model = PropStep
        filter_fields = ['prop_step_id', 'prop_def']
        interfaces = (relay.Node, )


class StepEvLinkNode(DjangoObjectType):
    class Meta:
        model = StepEvLink
        filter_fields = ['step_ev_id', 'prop_step']
        interfaces = (relay.Node, )


class Query(ObjectType):
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

    prop_def = relay.Node.Field(PropDefNode)
    all_prop_def = DjangoFilterConnectionField(PropDefNode)

    prop_go_link = relay.Node.Field(PropGoLinkNode)
    all_prop_go_link = DjangoFilterConnectionField(PropGoLinkNode)

    prop_link = relay.Node.Field(PropLinkNode)
    prop_links = DjangoFilterConnectionField(PropLinkNode)

    prop_ref = relay.Node.Field(PropRefNode)
    all_prop_ref = DjangoFilterConnectionField(PropRefNode)

    prop_step = relay.Node.Field(PropStepNode)
    prop_steps = DjangoFilterConnectionField(PropStepNode)

    step_ev_link = relay.Node.Field(StepEvLinkNode)
    all_step_ev_link = DjangoFilterConnectionField(StepEvLinkNode)
