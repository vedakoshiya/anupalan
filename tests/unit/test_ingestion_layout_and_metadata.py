"""Unit tests for layout-aware parsing and statutory metadata extraction."""

import unittest
from datetime import date
from services.ingestion.src.layout_parser import LayoutAwareParser
from services.ingestion.src.metadata_extractor import MetadataExtractor


class TestLayoutAndMetadata(unittest.TestCase):
    def setUp(self):
        self.parser = LayoutAwareParser()
        self.extractor = MetadataExtractor()

    def test_layout_parser_extracts_clauses_and_tables(self):
        doc_text = """# Notification No. 11/2017-Central Tax
(1) This notification may be called the Goods and Services Tax Rules.
(a) Job work services shall be taxed as specified below.
| Item | Description | Rate |
|---|---|---|
| 1 | Textiles | 5% |
| 2 | Other | 18% |
(b) Provided that registered principals can avail credit.
"""
        sections = self.parser.parse_pages([doc_text])
        self.assertGreater(len(sections), 0)

        # Check section heading
        sec = sections[0]
        self.assertEqual(sec.heading, "Notification No. 11/2017-Central Tax")

        # Check clauses
        clause_texts = [c.text for c in sec.clauses]
        self.assertTrue(any("Job work services" in t for t in clause_texts))
        self.assertTrue(any(c.clause_type == "proviso" for c in sec.clauses))

        # Check tables
        self.assertEqual(len(sec.tables), 1)
        tbl = sec.tables[0]
        self.assertEqual(tbl.headers, ["Item", "Description", "Rate"])
        self.assertEqual(len(tbl.rows), 2)
        self.assertEqual(tbl.rows[0], ["1", "Textiles", "5%"])

    def test_metadata_extractor(self):
        raw_circular = """
GOVERNMENT OF INDIA
MINISTRY OF FINANCE
DEPARTMENT OF REVENUE
CENTRAL BOARD OF INDIRECT TAXES AND CUSTOMS

Notification No. 20/2017-Central Tax (Rate)
New Delhi, dated the 22nd August, 2017

G.S.R. (E).- In exercise of the powers conferred by sub-section (1) of section 11 of the
Central Goods and Services Tax Act, 2017, the Central Government hereby amends Notification No. 11/2017-Central Tax (Rate).
Rate on textile job work reduced to 5%.
"""
        metadata = self.extractor.extract_metadata(raw_circular, "notif_20_2017.pdf")
        self.assertEqual(metadata.authority, "CBIC")
        self.assertEqual(metadata.instrument_type, "notification")
        self.assertEqual(metadata.number, "20/2017-Central Tax (Rate)")
        self.assertEqual(metadata.issued_on, date(2017, 8, 22))
        self.assertEqual(metadata.jurisdiction, "central")
        self.assertIn("job_work", metadata.subjects)

        # Verify extracted amendment relation
        self.assertEqual(len(metadata.relations), 1)
        rel = metadata.relations[0]
        self.assertEqual(rel["relation"], "amends")
        self.assertIn("11/2017", rel["target_number"])


if __name__ == "__main__":
    unittest.main()
