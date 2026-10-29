from unittest.mock import patch

from django.test import SimpleTestCase

from genomeproperties.services import GenomePropertyService, HierarchyService


class HierarchyServiceTests(SimpleTestCase):
    def test_unknown_accession_is_none(self):
        with patch("genomeproperties.services.hierarchy.GenomeProperty.objects") as properties:
            properties.values_list.return_value = []
            self.assertIsNone(HierarchyService().get_tree("NOPE"))

    def test_assembles_children_in_step_order_and_skips_cycles(self):
        steps = [
            {"auto_step": 1, "gp_accession_id": "ROOT"},
            {"auto_step": 2, "gp_accession_id": "CHILD"},
            {"auto_step": 3, "gp_accession_id": "GRAND"},
        ]
        evidence = [
            {"auto_step_id": 1, "gp_accession_id": "CHILD"},
            {"auto_step_id": 2, "gp_accession_id": "GRAND"},
            {"auto_step_id": 3, "gp_accession_id": "ROOT"},
        ]
        with (
            patch("genomeproperties.services.hierarchy.GenomeProperty.objects") as properties,
            patch("genomeproperties.services.hierarchy.GpStep.objects") as gp_steps,
            patch("genomeproperties.services.hierarchy.GpStepEvidenceGp.objects") as evidence_gp,
        ):
            properties.values_list.return_value = [
                ("ROOT", "root"),
                ("CHILD", "child"),
                ("GRAND", "grand"),
            ]
            gp_steps.order_by.return_value.values.return_value = steps
            evidence_gp.values.return_value = evidence
            tree = HierarchyService().get_tree("ROOT")

        self.assertIsNotNone(tree)
        self.assertEqual(tree.accession, "ROOT")
        self.assertEqual(tree.children[0].accession, "CHILD")
        self.assertEqual(tree.children[0].children[0].accession, "GRAND")
        self.assertEqual(tree.children[0].children[0].children, [])


class GenomePropertyServiceTests(SimpleTestCase):
    def test_unknown_accession_is_none(self):
        with patch(
            "genomeproperties.services.genome_property.GenomeProperty.objects"
        ) as properties:
            properties.filter.return_value.values.return_value.first.return_value = None
            self.assertIsNone(GenomePropertyService().get("NOPE"))

    def test_assembles_literature_links_and_steps(self):
        property_row = {
            "accession": "GenProp0001",
            "type": "PATHWAY",
            "author": "Author",
            "description": "Proline",
            "threshold": 8,
            "comment": "comment",
        }
        with (
            patch("genomeproperties.services.genome_property.GenomeProperty.objects") as properties,
            patch("genomeproperties.services.genome_property.GpLitRef.objects") as lit_refs,
            patch("genomeproperties.services.genome_property.GpDatabaseLink.objects") as db_links,
            patch("genomeproperties.services.genome_property.GpStep.objects") as steps,
            patch(
                "genomeproperties.services.genome_property.GpStepEvidenceGp.objects"
            ) as evidence_gp,
            patch(
                "genomeproperties.services.genome_property.GpStepEvidenceIpr.objects"
            ) as evidence_ipr,
            patch("genomeproperties.services.genome_property.IprStepToGo.objects") as ipr_to_go,
        ):
            properties.filter.return_value.values.return_value.first.return_value = property_row
            lit_refs.filter.return_value.order_by.return_value.values.return_value = [
                {
                    "list_order": 1,
                    "literature_reference_pmid__pmid": 172079,
                    "literature_reference_pmid__title": "Title",
                    "literature_reference_pmid__author": "Smith",
                    "literature_reference_pmid__journal": "Journal",
                }
            ]
            db_links.filter.return_value.values.return_value = [
                {
                    "db_id": "KEGG",
                    "db_link": "map00400",
                    "comment": "KEGG map",
                    "other_params": None,
                }
            ]
            steps.filter.return_value.order_by.return_value.values.return_value = [
                {"auto_step": 1, "step_id": "Step1", "step_number": 1, "required": 1}
            ]
            evidence_gp.filter.return_value.values.return_value = []
            evidence_ipr.filter.return_value.values.return_value = [
                {
                    "auto_step_id": 1,
                    "interpro_acc": "IPR000001",
                    "signature_acc": "PF00001",
                    "auto_ipr_step": 9,
                }
            ]
            ipr_to_go.filter.return_value.values.return_value = [
                {"auto_ipr_step_id": 9, "go_id": "GO:0000105"}
            ]
            payload = GenomePropertyService().get("GenProp0001")

        self.assertIsNotNone(payload)
        self.assertEqual(payload.accession, "GenProp0001")
        self.assertEqual(payload.literature[0].pmid, 172079)
        self.assertEqual(payload.database_links[0].db_link, "map00400")
        self.assertEqual(payload.steps[0].evidence[0].go_id, "GO:0000105")
        dumped = payload.model_dump(by_alias=True)
        self.assertEqual(dumped["databaseLinks"][0]["dbLink"], "map00400")
        self.assertEqual(dumped["steps"][0]["evidence"][0]["goId"], "GO:0000105")
