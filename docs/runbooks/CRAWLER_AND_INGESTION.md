# Crawler and Ingestion Pipeline Runbook

**Pipeline:** Anupalan Regulatory Ingestion (`services/ingestion`)  
**Sources:** CBIC GST Notifications, Gujarat Industries Commissionerate Circulars, Ministry of MSME Gazettes

---

## 1. Failed Crawl Recovery

When automated watchers (RSS/sitemaps) detect failures fetching official gazette PDFs:

1. **Check Source Status:**
   - CBIC Portal: `https://cbic-gst.gov.in/notices/`
   - Gujarat Portal: `https://industries.gujarat.gov.in/`
2. **Inspect Pipeline Logs:**
   ```bash
   grep -i "error" /var/log/anupalan/ingestion.log | tail -n 50
   ```
3. **Execute Manual Ingestion Retry:**
   ```bash
   python -m services.ingestion.src.pipeline \
     --source-url "https://cbic-gst.gov.in/notices/20-2017-ct-rate.pdf" \
     --force-reload
   ```

---

## 2. OCR Quality Degradation & Provider Failover

If an ingested scanned gazette PDF exhibits low OCR quality (confidence $< 0.85$):

1. The pipeline automatically flags the document and routes it to the **Human Curator Review Queue** (`review_status = 'pending_curation'`).
2. **Curator Action:**
   - Log into the review panel (`/admin/review`).
   - Review low-confidence clauses.
   - Manually verify numbers, rates (e.g. 5% vs 12%), and turnover thresholds.
   - Approve corrected transcription to release chunks into the active vector index.

---

## 3. Legal Version Graph Supersession Verification

Whenever an amendment circular is ingested:

1. Ensure the `relation` block contains a valid target:
   ```json
   {
     "code": "INST-GST-JW-002",
     "relation": { "type": "amends", "target": "INST-GST-JW-001", "scope": "Entry 26(i)" }
   }
   ```
2. Verify that no cycles were introduced into the Directed Acyclic Graph:
   ```python
   from services.ingestion.src.version_graph import LegalVersionGraph
   # Cycle check is enforced automatically before saving edges
   ```
3. Run the temporal regression suite:
   ```bash
   pytest tests/unit/test_retrieval_supersession.py
   ```
