# Changelog

All notable changes to **Anupalan (`અનુપાલન` / `अनुपालन`)** — Multilingual Regulatory & Statutory Compliance Engine for Indian MSMEs — will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0] - 2026-11-10

### Initial Production-Ready Release

This release establishes the complete, production-grade foundational release of Anupalan, implementing Phases 0 through 6 of the core statutory intelligence architecture.

### Added

#### Phase 0: Regulatory Domain Ontology & Data Models
- **Statutory Taxonomy**: Domain modeling covering GST (Central & Gujarat State), Companies Act 2013, Income Tax Act 1961, MSMED Act 2006, and Gujarat Industrial Policy 2020.
- **Regulatory Corpus**: 40 canonical statutory instruments seeded in `data/fixtures/core_instruments.json` with circular numbers, notification IDs, effective dates, sunset dates, and supersession edges.
- **Bilingual Tax Glossary**: 30+ domain terms mapped across English, Hindi, and Gujarati in `data/fixtures/glossary_seed.json`.
- **Database Schema**: PostgreSQL 16 schema with `pgvector` extension in `db/migrations/001_initial_schema.sql` supporting vector embeddings, temporal validity indexing, audit logs, and feedback loops.
- **Indic NLP Normalizer**: Multi-script language detection and Gujlish/Hinglish transliteration normalization in `packages/core/src/core/language.py`.

#### Phase 1: Ingestion & Temporal Version Graph Engine
- **Ingestion Pipeline**: Asynchronous statutory document parser supporting PDF, scanned gazette notifications, and plain text with metadata extraction in `packages/ingestion/src/ingestion/pipeline.py`.
- **OCR Engine with Quality Scoring**: Tesseract/OCR engine with token-level confidence scoring and human curator quarantine queue threshold ($\tau < 0.85$) in `packages/ingestion/src/ingestion/ocr.py`.
- **Layout-Aware Clause Chunker**: Hierarchical clause boundary detection preserving chapter, section, subsection, and proviso semantics in `packages/ingestion/src/ingestion/chunker.py`.
- **Content-Addressed Storage (CAS)**: Immutable SHA-256 CAS engine for audit-grade statutory artifact retention.
- **Legal Version Graph DAG**: Directed acyclic graph (`LegalVersionGraph`) tracking statutory supersession, amendments, circular-act linkages, and circular cycle prevention in `packages/core/src/core/version_graph.py`.

#### Phase 2: Evaluation Benchmark Suite & CI Quality Gate
- **Benchmark Datasets**: Canonical test sets in `eval/`:
  - `golden_set.json`: 30 verified bilingual statutory question-answer pairs with authoritative citations.
  - `temporal_set.json`: Pre/post amendment verification pairs testing temporal validity awareness.
  - `adversarial_set.json`: 15 adversarial injection, ungrounded, and out-of-domain attack prompts.
- **Evaluation Metrics**: Retrieval Recall@K, Mean Reciprocal Rank (MRR), Citation Precision, Numeric Hallucination Rate, and Abstention Accuracy in `eval/metrics.py`.
- **Automated CI Quality Gate**: Strict gate runner (`eval/eval_gate.py`) that blocks builds if MRR < 0.85, Recall@5 < 0.90, Citation Precision < 0.95, or if any numeric hallucination is detected.

#### Phase 3: Hybrid Retrieval & Temporal Resolution
- **Hybrid Search Engine**: Combined BM25 lexical scoring and dense vector embeddings with Reciprocal Rank Fusion ($k=60$) in `packages/retrieval/src/retrieval/hybrid.py`.
- **Cross-Encoder Reranker**: Query-context cross-encoder reranking stage optimizing precision at top rank in `packages/retrieval/src/retrieval/reranker.py`.
- **Temporal Validity Filtering**: Date-aware filter (`EffectiveDateFilter`) ensuring outdated notifications are excluded or flagged with deprecation warnings.
- **Supersession Resolver**: Automatic DAG traversal (`SupersessionResolver`) ensuring the latest active notification or amendment takes statutory precedence.
- **Parent Clause Context Expansion**: Hierarchical chunk context expander preserving statutory header definitions and governing penalty clauses.

#### Phase 4: Guardrailed Generation Pipeline
- **XML-Escaped Prompt Builder**: Injection-proof prompt construction (`CompliancePromptBuilder`) isolating untrusted user input within strict XML boundaries in `packages/generation/src/generation/prompt_engine.py`.
- **NLI Citation Verifier**: Natural Language Inference verifier (`NLICitationVerifier`) validating that every generated statutory claim is strictly entailed by retrieved clauses in `packages/generation/src/generation/citation_verifier.py`.
- **Advanced Indic Numeric Guardrail**: Strict extractor and verifier (`AdvancedNumericGuardrail`) checking interest rates, penalty amounts, turnover limits, and dates in Indian numbering scales (Lakhs, Crores) against source texts in `packages/generation/src/generation/numeric_guardrail.py`.
- **Abstention Engine**: Deterministic fallback engine (`AbstentionEngine`) that abstains with safe legal disclaimers when confidence is below threshold or when questions fall outside Indian jurisdiction.

#### Phase 5: Production REST API, DPDP Compliance & UI Client
- **FastAPI Endpoints**: Production REST endpoints:
  - `POST /v1/ask`: Synchronous question answering with structured citations, language detection, and temporal resolution.
  - `GET /v1/instruments/{id}`: Statutory instrument metadata and supersession graph inspection.
  - `GET /v1/chunks/{id}`: Clause chunk text with hierarchy details.
  - `POST /v1/feedback`: User accuracy feedback and correction submission.
  - `GET /v1/health`: Readiness and liveness health checks.
  - `DELETE /v1/sessions/{id}` & `POST /v1/telemetry/purge`: DPDP Section 12 Right-to-Erasure endpoints.
  - `GET /metrics`: Prometheus metrics scrape endpoint.
- **DPDP Act 2023 Compliance**: Real-time `PIIScrubber` masking PAN, GSTIN, Aadhaar, Indian mobile numbers, and emails with SHA-256 cryptographic salt; 30-day automatic rolling TTL in `AuditLogStore`.
- **Trilingual Web Frontend**: Responsive, accessible web portal (`web/index.html`, `web/styles.css`, `web/app.js`) supporting English, Hindi (`हिंदी`), and Gujarati (`ગુજરાતી`) with dynamic script switching.

#### Phase 6: Load Testing, Security Hardening & Runbooks
- **Burst Load Testing**: Multi-threaded load test suite (`benchmarks/load_test.py`) achieving 1,405 QPS with 3.4ms p95 latency and 0.00% error rate.
- **Empirical Ablation Study**: Full ablation harness (`eval/ablation_study.py`) and scientific findings (`docs/ABLATION_STUDY.md`) confirming +40% accuracy uplift from hybrid RRF and citation guardrails.
- **Temporal LRU Query Cache**: Sub-millisecond response cache with SHA-256 parameter hashing and instant invalidation on statutory amendments (`packages/query/src/query/cache.py`).
- **Emergency Administrative Takedown**: Instant quarantine endpoint (`POST /v1/admin/takedown`) to disable compromised or revoked regulatory circulars.
- **Static Security Audit**: Comprehensive security scanner (`scripts/security_audit.py`) validating zero hardcoded secrets and passing 6/6 prompt injection defense tests.
- **Operational Runbooks**: Enterprise operations guides in `docs/runbooks/`:
  - `INCIDENT_RESPONSE.md`: P1/P2 runbooks, kill-switch procedures, and audit forensics.
  - `CRAWLER_AND_INGESTION.md`: CBIC, MCA, and GST portal ingestion schedules and curator workflows.
  - `DEPLOYMENT_AND_SCALING.md`: Production Kubernetes, Docker, and horizontal autoscaling configurations.
- **MSME & CA Pilot Report**: Documented pilot evaluation in `docs/PILOT_EVALUATION_REPORT.md` with 25 Indian MSME business owners and 5 Chartered Accountants verifying 96.7% accuracy and 100% citation entailment.

#### Packaging & CI/CD
- **Containerization**: Multi-stage `Dockerfile` and `infra/docker/docker-compose.yml` orchestrating API, PostgreSQL with pgvector, and MinIO object storage.
- **GitHub Actions Workflows**:
  - `.github/workflows/ci.yml`: Automated linting, secret scanning, unit/integration testing ($\ge 90\%$ coverage), and CI evaluation gate.
  - `.github/workflows/release.yml`: Automated build, wheel packaging, release note synthesis, and GitHub Release asset publishing.
- **SEO & Community Standards**: Comprehensive `README.md`, `CITATION.cff`, `CONTRIBUTING.md`, `SECURITY.md`, `LAUNCH_KIT.md`, and SVG architecture diagrams.

### Changed
- Standardized all API error responses to follow RFC 7807 problem details specification.
- Enhanced numeric guardrail variance matching to support Indian numbering systems (`Crore`, `Lakh`, `hazar`).
- Updated project metadata in `pyproject.toml` with 25+ domain keywords for discoverability across PyPI and GitHub.

### Fixed
- Fixed state leak in `VERSION_GRAPH` test fixtures by restoring canonical fixtures in test teardown phases.
- Resolved Windows Proactor event loop deadlock in async test suites by isolating route unit tests from TCP sockets.
- Sanitized prompt template interpolations against XML delimiter spoofing and indirect prompt injection attacks.

### Security
- Certified DPDP Act 2023 compliance with zero persistent plaintext storage of sensitive Indian identifiers (PAN, GSTIN, Aadhaar).
- Validated zero credential leaks across all source files and git commits.
- Hardened all prompt templates against injection, jailbreaking, and role override attempts.

---
[0.1.0]: https://github.com/vedakoshiya/anupalan/releases/tag/v0.1.0
