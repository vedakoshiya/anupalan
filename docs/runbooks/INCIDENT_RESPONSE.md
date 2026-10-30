# Incident Response Runbook: Statutory Compliance Engine

**Service:** Anupalan Compliance Engine  
**Severity Levels:** P1 (Critical Statutory Inaccuracy / Hallucinated Number), P2 (Degraded Latency / Availability), P3 (Minor Ingestion Delay)

---

## 1. Bad-Answer Incident Response & Emergency Takedown (P1)

If an answer contains an inaccurate rate, an outdated circular, or an ungrounded claim that escaped the guardrails:

### Step 1: Execute Administrative Takedown
Invoke the administrative takedown endpoint immediately to purge the answer from the temporal query cache:

```bash
curl -X POST "https://api.anupalan.gov.in/v1/admin/takedown" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_JWT_TOKEN" \
  -d '{
    "answer_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "reason": "Circular 20/2017 superseded by Notification 14/2019 entry 26(i)"
  }'
```

### Step 2: Invalidate Corrupted or Superseded Chunk
If a chunk contains typographical errors or OCR distortions:
1. Identify the chunk UUID from the answer citations (`GET /v1/chunks/{id}`).
2. In the PostgreSQL database, mark the chunk active status:
   ```sql
   UPDATE chunks SET is_active = FALSE WHERE id = '3fa85f64-5717-4562-b3fc-2c963f66afa6';
   ```
3. Trigger re-indexing of the parent instrument.

### Step 3: Log Post-Mortem and Add to Adversarial Test Set
1. Add the triggering question and incorrect response to `eval/datasets/adversarial_set.json`.
2. Run `python eval/eval_gate.py` to ensure regression protection.

---

## 2. Emergency DPDP Right to Erasure & User Data Purge

Under DPDP Act 2023 Section 12, users or compliance officers may request immediate deletion of all session query traces:

### User Session Deletion:
```bash
curl -X DELETE "https://api.anupalan.gov.in/v1/sessions/<SESSION_UUID>"
```

### Force Rolling 30-Day TTL Purge:
```bash
curl -X POST "https://api.anupalan.gov.in/v1/telemetry/purge"
```

---

## 3. Database & pgvector Index Corruption Rollback

If the pgvector index fails consistency checks or embedding dimensions mismatch:

1. Stop incoming write traffic to the ingestion pipeline.
2. Restore vector store from the latest daily cryptographic snapshot:
   ```bash
   pg_restore -U anupalan_admin -d anupalan_db -c /backup/anupalan_vector_latest.dump
   ```
3. Re-run version graph integrity validation:
   ```bash
   python -c "from services.api.src.main import VERSION_GRAPH; assert not VERSION_GRAPH.has_cycles()"
   ```
4. Verify health status: `curl http://localhost:8000/v1/health`.
