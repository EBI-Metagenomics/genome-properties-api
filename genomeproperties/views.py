from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .hierarchy import build_hierarchy_tree
from .serialize import list_genome_properties as list_properties
from .serialize import serialize_genome_property


def health(_request):
    return JsonResponse({"status": "ok"})


@require_GET
def list_genome_properties(request):
    gp_type = request.GET.get("type")
    return JsonResponse(list_properties(gp_type or None), safe=False)


@require_GET
def genome_property_detail(_request, accession):
    payload = serialize_genome_property(accession)
    if payload is None:
        return JsonResponse({"detail": "Not found"}, status=404)
    return JsonResponse(payload)


@require_GET
def hierarchy_detail(_request, accession):
    tree = build_hierarchy_tree(accession)
    if tree is None:
        return JsonResponse({"detail": "Not found"}, status=404)
    return JsonResponse(tree)
