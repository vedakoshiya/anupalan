"""Unit tests for the statutory version and supersession graph."""

import unittest
from datetime import date
from uuid import uuid4

from services.ingestion.src.version_graph import (
    InstrumentNode,
    LegalVersionGraph,
)


class TestLegalVersionGraph(unittest.TestCase):
    def setUp(self):
        self.graph = LegalVersionGraph()

        self.inst_base = InstrumentNode(
            id=uuid4(),
            code="INST-GST-JW-001",
            number="11/2017-CT (Rate)",
            title="GST Rates on Services",
            issued_on=date(2017, 6, 28),
            effective_from=date(2017, 7, 1),
        )
        self.inst_amend = InstrumentNode(
            id=uuid4(),
            code="INST-GST-JW-002",
            number="20/2017-CT (Rate)",
            title="Reduction in Textile Job Work Rate to 5%",
            issued_on=date(2017, 8, 22),
            effective_from=date(2017, 8, 22),
        )
        self.inst_comp_old = InstrumentNode(
            id=uuid4(),
            code="INST-GST-COMP-002",
            number="08/2017-CT",
            title="Composition Limit 75 Lakhs",
            issued_on=date(2017, 6, 27),
            effective_from=date(2017, 7, 1),
        )
        self.inst_comp_new = InstrumentNode(
            id=uuid4(),
            code="INST-GST-COMP-003",
            number="14/2019-CT",
            title="Composition Limit 1.5 Crore",
            issued_on=date(2019, 3, 7),
            effective_from=date(2019, 4, 1),
        )

        self.graph.add_instrument(self.inst_base)
        self.graph.add_instrument(self.inst_amend)
        self.graph.add_instrument(self.inst_comp_old)
        self.graph.add_instrument(self.inst_comp_new)

    def test_add_valid_relations(self):
        self.graph.add_relation(
            from_code="INST-GST-JW-002",
            to_code="INST-GST-JW-001",
            relation="amends",
            effective_from=date(2017, 8, 22),
            scope="Entry 26(i)",
        )
        amendments = self.graph.get_amendments("INST-GST-JW-001")
        self.assertEqual(len(amendments), 1)
        self.assertEqual(amendments[0].from_code, "INST-GST-JW-002")

    def test_supersession_resolution_by_date(self):
        self.graph.add_relation(
            from_code="INST-GST-COMP-003",
            to_code="INST-GST-COMP-002",
            relation="supersedes",
            effective_from=date(2019, 4, 1),
        )

        # Before supersession takes effect (e.g. in 2018), old limit applies
        resolved_2018 = self.graph.resolve_in_force_instrument("INST-GST-COMP-002", as_of=date(2018, 1, 1))
        self.assertEqual(resolved_2018, "INST-GST-COMP-002")

        # After supersession takes effect (e.g. in 2020), new limit applies
        resolved_2020 = self.graph.resolve_in_force_instrument("INST-GST-COMP-002", as_of=date(2020, 1, 1))
        self.assertEqual(resolved_2020, "INST-GST-COMP-003")

    def test_cycle_detection_raises_error(self):
        self.graph.add_relation(
            from_code="INST-GST-JW-002",
            to_code="INST-GST-JW-001",
            relation="amends",
            effective_from=date(2017, 8, 22),
        )
        # Attempting to add circular relation: 001 amends 002
        with self.assertRaises(ValueError) as ctx:
            self.graph.add_relation(
                from_code="INST-GST-JW-001",
                to_code="INST-GST-JW-002",
                relation="amends",
                effective_from=date(2017, 9, 1),
            )
        self.assertIn("Cycle detected", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
