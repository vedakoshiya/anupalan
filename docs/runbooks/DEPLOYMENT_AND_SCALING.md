# Deployment, Scaling & Infrastructure Runbook

**Environment:** Production / Cloud (AWS ap-south-1 / GCP asia-south1)  
**SLA Targets:** p50 $< 4.0\text{s}$, p95 $< 8.0\text{s}$, Availability $\ge 99.5\%$

---

## 1. Production Container Architecture

The system deploys as standard multi-tier microservices:
1. **API Replicas (`services/api`):** FastAPI app with Gunicorn/Uvicorn workers.
2. **PostgreSQL 16 + pgvector:** Persistent vector store with HNSW index and trigram GIN indexes.
3. **Redis (Optional Distributed Cache):** High-speed distributed cache for normalized queries.
4. **Prometheus & Grafana:** Monitoring, latencies, and alerting.

### Docker Compose Deployment
```yaml
version: '3.8'

services:
  anupalan-api:
    image: anupalan/api:v0.1.0
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://anupalan:securepass@db:5432/anupalan_db
      - ENVIRONMENT=production
      - DPDP_TTL_DAYS=30
    depends_on:
      - db
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 16G

  db:
    image: pgvector/pgvector:pg16
    environment:
      - POSTGRES_DB=anupalan_db
      - POSTGRES_USER=anupalan
      - POSTGRES_PASSWORD=securepass
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  pgdata:
```

---

## 2. Zero-Downtime Blue-Green Index Swap

When re-indexing the entire statutory corpus with an updated embedding model:

1. Create green table: `CREATE TABLE chunks_v2 (LIKE chunks INCLUDING ALL);`
2. Populate `chunks_v2` and build HNSW cosine index:
   ```sql
   CREATE INDEX ON chunks_v2 USING hnsw (embedding vector_cosine_ops);
   ```
3. Run verification evaluation:
   ```bash
   python eval/eval_gate.py --target-table chunks_v2
   ```
4. If gates pass, execute atomic table swap:
   ```sql
   BEGIN;
   ALTER TABLE chunks RENAME TO chunks_v1_backup;
   ALTER TABLE chunks_v2 RENAME TO chunks;
   COMMIT;
   ```

---

## 3. Operational Prometheus Alerting Rules

Configure Prometheus alerts (`prometheus.rules.yml`):

1. **High p95 Latency Alert:**
   - Expression: `anupalan_query_latency_p95_seconds > 8.0`
   - Duration: `5m`
   - Severity: `Warning`
2. **High Abstention Rate Alert:**
   - Expression: `rate(anupalan_answers_total{abstained="true"}[15m]) / rate(anupalan_answers_total[15m]) > 0.35`
   - Duration: `10m`
   - Severity: `Critical` (Indicates possible corpus staleness or retriever misconfiguration).
3. **Corpus Staleness Alert:**
   - Alert if no successful circular sync occurred in the last 48 hours.
