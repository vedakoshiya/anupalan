# Software Specification: Anupalan

**Multilingual, Citation-Grounded Compliance Navigator for Indian MSMEs (RAG System)**

| Field | Value |
| --- | --- |
| Document type | PRD + SRS + Technical Design (combined) |
| Version | 1.0 (baseline) |
| Status | Approved for Implementation |
| Owner | Vedansi Koshiya ([@vedakoshiya](https://github.com/vedakoshiya)) |
| Working name | Anupalan ("compliance" in Hindi/Gujarati) |
| Repository | [https://github.com/vedakoshiya/anupalan](https://github.com/vedakoshiya/anupalan) |
| Target Audience | Indian MSMEs, Munshis, Accountants, and Tax Professionals |

---

## 1. Overview

### 1.1 Purpose

Anupalan answers compliance and scheme questions from small business owners in Gujarati, Hindi, English, or mixed Gujlish. Every answer is grounded in official documents (GST notifications and circulars, Udyam/MSME schemes, labour rules, Gujarat state circulars), carries exact citations, respects effective dates, and abstains when evidence is weak.

### 1.2 Problem Statement

MSME owners rely on word of mouth and intermediaries for rules that change often. Official documents are long, in English or legalese, often scanned, and amended repeatedly. Generic chatbots hallucinate rates, dates, and eligibility, and cannot tell which rule is currently in force.

### 1.3 Product Vision

An owner asks *"Job work par GST kevi rite lage?"* and receives a short answer in Gujarati, the governing notification number and clause, the date it took effect, any later amendment, and a clear statement of what is uncertain.

### 1.4 Goals

- **G1:** Citation precision of **95% or higher** (every cited span supports the claim it is attached to).
- **G2:** Retrieval recall@5 of **0.90 or higher** on the golden set for in-corpus questions.
- **G3:** Faithfulness (no unsupported claims) of **0.95 or higher**; hallucinated numbers (rates, dates, amounts) **below 1%**.
- **G4:** Correct abstention on out-of-corpus or ambiguous questions at **90% or higher**.
- **G5:** Corpus freshness: new or amended source documents indexed within **24 hours** of publication.
- **G6:** Latency: **p95 end-to-end latency under 8 seconds** (p50 under 4 seconds).

### 1.5 Non-Goals (v1)

- Legal advice, return filing, or form submission.
- Personalised tax computation.
- Case law and court judgments (deferred to v2).
- Languages beyond Gujarati, Hindi, English, and their transliterated mixes.
- Voice interface (deferred to v2).

### 1.6 Glossary

- **Notification / circular:** Official legal instruments issued by government departments (CBIC, GST Council, Gujarat Labour Dept, MSME Ministry).
- **Effective date:** The calendar date from which a statutory provision or notification applies.
- **Superseded:** Replaced, rescinded, or amended by a subsequent instrument.
- **Hybrid retrieval:** Lexical search (BM25 / Postgres FTS) combined with dense vector semantic search via Reciprocal Rank Fusion (RRF).
- **Abstention:** Formally declining to answer when evidence is insufficient or ambiguous, with clear escalation guidance.

---

## 2. Users and Personas

- **P1: MSME owner (primary):** Non-expert, asks short practical questions in Gujlish/vernacular, wants a plain-language answer and an actionable next step.
- **P2: Accountant / CA / munshi (secondary):** Wants the exact citation, clause text, and amendment history; frequently queries in English or formal terms.
- **P3: Content curator (internal):** Reviews ingestion quality, fixes metadata, and maintains the domain glossary.
- **P4: Platform operator:** Monitors quality, cost, freshness, and system reliability incidents.

---

## 3. User Stories and Acceptance Criteria

| ID | Story | Acceptance Criteria |
| --- | --- | --- |
| **US-01** | As an owner, I ask a question in Gujlish and get an answer in Gujarati. | Reply language matches the query language unless overridden; terms like "ITC" kept in English with explanation. |
| **US-02** | As a user, I see where the answer came from. | Each claim has an inline citation (instrument, number, clause, date) linking to the source passage and original PDF page. |
| **US-03** | As a user, I get the rule in force on a given date. | Query accepts "as on \<date>"; default is today; superseded text is never presented as current. |
| **US-04** | As a user, I am told when the system does not know. | If evidence score is below threshold, reply states the limit and suggests a human/official channel. |
| **US-05** | As an accountant, I view amendment history. | Timeline of an instrument showing amendments with effective dates. |
| **US-06** | As a user, I ask multi-part questions. | System decomposes, answers each part with separate citations. |
| **US-07** | As a curator, I review low-quality OCR/ingestion. | Review queue sorted by quality score with side-by-side page image and extracted text. |
| **US-08** | As an operator, I see quality dashboards. | Retrieval, faithfulness, abstention, latency, and cost metrics per day and per language. |
| **US-09** | As a user, I give feedback on an answer. | Thumbs and reason codes stored with full trace for review. |

---

## 4. Functional Requirements

### 4.1 Ingestion

- **FR-001:** Source connectors for official sites (configurable list), RSS/sitemap watchers, and manual upload.
- **FR-002:** Document type detection: native PDF, scanned PDF, HTML, DOCX.
- **FR-003:** OCR for scanned documents (English, Gujarati, Hindi) with per-page quality score; pages below threshold go to the curator queue.
- **FR-004:** Layout-aware parsing: headings, numbered clauses, tables (preserved as structured rows), footnotes, and annexures.
- **FR-005:** Metadata extraction: issuing authority, instrument type, number, date of issue, effective date, jurisdiction (central/Gujarat), subject tags, and the list of instruments it amends or supersedes.
- **FR-006:** Version graph: every instrument links to those it amends, supersedes, or clarifies; effective-date ranges are computed per clause where possible.
- **FR-007:** Deduplication by content hash and near-duplicate detection.
- **FR-008:** Idempotent, resumable pipeline with checksummed raw artifacts stored immutably.

### 4.2 Chunking and Indexing

- **FR-010:** Structure-aware chunking by clause or section, with a target of 200 to 500 tokens and parent-child links (clause, section, instrument).
- **FR-011:** Each chunk carries a contextual header (instrument title, section path) prepended for embedding.
- **FR-012:** Table rows are indexed as individual chunks with column headers repeated.
- **FR-013:** Dual indexing: BM25 (OpenSearch or Postgres FTS) and dense vectors (multilingual embedding model) in pgvector or Qdrant.
- **FR-014:** Chunk metadata supports filters: jurisdiction, instrument type, subject, effective_from, effective_to, language.
- **FR-015:** Re-indexing is incremental; embedding model version is stored per chunk and migrations are blue-green.

### 4.3 Query Understanding

- **FR-020:** Language and script detection, including transliterated Gujarati and Hindi.
- **FR-021:** Query normalisation: transliteration to canonical forms, spelling variants, and numerals ("dedh lakh", "2 lakh").
- **FR-022:** Glossary-based expansion (for example job work, ITC, composition scheme, Udyam, MSME, e-way bill) mapping vernacular terms to official terminology.
- **FR-023:** Intent classification: factual rule lookup, scheme eligibility, procedure, deadline, out-of-scope, chit-chat.
- **FR-024:** Temporal resolution of phrases like "aa varsh", "1 April thi" into an as-of date.
- **FR-025:** Decomposition of multi-part questions into sub-queries with dependencies.
- **FR-026:** Clarification questions when a required slot is missing (for example turnover band or state), limited to at most 2 turns.

### 4.4 Retrieval

- **FR-030:** Hybrid retrieval with reciprocal rank fusion (RRF) of BM25 and dense results, top 50 candidates.
- **FR-031:** Metadata pre-filtering by validity on the as-of date and jurisdiction.
- **FR-032:** Cross-encoder reranking to the top 8, with scores logged.
- **FR-033:** Parent expansion: include the parent section or neighbouring clauses when a retrieved clause depends on a definition or exception.
- **FR-034:** Supersession check: if a retrieved chunk is amended by a later instrument valid on the as-of date, include the amending text or demote the old chunk.
- **FR-035:** Retrieval confidence score computed from rerank scores and score gaps; below-threshold triggers abstention path.

### 4.5 Generation

- **FR-040:** Structured output schema: answer sections, claims[], each with citation ids, confidence, and a short "what to do next" list.
- **FR-041:** Citation enforcement: a post-generation verifier checks that each claim is entailed by its cited chunks; unsupported claims are removed or trigger regeneration.
- **FR-042:** Numeric guard: any number, date, or percentage in the answer must appear in the cited text (after normalisation).
- **FR-043:** Language control: reply in the user's language; keep legal terms bilingual on first use.
- **FR-044:** Abstention and escalation messaging; never fabricate a citation.
- **FR-045:** Mandatory disclaimer that the answer is informational, with the last-updated date of the corpus.

### 4.6 Freshness and Change Management

- **FR-050:** Nightly crawl and diff; changed documents re-ingested and re-indexed.
- **FR-051:** Alert on newly published amendments affecting frequently cited instruments.
- **FR-052:** Cached answers are invalidated when any cited chunk changes.

### 4.7 Feedback and Operations

- **FR-060:** Persist full traces (query, rewrites, retrieved chunks, scores, prompts, output, verifier result).
- **FR-061:** Feedback capture with reason codes; failures feed the evaluation set after review.
- **FR-062:** Admin review UI for ingestion quality, glossary management, and flagged answers.

---

## 5. Non-Functional Requirements

| Category | Requirement |
| --- | --- |
| **Latency** | p50 under 4 s, p95 under 8 s end to end |
| **Availability** | 99.5% monthly for the query API |
| **Quality** | Targets in Section 1.4, enforced as CI gates |
| **Scalability** | 10k documents, 1M chunks, 20 queries/second burst |
| **Cost** | Under ₹1.5 per query at p95 (embedding, rerank, generation) |
| **Security** | TLS, encrypted storage, secrets in a vault, least-privilege IAM |
| **Privacy** | Queries may contain business data; minimal retention (30 days), PII redaction in logs, DPDP-aligned consent and deletion |
| **Auditability** | Every answer reproducible from stored trace and versioned corpus snapshot |
| **Maintainability** | Provider-agnostic interfaces for LLM, embedder, reranker, OCR |
| **Accessibility** | Plain-language responses; text-first UI usable on low-end phones |

---

## 6. System Architecture

### 6.1 Component Overview

```text
 Sources (gov sites, uploads)
        │
        ▼
 [Crawler/Watcher] → [Raw Store (S3, immutable)]
        │
        ▼
 [Parse + OCR] → [Metadata + Version Graph Extractor] → [Curator Review UI]
        │
        ▼
 [Chunker] → [Embedder] → [Index: BM25 + Vector + Metadata (Postgres/Qdrant/OpenSearch)]

 User (WhatsApp / Web)
        │
        ▼
 [API Gateway / FastAPI]
        │
        ▼
 [Query Understanding: lang-id, normalise, glossary, intent, date, decompose]
        │
        ▼
 [Retriever: hybrid + filters + rerank + parent expansion + supersession]
        │
        ▼
 [Generator (LLM, structured output)] → [Verifier: entailment + numeric guard]
        │
        ▼
 [Response + citations]   →   [Trace Store / Feedback / Metrics]
```

### 6.2 Key Design Decisions

1. **Structure-aware chunking over fixed windows:** Legal meaning lives in clauses, provisos, and definitions; fixed windows split them.
2. **Temporal correctness is a retrieval concern, not a prompt concern:** Validity filters and supersession checks happen before the LLM sees any text.
3. **Verify, don't trust:** A separate verifier (NLI model or second LLM call) checks each claim against its citations before the user sees it.
4. **Abstain by design:** Retrieval confidence gates generation; a wrong confident answer is worse than "I'm not sure."
5. **Evaluation as code:** Retrieval and generation are evaluated separately in CI with frozen golden sets.
6. **Provider abstraction:** All model calls go through interfaces with logged versions so results are comparable.

### 6.3 Technology Stack

- **Backend & Core:** Python 3.12, FastAPI, Pydantic v2, Celery / Temporal for pipelines.
- **Storage:** S3-compatible object store (raw), PostgreSQL 16 (metadata, traces), pgvector or Qdrant (vectors), OpenSearch or Postgres FTS (BM25).
- **OCR / Layout:** A document-AI service or open-source stack (OCR engine plus layout parser), with table extraction.
- **Embeddings & Reranker:** Multilingual model evaluated on Gujarati and Hindi retrieval; reranker: multilingual cross-encoder (`BAAI/bge-reranker-v2-m3` or equivalent).
- **LLM:** Hosted model with structured outputs; separate smaller model for classification and rewriting.
- **Frontend:** Lightweight web app and optional WhatsApp channel.
- **Observability:** OpenTelemetry, Langfuse or equivalent, Prometheus/Grafana.
- **Infra:** Docker, Terraform, GitHub Actions, India region.

---

## 7. Data Model

```sql
CREATE TABLE instruments (
  id UUID PRIMARY KEY,
  authority TEXT NOT NULL,              -- CBIC, GST Council, Gujarat Labour Dept, MSME Ministry
  type TEXT NOT NULL,                   -- notification, circular, act, rule, scheme, order
  number TEXT NOT NULL,
  title TEXT NOT NULL,
  jurisdiction TEXT NOT NULL,           -- central | gujarat
  issued_on DATE NOT NULL,
  effective_from DATE,
  effective_to DATE,
  language TEXT[] NOT NULL,
  source_url TEXT NOT NULL,
  raw_object_key TEXT NOT NULL,
  content_hash TEXT NOT NULL UNIQUE,
  ingest_version INT NOT NULL DEFAULT 1,
  UNIQUE (authority, type, number)
);

CREATE TABLE instrument_relations (
  from_id UUID NOT NULL REFERENCES instruments(id),
  to_id UUID NOT NULL REFERENCES instruments(id),
  relation TEXT NOT NULL CHECK (relation IN ('amends','supersedes','clarifies','rescinds')),
  effective_from DATE,
  scope TEXT,                           -- e.g. 'clause 3(b)'
  PRIMARY KEY (from_id, to_id, relation)
);

CREATE TABLE sections (
  id UUID PRIMARY KEY,
  instrument_id UUID NOT NULL REFERENCES instruments(id),
  parent_id UUID REFERENCES sections(id),
  path TEXT NOT NULL,                   -- 'Notif 12/2024 > Para 3 > Cl (b)'
  heading TEXT,
  page_from INT, page_to INT
);

CREATE TABLE chunks (
  id UUID PRIMARY KEY,
  section_id UUID NOT NULL REFERENCES sections(id),
  instrument_id UUID NOT NULL REFERENCES instruments(id),
  text TEXT NOT NULL,
  context_header TEXT NOT NULL,
  chunk_type TEXT NOT NULL,             -- clause | table_row | definition | proviso
  effective_from DATE,
  effective_to DATE,
  jurisdiction TEXT NOT NULL,
  subjects TEXT[] NOT NULL,
  language TEXT NOT NULL,
  embedding VECTOR(1024),
  embed_model TEXT NOT NULL,
  ocr_quality NUMERIC(3,2),
  bbox JSONB                            -- page coordinates for highlight
);

CREATE TABLE glossary (
  id UUID PRIMARY KEY,
  canonical_term TEXT NOT NULL,
  variants TEXT[] NOT NULL,             -- vernacular and transliterated forms
  language TEXT NOT NULL,
  definition TEXT
);

CREATE TABLE queries (
  id UUID PRIMARY KEY,
  session_id UUID,
  raw_query TEXT NOT NULL,
  language TEXT,
  as_of DATE NOT NULL,
  intent TEXT,
  rewritten JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE answers (
  id UUID PRIMARY KEY,
  query_id UUID NOT NULL REFERENCES queries(id),
  retrieved JSONB NOT NULL,             -- chunk ids, scores, rerank scores
  prompt_version TEXT NOT NULL,
  model TEXT NOT NULL,
  output JSONB NOT NULL,
  verifier JSONB NOT NULL,
  abstained BOOLEAN NOT NULL,
  corpus_snapshot TEXT NOT NULL,
  latency_ms INT, cost_inr NUMERIC(8,3)
);

CREATE TABLE feedback (
  id UUID PRIMARY KEY,
  answer_id UUID NOT NULL REFERENCES answers(id),
  rating SMALLINT, reason_code TEXT, comment TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

**Indexes:** GIN on `chunks.subjects`, B-Tree on `(jurisdiction, effective_from, effective_to)`, HNSW on `embedding`, FTS index on `text`.

---

## 8. Interfaces

### 8.1 Public API

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/v1/ask` | Ask a question (body: query, as_of, language, session_id) |
| `GET` | `/v1/instruments/{id}` | Instrument metadata and amendment timeline |
| `GET` | `/v1/chunks/{id}` | Source passage with page and highlight coordinates |
| `POST` | `/v1/feedback` | Submit feedback on an answer |
| `GET` | `/v1/health` | Liveness and corpus freshness |

### 8.2 Response Contract

```json
{
  "answer_id": "...",
  "language": "gu",
  "abstained": false,
  "summary": "...",
  "claims": [
    {
      "text": "...",
      "citations": [
        {
          "chunk_id": "...",
          "instrument": "Notification 12/2024-CT",
          "clause": "Para 3(b)",
          "effective_from": "2024-04-01"
        }
      ],
      "confidence": 0.93
    }
  ],
  "next_steps": ["..."],
  "as_of": "2026-10-26",
  "corpus_updated": "2026-10-25",
  "disclaimer": "Informational use only. Consult a registered CA for tax filing."
}
```

### 8.3 Internal Interfaces

- `Embedder.embed(texts) -> vectors`, `Reranker.score(query, passages)`, `LLM.generate(schema, messages)`, `OCR.extract(file)`: all provider-agnostic with version tags.
- Admin API (JWT, role-based) for review queue, glossary CRUD, reindex triggers.

---

## 9. Evaluation Plan

### 9.1 Datasets

- **Golden set:** 250 questions across GST, MSME schemes, labour rules, and Gujarat circulars (40% Gujlish, 30% Gujarati script, 20% Hindi/Hinglish, 10% English). Each has gold supporting passages, the correct as-of answer, and a type tag.
- **Temporal set:** 50 questions where the answer changed after an amendment, tested with different as-of dates.
- **Adversarial set:** Questions with false premises, outdated rates, and requests for personal tax advice.
- Labelling by two annotators with agreement measured (Cohen's Kappa $\ge$ 0.70) and practitioner (CA) verification.

### 9.2 Metrics & Thresholds

| Layer | Metric | Target |
| --- | --- | --- |
| **Retrieval** | Recall@5, recall@20, MRR, nDCG | 0.90 / 0.97 / 0.80 / 0.85 |
| **Temporal** | Correct-version rate | 97% or higher |
| **Generation** | Faithfulness, citation precision, citation recall | 0.95 / 95% / 90% |
| **Safety** | Hallucinated numbers, wrong-confident rate | under 1%, under 2% |
| **Abstention** | Correct abstain / wrongful abstain | 90% / under 10% |
| **Language** | Reply-language correctness | 98% or higher |
| **System** | Latency p95, cost per query | under 8 s, under ₹1.5 |

---

## 10. Security, Privacy and Compliance

- Publicly available official documents only; respect `robots.txt` and source terms; record source URLs and timestamp.
- User queries: retention capped at **30 days** by default for raw queries, PII redaction in logs, consent-based trace archiving.
- Prompt injection protection: retrieved context and user query treated as pure data payloads. System prompt forbids running instructions inside documents.
- Indian **DPDP Act (2023)** alignment: bilingual consent notice, deletion on request, India-region data hosting.

---

## 11. Testing Strategy

- **Unit:** Parsers, chunkers, transliteration normalisers, date resolution, numeric guardrail.
- **Property-based:** Chunking never breaks mid-clause; amendment graph is guaranteed acyclic.
- **Integration:** End-to-end fixture-based ingestion and question answering with stubbed models.
- **Regression (ML):** CI gates evaluating golden and temporal sets against metric thresholds.
- **Load Testing:** 20 queries/second burst testing, measuring p95 latency.

---

## 12. Operations

- **Environments:** Local, Staging, Production with isolated databases and index namespaces.
- **Deployment:** Containerized microservices, blue-green index swaps.
- **Monitoring & Alerts:** Retrieval score drift, abstention anomalies, verifier rejection spikes, corpus staleness (> 48 hours).

---

## 13. Milestones & Delivery Roadmap

- **Phase 0 (Week 1):** Scoping, 40 core instruments, source registry, glossary schema.
- **Phase 1 (Weeks 2–3):** Ingestion, OCR pipeline, layout parser, version graph builder.
- **Phase 2 (Weeks 3–4):** Evaluation datasets (250 golden questions, temporal benchmarks).
- **Phase 3 (Weeks 5–6):** Hybrid retrieval (BM25 + Dense + Reranking + Supersession).
- **Phase 4 (Weeks 7–8):** Generation, citation verification engine, numeric guard, abstention logic.
- **Phase 5 (Weeks 9–10):** Public REST API, clean Web UI, feedback collection, operator dashboard.
- **Phase 6 (Weeks 11–12):** Hardening, load tests, ablation writeup, pilot deployment.

---

## 14. Appendix: Sample Evaluation Cases

| Query | Type | Expected Behavior |
| --- | --- | --- |
| *"Job work par GST kevi rite lage?"* | Single-hop, Gujlish | Answer with rate/treatment, cite the governing entry, reply in Gujarati. |
| *"2023 ma composition limit shu hati?"* | Temporal | Return the value valid in 2023 and note subsequent amendments. |
| *"Mara pase 40 lakh turnover che, mane shu karvu pade?"* | Ambiguous | Ask clarifying question for missing slot (goods vs services, state) before answering. |
| *"Mane income tax ketlo bharvo?"* | Out of scope | Abstain safely and explain system compliance scope. |
| *"Udyam registration ma 2019 vala subsidy hajhi male che?"* | Temporal + false premise | Check validity date, state if discontinued, cite the relevant order. |
