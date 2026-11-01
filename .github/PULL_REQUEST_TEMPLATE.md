## 📋 Pull Request Description

### Summary of Changes
<!-- Provide a brief description of what this PR introduces or fixes. -->

### Related Issue(s)
<!-- Closes #123 -->

---

## 🔍 Type of Change
- [ ] 🐛 Bug fix (non-breaking change fixing an issue or citation discrepancy)
- [ ] ✨ New feature (addition to query engine, retrieval, or UI)
- [ ] 📜 Corpus expansion (added new gazette notifications or glossary terms)
- [ ] ⚡ Performance optimization (latency reduction, caching, index improvements)
- [ ] 📚 Documentation update (runbooks, specifications, tutorials)

---

## 🧪 Quality Gate & Testing Verification

Please verify that your changes adhere to Anupalan's strict quality thresholds:

- [ ] All 156+ unit and integration tests pass: `python -m pytest tests`
- [ ] Code coverage remains $\ge 90\%$: `pytest --cov=.`
- [ ] Automated evaluation gate passes: `python eval/eval_gate.py`
  - Recall@5 $\ge 0.900$
  - Hallucinated rates $= 0.00\%$
  - Correct abstention $\ge 0.900$
- [ ] Static security audit passes: `python scripts/security_audit.py` (No API keys or unscrubbed PII)
- [ ] Linting & type safety pass: `ruff check .`

---

## 📜 Legal & Compliance Check
- [ ] Changes adhere to the Apache-2.0 license.
- [ ] No copyrighted proprietary database or unverified non-gazette text committed.
