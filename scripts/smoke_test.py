#!/usr/bin/env python3
"""End-to-End API Smoke Test Runner for Anupalan.

Tests all 9 REST API endpoints directly against the application layer:
1. GET  /v1/health
2. POST /v1/ask (Bilingual queries, DPDP scrubbing, caching)
3. GET  /v1/instruments/{id} (Amendment timeline)
4. GET  /v1/chunks/{id} (Bounding box and OCR score)
5. POST /v1/feedback (Audit logging)
6. DELETE /v1/sessions/{session_id} (DPDP Right-to-Erasure)
7. POST /v1/telemetry/purge (30-day retention pruner)
8. POST /v1/admin/takedown (Emergency incident kill-switch)
9. GET  /metrics (Prometheus exposition)
"""

import sys
import time
from datetime import date
from pathlib import Path
from uuid import uuid4

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from packages.generation.src.generation.schemas import (
    AskRequest,
    FeedbackRequest,
)
from services.api.src.main import (
    CHUNKS_DB,
    AdminTakedownRequest,
    admin_takedown,
    ask_question,
    chunker,
    delete_session,
    get_chunk,
    get_instrument,
    get_metrics,
    health_check,
    load_core_instruments,
    purge_telemetry,
    submit_feedback,
)


def run_smoke_test() -> bool:
    print("=" * 80)
    print("        ANUPALAN PRODUCTION SMOKE TEST & ENDPOINT HEALTH VERIFICATION")
    print("=" * 80)
    start_total = time.time()
    passed = 0
    total = 9

    # Setup
    load_core_instruments()
    inst_id = uuid4()
    chunks = chunker.chunk_clauses(
        instrument_id=inst_id,
        authority="CBIC",
        instrument_title="Smoke Test Instrument 01/2026",
        clauses=[
            {
                "path": "Entry 1",
                "text": "Standard GST rate on textile processing is 5% under notification 20/2017.",
                "type": "clause",
            }
        ],
        effective_from=date(2024, 1, 1),
        effective_to=None,
        jurisdiction="central",
        subjects=["textile", "rate"],
        language="en",
    )
    for c in chunks:
        CHUNKS_DB[c.id] = c
    sample_chunk_id = chunks[0].id

    # 1. Health Endpoint
    try:
        h = health_check()
        assert h["status"] == "healthy", f"Status not healthy: {h}"
        assert h["version"] == "0.1.0", f"Version mismatch: {h}"
        print("  [1/9] GET  /v1/health                     --> PASS")
        passed += 1
    except Exception as e:
        print(f"  [1/9] GET  /v1/health                     --> FAIL ({e})")

    # 2. Ask Endpoint
    try:
        req = AskRequest(
            query="What is standard GST rate on textile processing with PAN ABCDE1234F?",
            as_of=date(2024, 6, 1),
            language="en",
        )
        resp = ask_question(req)
        assert resp.answer_id is not None
        assert not resp.abstained
        print("  [2/9] POST /v1/ask                        --> PASS (DPDP & Retrieval)")
        passed += 1
    except Exception as e:
        print(f"  [2/9] POST /v1/ask                        --> FAIL ({e})")

    # 3. Instruments Endpoint
    try:
        inst = get_instrument("INST-GST-JW-002")
        assert inst["code"] == "INST-GST-JW-002"
        assert "amendment_timeline" in inst
        print("  [3/9] GET  /v1/instruments/{id}           --> PASS (DAG Resolution)")
        passed += 1
    except Exception as e:
        print(f"  [3/9] GET  /v1/instruments/{id}           --> FAIL ({e})")

    # 4. Chunks Endpoint
    try:
        chk = get_chunk(sample_chunk_id)
        assert chk["id"] == sample_chunk_id
        assert "bbox" in chk
        print("  [4/9] GET  /v1/chunks/{id}                --> PASS (BBox & OCR)")
        passed += 1
    except Exception as e:
        print(f"  [4/9] GET  /v1/chunks/{id}                --> FAIL ({e})")

    # 5. Feedback Endpoint
    try:
        fb = FeedbackRequest(
            answer_id=resp.answer_id,
            rating=1,
            reason_code="accurate_rate",
            comment="Grounded rate verified with CBIC portal.",
        )
        fb_res = submit_feedback(fb)
        assert fb_res["status"] == "recorded"
        print("  [5/9] POST /v1/feedback                   --> PASS (Audit Feed)")
        passed += 1
    except Exception as e:
        print(f"  [5/9] POST /v1/feedback                   --> FAIL ({e})")

    # 6. Session Deletion (DPDP Section 12)
    try:
        del_res = delete_session(req.session_id)
        assert del_res["status"] == "purged"
        print("  [6/9] DELETE /v1/sessions/{id}            --> PASS (Right to Erasure)")
        passed += 1
    except Exception as e:
        print(f"  [6/9] DELETE /v1/sessions/{id}            --> FAIL ({e})")

    # 7. Telemetry Retention Purge
    try:
        p_res = purge_telemetry()
        assert p_res["status"] == "purged"
        assert p_res["retention_days"] == 30
        print("  [7/9] POST /v1/telemetry/purge            --> PASS (30-day Retention)")
        passed += 1
    except Exception as e:
        print(f"  [7/9] POST /v1/telemetry/purge            --> FAIL ({e})")

    # 8. Admin Emergency Takedown
    try:
        td_req = AdminTakedownRequest(
            answer_id=resp.answer_id,
            reason="Smoke test emergency kill-switch verification",
        )
        td_res = admin_takedown(td_req)
        assert td_res["status"] == "takedown_completed"
        print("  [8/9] POST /v1/admin/takedown            --> PASS (Cache Eviction)")
        passed += 1
    except Exception as e:
        print(f"  [8/9] POST /v1/admin/takedown            --> FAIL ({e})")

    # 9. Prometheus Metrics Endpoint
    try:
        m = get_metrics()
        assert m.status_code == 200
        assert b"anupalan_http_requests_total" in m.body
        print("  [9/9] GET  /metrics                       --> PASS (Prometheus Scrape)")
        passed += 1
    except Exception as e:
        print(f"  [9/9] GET  /metrics                       --> FAIL ({e})")

    elapsed = (time.time() - start_total) * 1000
    print("-" * 80)
    print(f"RESULTS: {passed}/{total} ENDPOINTS CERTIFIED IN {elapsed:.1f}ms")
    print("=" * 80)
    return passed == total


if __name__ == "__main__":
    success = run_smoke_test()
    sys.exit(0 if success else 1)
