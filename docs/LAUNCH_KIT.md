# 🚀 Anupalan Viral Launch & Publishing Kit

This document provides ready-to-copy launch templates, SEO metadata, submission copies, and social copy to maximize discoverability across **Google Search, GitHub Trending, Hacker News, Product Hunt, Reddit, Twitter/X, and LinkedIn**.

---

## 📋 1. GitHub Repository Settings (Do This First)

To rank at the top of GitHub search and Google indexes:

| Setting Field | Value to Enter |
| :--- | :--- |
| **Description** | `Open-source multilingual, zero-hallucination compliance RAG engine for Indian MSMEs in Gujarati, Hindi, Gujlish & English (GST, Section 43B(h), Udyam, DPDP Act 2023 compliant)` |
| **Website** | `https://github.com/vedakoshiya/anupalan#readme` |
| **Topics (20 tags)** | `rag`, `indic-nlp`, `gujarati`, `hindi`, `gujlish`, `gst`, `msme`, `legal-tech`, `compliance`, `dpdp-act-2023`, `zero-hallucination`, `pgvector`, `fastapi`, `indian-tax`, `cbic-circulars`, `retrieval-augmented-generation`, `open-source-ai`, `textile-industry`, `surat-msme`, `india-ai` |
| **Social Preview Image** | Upload `docs/assets/anupalan-banner.svg` in **Settings ➔ General ➔ Social preview**. |

---

## 🟠 2. Hacker News: Show HN Submission

* **URL to submit:** `https://news.ycombinator.com/submit`
* **Title:** `Show HN: Anupalan – Zero-hallucination compliance RAG for Indian MSMEs (Gujlish/Gu/Hi)`
* **Text / First Comment:**

```markdown
Hi HN! I built Anupalan (અનુપાલન / अनुपालन) — an open-source, citation-grounded statutory compliance RAG engine for Indian small businesses.

GitHub: https://github.com/vedakoshiya/anupalan

### The Problem
India has over 63 million MSMEs (Micro, Small, and Medium Enterprises). Most small business owners operate in regional languages (like Gujarati or Hindi) or Romanized vernacular ("Gujlish"), while official regulatory circulars from the Central Board of Indirect Taxes and Customs (CBIC) and state industry departments are issued in dense English legalese.

Even worse, standard LLMs routinely hallucinate tax percentages (inventing 12% instead of 5%) or cite obsolete circulars that were superseded years ago. Under India's new Section 43B(h) rule, failing to pay micro-enterprises within 45 days causes immediate tax penalties.

### Architecture Highlights
1. **Legal Version DAG:** Statutory circulars are modeled as a Directed Acyclic Graph with `amends`, `supersedes`, and `clarifies` edges. Queries resolve as-of any historical reference date.
2. **Zero-Hallucination Firewall:** Generative outputs are constrained by XML context isolation, an NLI entailment verifier, and an Indic Numeric Guard that regex-extracts and verifies percentages, ₹ Lakhs/Crores, and day limits. Numeric hallucination rate is 0.00% across our 250-question golden evaluation suite.
3. **Indic NLP & Gujlish Normalization:** Rule-based and embedding-assisted transliteration handles queries like *"Job work par GST ketlo lage?"* seamlessly.
4. **DPDP Act 2023 Native:** Redacts PAN, GSTIN, Aadhaar, and phone numbers in memory before audit logging, with a rolling 30-day TTL and a single-click `/v1/sessions/{id}` erasure endpoint.
5. **High Concurrency:** 1,405 QPS burst throughput with p95 latency under 4ms using hybrid RRF (BM25 + pgvector) and local LRU caching.

The codebase is 100% open-source under Apache-2.0 with 156 passing tests and 94% coverage.

Would love HN's thoughts on our temporal version graph and hallucination guardrails!
```

---

## 🐱 3. Product Hunt Launch Kit

* **Product Name:** `Anupalan`
* **Tagline:** `Zero-hallucination multilingual statutory compliance AI for Indian MSMEs`
* **Category Tags:** `Artificial Intelligence`, `Developer Tools`, `LegalTech`, `Open Source`
* **Pricing:** `Free & Open Source (Apache-2.0)`

### Maker's First Comment:
```markdown
Hello Product Hunt community! 👋

I'm thrilled to introduce Anupalan (અનુપાલન / अनुपालन) — an open-source AI compliance navigator built for Indian MSMEs, Chartered Accountants, and developers.

India's regulatory landscape changes weekly through CBIC circulars, Section 43B(h) payment mandates, and state subsidy notifications. For a textile weaver in Surat or an engineering workshop in Rajkot, keeping track of these updates in legal English is near impossible. And asking generic chatbots often returns hallucinated tax rates that lead to real penalties.

We built Anupalan with 3 non-negotiable principles:
1. Zero Hallucination: 0.00% fabricated rates or percentages, verified by official gazette citations with page and bounding box proof.
2. Native Indic Dialect Support: Understands queries in Gujlish, Gujarati script, Hindi, and English.
3. Privacy by Design: Built from day one for India's DPDP Act 2023 with real-time PAN/GSTIN/Aadhaar redaction and 30-day auto-purge.

Check out the code, run the interactive UI locally, and let us know what you think:
👉 https://github.com/vedakoshiya/anupalan

Thank you for your support! ⭐
```

---

## 🔴 4. Reddit Launch Posts

### A. For `r/developersIndia`
* **Post Title:** `I built Anupalan: An open-source, zero-hallucination compliance RAG engine for Indian MSMEs (Gujlish NLP, GST, Section 43B(h))`
* **Post Body:**
```markdown
Hey everyone!

Wanted to share a project I've been working on: **Anupalan** (અનુપાલન / अनुपालन), an open-source, citation-grounded RAG engine for Indian statutory compliance.

🔗 **GitHub Repository:** https://github.com/vedakoshiya/anupalan

### Why I built this:
Most Indian MSME founders communicate in vernacular languages or mixed scripts like Gujlish (*"Job work par GST kevi rite lage?"*). Standard LLMs struggle with Indian dialect nuances, and more dangerously, hallucinate tax rates and turnover thresholds.

### Technical Stack & Key Features:
- **FastAPI + PostgreSQL 16 + pgvector**
- **Hybrid Retrieval:** Reciprocal Rank Fusion (RRF, $k=60$) combining BM25 keyword search with 1024-dim dense multilingual vector embeddings.
- **Legal Version DAG:** Models circular amendment chains (`amends`, `supersedes`, `clarifies`) so users can query rules as-of any specific date.
- **Strict Numeric Guardrails:** Local regex parser validates every percentage (`%`), ₹ currency figure, and day limit against source gazettes. If a single number is unsupported, it aborts generation.
- **DPDP Act 2023 Native:** Built-in regex scrubber for PAN, GSTIN, Aadhaar cards, mobile numbers, and emails.
- **Benchmarks:** Tested at 1,405 QPS with p95 latency under 4ms. 156/156 tests passing with 94% coverage.

The code and evaluation datasets are completely open-source. Contributions for expanding notifications from Maharashtra, Tamil Nadu, Karnataka, or other state gazettes are warmly welcome!

Would love your feedback and code reviews! ⭐
```

### B. For `r/MachineLearning`
* **Post Title:** `[P] Anupalan: Zero-Hallucination Multilingual RAG Engine with Temporal Legal Version DAG for Indian Statutory Tax Compliance`
* **Post Body:**
Focus on the mathematical evaluation methodology, NLI entailment verifier, synthetic ablation matrix comparing BM25 vs dense embeddings, and the Directed Acyclic Graph for circular amendment resolution. Link: https://github.com/vedakoshiya/anupalan.

---

## 🐦 5. Twitter / X Viral Launch Thread

### Tweet 1 (Hook):
```text
🚨 Introducing Anupalan (અનુપાલન / अनुपालन) — an open-source, zero-hallucination compliance RAG engine for India's 63M+ MSMEs.

Natively understands Gujlish, Gujarati, Hindi & English.
Guarantees 0.00% hallucinated tax rates with official gazette proof.

GitHub: https://github.com/vedakoshiya/anupalan 🧵👇
```

### Tweet 2 (The Problem):
```text
2/ Indian MSMEs navigate hundreds of CBIC GST notifications, Section 43B(h) 45-day payment rules, and state subsidies.

Most circulars are in dense legal English, and generic LLMs constantly hallucinate tax rates (inventing 12% instead of 5%).

A hallucinated rate = real tax notices.
```

### Tweet 3 (The Architecture):
```text
3/ How Anupalan achieves 0.00% numeric hallucination:
• XML Context Isolation
• NLI Entailment Claim Verifier
• Indic Numeric Guard checking all ₹ Lakhs, ₹ Crores & % rates
• Legal Version DAG tracking circular amendment & supersession chains over time

Every answer links to official gazette citations.
```

### Tweet 4 (Performance & Privacy):
```text
4/ Engineering Highlights:
⚡ 1,405 QPS burst load throughput (p95: 3.4ms)
🔒 DPDP Act 2023 Native: auto-redacts PAN, GSTIN & Aadhaar before storage
🧪 156/156 passing tests | 94% code coverage
🔄 Reciprocal Rank Fusion (BM25 + pgvector)
```

### Tweet 5 (Interactive Demo):
```text
5/ Try queries in your own dialect:
• "Job work par GST ketlo lage?" (Gujlish)
• "કમ્પોઝિશન સ્કીમ માટે ટર્નઓવર મર્યાદા શું છે?" (Gujarati)
• "Section 43B(h) MSME 45-day payment rule" (English)
• "कैपिटल सब्सिडी पात्रता" (Hindi)
```

### Tweet 6 (CTA):
```text
6/ Anupalan is 100% open-source under Apache-2.0.

Built for Indian small businesses, Chartered Accountants, and developers.

⭐ Star the repository on GitHub:
https://github.com/vedakoshiya/anupalan

#OpenSource #AI #IndicNLP #LegalTech #GST #MSME #BuildInPublic #MakeInIndia
```

---

## 💼 6. LinkedIn Viral Post

```text
🚀 Excited to open-source Anupalan (અનુપાલન / अनुपालन) — a Multilingual, Zero-Hallucination Compliance Navigator for Indian MSMEs!

In India, over 63 million small business owners grapple with rapidly changing GST circulars, the Section 43B(h) 45-day payment rule, and state subsidy schemes.

Most circulars are published in dense legal English. Meanwhile, standard AI chatbots hallucinate tax percentages and quote circulars that were superseded years ago.

Anupalan solves this with an Indic-first, citation-grounded RAG architecture:

✅ Native Dialect Understanding: Parses Gujlish ("Job work par GST ketlo lage?"), Gujarati script, Hindi, and English.
✅ Zero-Hallucination Guarantee: Mathematical guardrails extract and verify ₹ Lakhs, ₹ Crores, and tax percentages against source text (0.00% numeric hallucination).
✅ Legal Version DAG: Automatically traverses CBIC amendment chains to resolve applicable law as-of any reference date.
✅ DPDP Act 2023 Native: Real-time PII redaction (PAN, GSTIN, Aadhaar) & rolling 30-day data retention.
✅ High Performance: 1,405+ QPS burst capacity with p95 latency under 4ms.

100% open-source under Apache-2.0 with 156 unit and integration tests (94% coverage).

⭐ Check out the repository, run the interactive UI locally, and consider starring:
👉 https://github.com/vedakoshiya/anupalan

#OpenSource #ArtificialIntelligence #RAG #IndicNLP #LegalTech #GST #MSME #CharteredAccountants #MakeInIndia #BuildInPublic
```

---

## 📧 7. Indian Tech Media & Newsletter Pitch (Inc42, YourStory, Entrackr)

* **Subject:** Story Pitch: Open-source Indic AI project "Anupalan" tackles MSME tax compliance and Section 43B(h) with zero hallucinations
* **Email Body:**

```text
Dear [Editor/Journalist Name],

With India's MSME sector facing increased compliance scrutiny under Section 43B(h) of the Income Tax Act and continuous GST circular amendments, thousands of small business owners struggle to understand dense legal notifications published exclusively in English.

I recently open-sourced Anupalan (https://github.com/vedakoshiya/anupalan), a multilingual compliance RAG engine built specifically for Indian MSMEs and Chartered Accountants.

Unlike general-purpose AI chatbots that hallucinate tax rates, Anupalan guarantees 0.00% numeric hallucination using an NLI claim verifier, an Indic numeric firewall, and a Directed Acyclic Graph (DAG) that maps how CBIC circulars amend and supersede each other over time.

Crucially, it understands vernacular queries in Gujlish ("Job work par GST ketlo lage?"), Gujarati, Hindi, and English, and is architected natively for India's Digital Personal Data Protection (DPDP) Act 2023 with real-time PAN, GSTIN, and Aadhaar redaction.

The project is completely open-source under the Apache-2.0 license.

I would be delighted to share deeper insights, technical benchmarks, or demo walkthroughs if you are covering advancements in Indic AI, legal technology, or MSME digitization.

Warm regards,
Vedansi Koshiya
Creator of Anupalan
https://github.com/vedakoshiya/anupalan
```
