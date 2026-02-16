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


