# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class GenomeProperty(models.Model):
    accession = models.CharField(primary_key=True, max_length=11)
    description = models.CharField(max_length=255)
    type = models.CharField(max_length=30)
    author = models.TextField()
    threshold = models.IntegerField()
    comment = models.TextField(blank=True, null=True)
    private = models.TextField(blank=True, null=True)
    ispublic = models.IntegerField()
    checked = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'genome_property'


class GoTerms(models.Model):
    go_id = models.CharField(primary_key=True, max_length=10)
    term = models.TextField()
    category = models.CharField(max_length=45)

    class Meta:
        managed = False
        db_table = 'go_terms'


class GpDatabaseLink(models.Model):
    gp_accession = models.ForeignKey(GenomeProperty, models.PROTECT, primary_key=True, db_column='gp_accession')
    db_id = models.TextField()
    db_link = models.TextField()
    other_params = models.TextField(blank=True, null=True)
    comment = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'gp_database_link'
        unique_together = ('gp_accession', 'db_id')


class GpLitRef(models.Model):
    gp_accession = models.ForeignKey(GenomeProperty, models.PROTECT, primary_key=True, db_column='gp_accession')
    literature_reference_pmid = models.ForeignKey('LiteratureReference', models.PROTECT, db_column='literature_reference_pmid')
    list_order = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'gp_lit_ref'
        unique_together = ('gp_accession', 'literature_reference_pmid')


class GpStep(models.Model):
    gp_accession = models.ForeignKey(GenomeProperty, models.PROTECT, db_column='gp_accession')
    auto_step = models.AutoField(primary_key=True)
    step_number = models.IntegerField()
    step_id = models.TextField()
    step_display_name = models.TextField(blank=True, null=True)
    required = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'gp_step'


class GpStepEvidenceGp(models.Model):
    auto_step = models.ForeignKey(GpStep, models.PROTECT, db_column='auto_step')
    gp_accession = models.ForeignKey(GenomeProperty, models.PROTECT, db_column='gp_accession')
    auto_gp_step = models.AutoField(primary_key=True)

    class Meta:
        managed = False
        db_table = 'gp_step_evidence_gp'


class GpStepEvidenceIpr(models.Model):
    auto_step = models.ForeignKey(GpStep, models.PROTECT, db_column='auto_step')
    interpro_acc = models.CharField(max_length=9)
    signature_acc = models.CharField(max_length=45)
    sufficient = models.IntegerField()
    auto_ipr_step = models.AutoField(primary_key=True)

    class Meta:
        managed = False
        db_table = 'gp_step_evidence_ipr'


class GpStepToGo(models.Model):
    auto_gp_step = models.ForeignKey(GpStepEvidenceGp, models.PROTECT, primary_key=True, db_column='auto_gp_step')
    go = models.ForeignKey(GoTerms, models.PROTECT)

    class Meta:
        managed = False
        db_table = 'gp_step_to_go'
        unique_together = ('auto_gp_step', 'go')


class IprStepToGo(models.Model):
    auto_ipr_step = models.ForeignKey(GpStepEvidenceIpr, models.PROTECT, primary_key=True, db_column='auto_ipr_step')
    go = models.ForeignKey(GoTerms, models.PROTECT)

    class Meta:
        managed = False
        db_table = 'ipr_step_to_go'
        unique_together = ('auto_ipr_step', 'go')


class LiteratureReference(models.Model):
    pmid = models.IntegerField(primary_key=True)
    title = models.TextField(blank=True, null=True)
    author = models.TextField(blank=True, null=True)
    journal = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'literature_reference'


class PropDef(models.Model):
    prop_def_id = models.IntegerField(primary_key=True)
    property = models.CharField(unique=True, max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    private = models.TextField(blank=True, null=True)
    prop_type = models.CharField(max_length=30, blank=True, null=True)
    role_id = models.IntegerField(blank=True, null=True)
    prop_acc = models.CharField(max_length=11)
    ispublic = models.IntegerField()
    thresh = models.IntegerField()
    eval_method = models.CharField(max_length=32, blank=True, null=True)
    sub_property = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'prop_def'


class PropGoLink(models.Model):
    prop_def = models.ForeignKey(PropDef, models.PROTECT, primary_key=True, db_column='prop_def')
    go_id = models.CharField(max_length=10)
    get_go = models.IntegerField(db_column='get_GO')  # Field name made lowercase.
    curated = models.IntegerField()
    curation_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'prop_go_link'
        unique_together = ('prop_def', 'go_id')


class PropLink(models.Model):
    parent = models.ForeignKey(PropDef, models.PROTECT, related_name='%(class)s_parent', primary_key=True)
    child = models.ForeignKey(PropDef, models.PROTECT, related_name='%(class)s_child')
    link_type = models.CharField(max_length=12)
    link_value = models.FloatField(blank=True, null=True)
    link_string = models.CharField(max_length=255, blank=True, null=True)
    link_int = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'prop_link'
        unique_together = (('parent', 'child', 'link_type', 'link_string'),)


class PropRef(models.Model):
    prop_def = models.ForeignKey(PropDef, models.PROTECT, primary_key=True, db_column='prop_def')
    ref_num = models.IntegerField()
    ref_type = models.CharField(max_length=10)
    accession = models.CharField(max_length=20, blank=True, null=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    authors = models.CharField(max_length=255, blank=True, null=True)
    citation = models.CharField(max_length=80, blank=True, null=True)
    comment = models.CharField(max_length=1000, blank=True, null=True)
    url = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'prop_ref'
        unique_together = (('prop_def', 'ref_num', 'ref_type'),)


class PropStep(models.Model):
    prop_step_id = models.AutoField(primary_key=True)
    prop_def = models.ForeignKey(PropDef, models.PROTECT)
    step_num = models.CharField(max_length=8)
    step_name = models.CharField(max_length=255, blank=True, null=True)
    in_rule = models.IntegerField(blank=True, null=True)
    branch = models.CharField(max_length=8)
    drop_name = models.CharField(max_length=255, blank=True, null=True)
    prop_def_link_type = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'prop_step'
        unique_together = (('prop_def', 'prop_step_id'),)


class StepEvLink(models.Model):
    step_ev_id = models.AutoField(primary_key=True)
    prop_step = models.ForeignKey(PropStep, models.PROTECT)
    query = models.CharField(max_length=30)
    method = models.CharField(max_length=15)
    get_go = models.IntegerField(db_column='get_GO')  # Field name made lowercase.
    prop_step_link_type = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'step_ev_link'
        unique_together = (('prop_step', 'step_ev_id'),)
