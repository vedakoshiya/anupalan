# Anupalan (અનુપાલન / अनुपालन)

> **Multilingual, Citation-Grounded Compliance Navigator for Indian MSMEs (RAG System)**

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.12%2B-brightgreen.svg)](https://www.python.org/)
[![Target Audience](https://img.shields.io/badge/Target-Indian%20MSMEs-orange.svg)](#)
[![Languages](https://img.shields.io/badge/Languages-Gujarati%20%7C%20Hindi%20%7C%20Gujlish%20%7C%20English-purple.svg)](#)
[![Code Style: Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

---

## 📖 Overview

Small business owners (MSMEs) in India navigate complex, frequently amended compliance circulars across **GST, Udyam/MSME schemes, labour regulations, and state circulars**. Most official documents are drafted in dense English legalese, often scanned, and altered by subsequent notifications. 

Generic AI chatbots hallucinate tax rates, eligibility thresholds, and dates. **Anupalan** is an open-source, citation-grounded Retrieval-Augmented Generation (RAG) system engineered specifically to answer MSME compliance questions in **Gujarati, Hindi, English, and Gujlish** with absolute grounding and zero fabricated rules.

```
Owner asks: "Job work par GST kevi rite lage?"
    │
    ▼
Anupalan provides:
1. Concise answer in Gujarati
2. Governing Notification number and exact clause (e.g. Notif 12/2024-CT)
3. Effective in-force date and subsequent amendment notes
4. Direct link to highlighted source passage on official PDF
5. Actionable next steps for the business owner
```

---

## ⚡ Key Architectural Capabilities

* **Indic-First Query Understanding:** Native handling of mixed **Gujlish**, Gujarati script, Hindi, Hinglish, and vernacular numerals (e.g., *"dedh lakh"* $\rightarrow$ ₹1,50,000).
* **Legal Version & Supersession Graph:** Tracks legal instrument relationships (`amends`, `supersedes`, `clarifies`, `rescinds`). A query `"as on 2023-04-01"` automatically retrieves the rule active on that date, ignoring subsequent or defunct changes.
* **Citation Precision ($\ge 95\%$):** Every single factual claim has an inline citation pointing to the exact statutory paragraph, clause, and document hash.
* **Numeric Guardrail:** Strict post-generation validation ensuring every tax rate, monetary ceiling, and calendar date appears verbatim in the cited official text.
* **Abstention by Design:** If evidence confidence falls below threshold or the query is out of scope (e.g. personal income tax computation), Anupalan gracefully abstains and provides official helpline links.
* **DPDP Act (2023) Aligned:** Built with rolling 30-day raw query retention, automated PII scrubbing, and India data residency.

---

## 🏛️ System Architecture

```text
 Sources (CBIC, GST Council, Gujarat Depts)
        │
        ▼
 [Crawler / Watcher] ──▶ [Raw Store (MinIO / S3, SHA-256 Checksummed)]
        │
        ▼
 [Layout OCR & Parser] ──▶ [Metadata & Version Graph Builder] ──▶ [Curator Review UI]
        │
        ▼
 [Structure-Aware Chunker] ──▶ [Multilingual Embedder] ──▶ [Hybrid Index: BM25 + Vector]

 User (Web / WhatsApp)
        │
        ▼
 [FastAPI Gateway]
        │
        ▼
 [Query Understanding] ──▶ Lang-ID, Transliteration Normalization, Glossary Expansion
        │
        ▼
 [Hybrid Retrieval]    ──▶ RRF (BM25 + pgvector) + Temporal Filters + Cross-Encoder Rerank
        │
        ▼
 [Generation & Guard]  ──▶ Structured Output ──▶ Entailment Verifier & Numeric Guard
        │
        ▼
 [Grounded Response]   ──▶ Claims with Verified Citations + Actionable Next Steps
```

---

## 📂 Repository Structure

```text
anupalan/
├── .github/workflows/          # CI/CD, linting, evaluation gates
├── config/                     # Application configurations
├── data/                       # Local raw/processed data mounts (git-ignored)
├── db/migrations/              # PostgreSQL + pgvector schema migrations
├── docs/                       # Specifications, ADRs, runbooks
│   ├── SPECIFICATION.md        # Canonical PRD & SRS specification
│   └── IMPLEMENTATION.md       # Production engineering implementation guide
├── eval/                       # 250-question golden set, temporal & adversarial evals
├── infra/                      # Docker & Terraform deployments (India region)
├── packages/                   # Core modular Python packages
│   ├── adapters/               # Provider-agnostic LLM, Embedder, OCR adapters
│   ├── generation/             # Prompt engine, Pydantic schemas, Verifier, Numeric guard
│   ├── query/                  # Transliteration, glossary expansion, intent, temporal parser
│   └── retrieval/              # Hybrid RRF, Cross-encoder reranker, supersession graph
├── services/                   # Microservices
│   ├── admin/                  # Curator UI backend (OCR review, glossary CRUD)
│   ├── api/                    # Public FastAPI REST API
│   └── ingestion/              # Scrapers, layout parsers, version graph builders
├── tests/                      # Unit & integration test suites
└── web/                        # Responsive web application interface
```

---

## 🚀 Quickstart

### 1. Clone & Set Up Environment

```bash
# Clone the repository
git clone https://github.com/vedakoshiya/anupalan.git
cd anupalan

# Create virtual environment
python -m venv .venv
source .venv/bin/activate       # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"
```

### 2. Configure Environment

```bash
# Copy the safe environment template
cp .env.example .env
```
Edit `.env` with your local database credentials and AI model API keys. *(Note: `.env` is ignored by `.gitignore` and must never be committed).*

### 3. Start Database & Search Backends

```bash
# Start PostgreSQL 16 (with pgvector) and MinIO
docker compose -f infra/docker/docker-compose.yml up -d

# Apply schema migrations
psql -h localhost -U postgres -d anupalan -f db/migrations/001_initial_schema.sql
```

### 4. Run Development API

```bash
uvicorn services.api.src.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 📡 API Contract Example

### Request (`POST /v1/ask`)
```json
{
  "query": "Job work par GST ketlo lage?",
  "language": "gu",
  "as_of": "2026-10-27"
}
```

### Response (`200 OK`)
```json
{
  "answer_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "language": "gu",
  "abstained": false,
  "summary": "સામાન્ય જોબ વર્ક સેવાઓ પર 12% અથવા 18% GST લાગુ પડે છે, જ્યારે કાપડ અને હીરા સંબંધિત ચોક્કસ કામ માટે 5% રેટ માન્ય છે.",
  "claims": [
    {
      "text": "કાપડ અને ટેક્સટાઇલ યાર્ન પરના જોબ વર્ક માટે GST દર 5% રહેશે.",
      "citations": [
        {
          "chunk_id": "c1f7596a-0487-43cf-a4d1-5f2122650720",
          "instrument": "Notification No. 11/2017-Central Tax (Rate)",
          "clause": "Item (i) of Entry 26",
          "effective_from": "2017-07-01"
        }
      ],
      "confidence": 0.96
    }
  ],
  "next_steps": [
    "તમારા જોબ વર્ક ચલણ અને HSN/SAC કોડ 9988 ચકાસો.",
    "ઇનપુટ ટેક્સ ક્રેડિટ (ITC) માટે સમયમર્યાદા ધ્યાનમાં રાખો."
  ],
  "as_of": "2026-10-27",
  "corpus_updated": "2026-10-26",
  "disclaimer": "આ માત્ર માહિતી માટે છે. સત્તાવાર કર આકારણી માટે તમારા ચાર્ટર્ડ એકાઉન્ટન્ટ (CA) ની સલાહ લો."
}
```

---

## 🎯 Quantitative Evaluation Targets

| Evaluation Layer | Target Metric | Benchmark Goal |
| :--- | :--- | :--- |
| **Retrieval** | Recall@5 / MRR | $\ge \mathbf{0.90} \;/ \ge \mathbf{0.80}$ |
| **Temporal Accuracy** | Correct In-Force Version | $\ge \mathbf{97\%}$ |
| **Generation** | Faithfulness | $\ge \mathbf{0.95}$ |
| **Citations** | Precision / Recall | $\ge \mathbf{95\%} \;/ \ge \mathbf{90\%}$ |
| **Safety** | Hallucinated Numbers | $< \mathbf{1.0\%}$ |
| **Abstention** | Correct Abstention Rate | $\ge \mathbf{90\%}$ |
| **Performance** | Latency p95 / Cost per Query | $< \mathbf{8.0s} \;/ < \mathbf{₹1.50}$ |

---

## 🔒 Security & Privacy Policy

- **Zero Secret Commits:** We enforce pre-commit security checks and GitHub secret scanning.
- **DPDP Act (2023):** Raw user queries are stored for 30 days maximum. Logs are scrubbed of all PII (GSTIN, PAN, Phone Numbers, Aadhaar).
- **Public Domain Corpus:** All ingested circulars and notifications are publicly issued by the Government of India and the Government of Gujarat.

---

## 📜 License

Distributed under the **Apache License 2.0**. See [`LICENSE`](LICENSE) for more information.

---

## 👩‍💻 Author & Contact

**Vedansi Koshiya**  
GitHub: [@vedakoshiya](https://github.com/vedakoshiya)  
Project Repository: [https://github.com/vedakoshiya/anupalan](https://github.com/vedakoshiya/anupalan)
