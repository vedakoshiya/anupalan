"""End-to-End Integration Test for the Anupalan Compliance System.

Tests the full lifecycle:
1. Ingestion of statutory circulars into structured chunks with contextual headers.
2. Legal Version Graph assembly and amendment/supersession chaining.
3. Public FastAPI endpoint interfaces (/v1/ask, /v1/feedback, /v1/health, /v1/chunks/{id}).
4. Multi-language queries in Gujlish and English.
5. Temporal rule evaluation (as-of date supersession).
6. Grounded citations, numeric guardrails, and graceful abstention.
"""

import unittest
from datetime import date
from uuid import uuid4

from packages.generation.src.generation.schemas import (
    AskRequest,
    AskResponse,
    FeedbackRequest,
)
from services.api.src.main import (
    CHUNKS_DB,
    FEEDBACK_DB,
    VERSION_GRAPH,
    ask_question,
    chunker,
    get_chunk,
    health_check,
    submit_feedback,
)
from services.ingestion.src.chunker import StatutoryChunk
from services.ingestion.src.version_graph import InstrumentNode


class TestEndToEndPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 1. Clear in-memory DBs for clean test state
        CHUNKS_DB.clear()
        FEEDBACK_DB.clear()

        # 2. Ingest Test Instruments into Version Graph and Chunks DB
        inst_jw_id = uuid4()
        inst_comp_old_id = uuid4()
        inst_comp_new_id = uuid4()

        # Add Nodes to Version Graph
        node_jw = InstrumentNode(
            id=inst_jw_id,
            code="INST-GST-JW-002",
            number="Notification 20/2017-CT (Rate)",
            title="Reduced GST rate on textile job work to 5%",
            issued_on=date(2017, 8, 22),
            effective_from=date(2017, 8, 22),
        )
        node_comp_old = InstrumentNode(
            id=inst_comp_old_id,
            code="INST-GST-COMP-002",
            number="Notification 08/2017-CT",
            title="Composition Scheme threshold limit is 75 Lakhs",
            issued_on=date(2017, 6, 27),
            effective_from=date(2017, 7, 1),
            effective_to=date(2019, 4, 1),
        )
        node_comp_new = InstrumentNode(
            id=inst_comp_new_id,
            code="INST-GST-COMP-003",
            number="Notification 14/2019-CT",
            title="Composition Scheme threshold increased to 15000000 (1.5 Crore)",
            issued_on=date(2019, 3, 7),
            effective_from=date(2019, 4, 1),
        )

        VERSION_GRAPH.add_instrument(node_jw)
        VERSION_GRAPH.add_instrument(node_comp_old)
        VERSION_GRAPH.add_instrument(node_comp_new)

        # Add supersession edge
        VERSION_GRAPH.add_relation(
            from_code="INST-GST-COMP-003",
            to_code="INST-GST-COMP-002",
            relation="supersedes",
            effective_from=date(2019, 4, 1),
        )

        # 3. Create Chunks via Structure-Aware Chunker
        jw_clauses = [
            {
                "path": "Entry 26(i)",
                "text": "Rate of GST on textile job work is 5% for all yarn and fabrics.",
                "type": "clause",
            }
        ]
        jw_chunks = chunker.chunk_clauses(
            instrument_id=inst_jw_id,
            authority="CBIC",
            instrument_title="Notification 20/2017-CT (Rate)",
            clauses=jw_clauses,
            effective_from=date(2017, 8, 22),
            effective_to=None,
            jurisdiction="central",
            subjects=["job_work", "textiles"],
            language="gu",
        )
        for c in jw_chunks:
            CHUNKS_DB[c.id] = c

        comp_old_clauses = [
            {
                "path": "Para 1",
                "text": "The turnover limit for composition scheme under Section 10 is 75 Lakhs.",
                "type": "clause",
            }
        ]
        comp_old_chunks = chunker.chunk_clauses(
            instrument_id=inst_comp_old_id,
            authority="CBIC",
            instrument_title="Notification 08/2017-CT",
            clauses=comp_old_clauses,
            effective_from=date(2017, 7, 1),
            effective_to=date(2019, 4, 1),
            jurisdiction="central",
            subjects=["composition"],
            language="en",
        )
        for c in comp_old_chunks:
            CHUNKS_DB[c.id] = c

        comp_new_clauses = [
            {
                "path": "Para 1",
                "text": "The enhanced turnover limit for composition scheme under Section 10 is 15000000 (1.5 Crore).",
                "type": "clause",
            }
        ]
        comp_new_chunks = chunker.chunk_clauses(
            instrument_id=inst_comp_new_id,
            authority="CBIC",
            instrument_title="Notification 14/2019-CT",
            clauses=comp_new_clauses,
            effective_from=date(2019, 4, 1),
            effective_to=None,
            jurisdiction="central",
            subjects=["composition"],
            language="en",
        )
        for c in comp_new_chunks:
            CHUNKS_DB[c.id] = c

    @classmethod
    def tearDownClass(cls):
        # Reset in-memory DBs to keep test suites hermetic
        CHUNKS_DB.clear()
        FEEDBACK_DB.clear()
        VERSION_GRAPH.nodes.clear()
        VERSION_GRAPH.edges.clear()

    def test_01_health_endpoint(self):
        """Verifies GET /v1/health returns healthy status and indexed chunk count."""
        data = health_check()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["indexed_chunks"], 3)
        self.assertEqual(data["version"], "0.1.0")

    def test_02_ask_gujlish_job_work_query(self):
        """Tests owner asking in Gujlish ('Job work par GST kevi rite lage?').

        Verifies:
        - Response language is Gujarati ('gu')
        - Grounded claim cites Notification 20/2017-CT (Rate)
        - Numeric rate (5%) is strictly verified
        """
        req = AskRequest(
            query="Job work par GST kevi rite lage?",
            as_of=date(2026, 10, 27),
        )
        resp = ask_question(req)

        self.assertIsInstance(resp, AskResponse)
        self.assertFalse(resp.abstained)
        self.assertEqual(resp.language, "gu")
        self.assertGreater(len(resp.claims), 0)

        # Verify citation
        top_claim = resp.claims[0]
        self.assertIn("5%", top_claim.text)
        self.assertGreater(len(top_claim.citations), 0)
        citation = top_claim.citations[0]
        self.assertEqual(citation.instrument, "Notification 20/2017-CT (Rate)")
        self.assertEqual(citation.clause, "Entry 26(i)")
        self.assertEqual(citation.effective_from, date(2017, 8, 22))

    def test_03_temporal_supersession_rule(self):
        """Tests temporal law engine:

        - As of 2018-01-01: Composition limit returns 75 Lakhs (Notification 08/2017)
        - As of 2024-01-01: Composition limit returns 15000000 / 1.5 Crore (Notification 14/2019)
        """
        # Historical query in 2018
        req_2018 = AskRequest(
            query="Composition scheme limit ketli hati?",
            as_of=date(2018, 1, 1),
        )
        resp_2018 = ask_question(req_2018)
        self.assertFalse(resp_2018.abstained)
        self.assertEqual(resp_2018.claims[0].citations[0].instrument, "Notification 08/2017-CT")
        self.assertIn("75 Lakhs", resp_2018.claims[0].text)

        # Current query in 2024 (After supersession)
        req_2024 = AskRequest(
            query="Composition scheme limit ketli che?",
            as_of=date(2024, 1, 1),
        )
        resp_2024 = ask_question(req_2024)
        self.assertFalse(resp_2024.abstained)
        self.assertEqual(resp_2024.claims[0].citations[0].instrument, "Notification 14/2019-CT")
        self.assertIn("15000000", resp_2024.claims[0].text)

    def test_04_abstention_on_out_of_scope(self):
        """Verifies system gracefully abstains when evidence is insufficient or query is out-of-scope."""
        req = AskRequest(
            query="Mane income tax ketlo bharvo pade?",
            as_of=date(2026, 10, 27),
        )
        resp = ask_question(req)

        self.assertTrue(resp.abstained)
        self.assertEqual(len(resp.claims), 0)
        self.assertGreater(len(resp.next_steps), 0)
        self.assertIn("આ સિસ્ટમ માત્ર સત્તાવાર પરિપત્રો", resp.disclaimer)

    def test_05_feedback_submission(self):
        """Verifies user can submit rating and reason code for an answer."""
        fb_req = FeedbackRequest(
            answer_id=uuid4(),
            rating=1,
            reason_code="accurate_citation",
            comment="Perfect citation of Notification 20/2017.",
        )
        resp = submit_feedback(fb_req)
        self.assertEqual(resp["status"], "recorded")
        self.assertEqual(len(FEEDBACK_DB), 1)

    def test_06_get_chunk_by_id(self):
        """Verifies GET /v1/chunks/{id} returns chunk detail."""
        chunk_id = next(iter(CHUNKS_DB.keys()))
        chunk_data = get_chunk(chunk_id)
        self.assertEqual(chunk_data["id"], chunk_id)
        self.assertIn("Notification", chunk_data["instrument_title"])


if __name__ == "__main__":
    unittest.main()
