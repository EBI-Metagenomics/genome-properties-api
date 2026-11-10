from django.contrib import admin

from .models import GenomeProperty, LiteratureReference


@admin.register(GenomeProperty)
class GenomePropertyAdmin(admin.ModelAdmin):
    list_display = ("accession", "type", "description", "author", "ispublic")
    search_fields = ("accession", "description", "author")
    list_filter = ("type", "ispublic")
    readonly_fields = [field.name for field in GenomeProperty._meta.fields]


@admin.register(LiteratureReference)
class LiteratureReferenceAdmin(admin.ModelAdmin):
    list_display = ("pmid", "title", "author", "journal")
    search_fields = ("pmid", "title", "author")
    readonly_fields = [field.name for field in LiteratureReference._meta.fields]
