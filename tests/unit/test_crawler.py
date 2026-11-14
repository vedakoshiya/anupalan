"""Unit tests for RegulatoryGazetteCrawler and IngestionPipeline integration."""

import asyncio
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from services.ingestion.src.crawler import (
    CrawlReport,
    GazetteEntry,
    RegulatoryGazetteCrawler,
)
from services.ingestion.src.pipeline import IngestionPipeline
from services.ingestion.src.storage import LocalImmutableStorage


class TestRegulatoryGazetteCrawler(unittest.TestCase):
    def setUp(self):
        self.crawler = RegulatoryGazetteCrawler(timeout_seconds=5.0, rate_limit_delay=0.0)

    def test_parse_date_valid(self):
        d1 = self.crawler._parse_date("22/08/2017")
        self.assertEqual(d1, date(2017, 8, 22))

        d2 = self.crawler._parse_date("04-05-2024")
        self.assertEqual(d2, date(2024, 5, 4))

        d3 = self.crawler._parse_date("Published on 15.03.2023 by Department")
        self.assertEqual(d3, date(2023, 3, 15))

    def test_parse_date_invalid(self):
        d = self.crawler._parse_date("No date mentioned")
        self.assertIsNone(d)

    def test_extract_subjects(self):
        s1 = self.crawler._extract_subjects("Concessional rate for textile weaving and job work")
        self.assertIn("job_work", s1)

        s2 = self.crawler._extract_subjects("MSME payment delay disallowance under Section 43B(h)")
        self.assertIn("msme_payment", s2)

        s3 = self.crawler._extract_subjects("Threshold limit for composition scheme under section 10")
        self.assertIn("composition", s3)

        s4 = self.crawler._extract_subjects("Guidelines regarding E-Way Bill generation during transit")
        self.assertIn("e_way_bill", s4)

        s5 = self.crawler._extract_subjects("Routine miscellaneous office memorandum")
        self.assertIn("general_compliance", s5)

    def test_parse_html_table(self):
        html_sample = """
        <html>
        <body>
        <table class="table">
            <thead>
                <tr><th>Notification No.</th><th>Date</th><th>Subject</th><th>Download</th></tr>
            </thead>
            <tbody>
                <tr>
                    <td>20/2017-Central Tax (Rate)</td>
                    <td>22-08-2017</td>
                    <td>Seeks to reduce GST rate on job work services in relation to textiles.</td>
                    <td><a href="/resources/notif-20-2017.pdf">View PDF</a></td>
                </tr>
                <tr>
                    <td>04/2024-Central Tax</td>
                    <td>08-04-2024</td>
                    <td>Special procedure to be followed by manufacturers of pan masala and tobacco.</td>
                    <td><a href="notif-04-2024.pdf">PDF (120 KB)</a></td>
                </tr>
                <tr>
                    <td colspan="4">No more records</td>
                </tr>
            </tbody>
        </table>
        </body>
        </html>
        """
        entries = self.crawler.parse_html_table(
            html=html_sample,
            base_url="https://www.cbic.gov.in/htdocs-cbec/gst/",
            authority="CBIC",
        )
        self.assertEqual(len(entries), 2)

        entry1 = entries[0]
        self.assertEqual(entry1.authority, "CBIC")
        self.assertEqual(entry1.notification_number, "20/2017-Central Tax (Rate)")
        self.assertEqual(entry1.issue_date, date(2017, 8, 22))
        self.assertIn("textile", entry1.title)
        self.assertEqual(entry1.pdf_url, "https://www.cbic.gov.in/resources/notif-20-2017.pdf")
        self.assertIn("job_work", entry1.subjects)

        entry2 = entries[1]
        self.assertEqual(entry2.notification_number, "04/2024-Central Tax")
        self.assertEqual(entry2.issue_date, date(2024, 4, 8))
        self.assertEqual(entry2.pdf_url, "https://www.cbic.gov.in/htdocs-cbec/gst/notif-04-2024.pdf")

    def test_crawl_source_with_pipeline_deduplication(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            storage = LocalImmutableStorage(base_directory=Path(tmp_dir))
            pipeline = IngestionPipeline(storage=storage)

            html_sample = """
            <table>
                <tr>
                    <td>Notification 14/2019-Central Tax</td>
                    <td>07-03-2019</td>
                    <td>Threshold limit for composition levy increased to 1.5 Crores.</td>
                    <td><a href="notif-14-2019.pdf">PDF</a></td>
                </tr>
            </table>
            """
            pdf_sample_bytes = b"%PDF-1.4 Mock PDF content for Composition Scheme threshold notification"

            # 1. First crawl execution: Ingests new document
            report1 = asyncio.run(
                self.crawler.crawl_source(
                    source_key="CBIC_GST_NOTIFICATIONS",
                    pipeline=pipeline,
                    max_entries=5,
                    mock_html=html_sample,
                    mock_pdf_bytes=pdf_sample_bytes,
                )
            )
            self.assertEqual(report1.items_discovered, 1)
            self.assertEqual(report1.items_downloaded, 1)
            self.assertEqual(report1.items_ingested, 1)
            self.assertEqual(report1.items_skipped, 0)
            self.assertEqual(len(report1.errors), 0)

            # 2. Second crawl execution: Detects duplicate SHA-256 and skips
            report2 = asyncio.run(
                self.crawler.crawl_source(
                    source_key="CBIC_GST_NOTIFICATIONS",
                    pipeline=pipeline,
                    max_entries=5,
                    mock_html=html_sample,
                    mock_pdf_bytes=pdf_sample_bytes,
                )
            )
            self.assertEqual(report2.items_discovered, 1)
            self.assertEqual(report2.items_downloaded, 1)
            self.assertEqual(report2.items_ingested, 0)
            self.assertEqual(report2.items_skipped, 1)

    def test_crawl_source_error_recorded(self):
        with patch.object(self.crawler, "fetch_page", side_effect=RuntimeError("Connection timeout 504")):
            report = asyncio.run(self.crawler.crawl_source(source_key="CBIC_GST_NOTIFICATIONS"))
            self.assertEqual(len(report.errors), 1)
            self.assertIn("Fatal crawl error", report.errors[0])
            self.assertIn("Connection timeout 504", report.errors[0])


if __name__ == "__main__":
    unittest.main()
