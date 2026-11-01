# Contributing to Anupalan (અનુપાલન / अनुपालन)

First off, thank you for considering contributing to **Anupalan**! Anupalan is an open-source, public-interest compliance project dedicated to Indian MSMEs, tax practitioners, and developers building Indic AI.

---

## 🌟 How You Can Contribute

1. **Expanding the Statutory Corpus:** Add new CBIC GST notifications, state MSME policies (e.g. Maharashtra, Tamil Nadu, Rajasthan), or Central Labour Codes to `data/fixtures/core_instruments.json`.
2. **Vernacular Glossary & Transliteration:** Add new dialect terms, Gujlish/Hinglish tax phrases, or regional accounting slang to `data/fixtures/glossary_seed.json`.
3. **Adversarial & Evaluation Datasets:** Contribute tricky compliance edge cases, false-premise tax questions, or historical amendment queries to `eval/datasets/`.
4. **Front-End & Mobile Interfaces:** Improve the Web UI, add dark mode, or help build WhatsApp / Telegram bot bridges.
5. **Bug Reports & Performance:** Report inaccurate citations, edge-case parser failures, or latency bottlenecks.

---

## 🛠️ Development Setup

```bash
# 1. Fork and clone the repository
git clone https://github.com/<your-username>/anupalan.git
cd anupalan

# 2. Set up virtual environment
python -m venv .venv
source .venv/bin/activate       # On Windows: .venv\Scripts\activate

# 3. Install in development mode
pip install -e ".[dev]"

# 4. Run tests to ensure everything is working
python -m pytest tests --cov=.
```

---

## 🧪 Quality Standards & PR Checklist

Before submitting a Pull Request, ensure that:
- [ ] All tests pass: `python -m pytest tests` (100% pass rate).
- [ ] Code coverage remains $\ge 90\%$.
- [ ] CI evaluation gate passes: `python eval/eval_gate.py` (Recall $\ge 0.90$, Zero hallucinations).
- [ ] Security audit passes: `python scripts/security_audit.py` (No API keys or PII committed).
- [ ] Code follows standard style conventions.

---

## 📜 Code of Conduct

We are committed to providing a welcoming, inclusive, and harassment-free environment for everyone. Please be respectful and constructive in all discussions, issues, and code reviews.

---

## 👩‍💻 Questions & Community

Have questions or want to discuss architecture?
* Open an issue: [https://github.com/vedakoshiya/anupalan/issues](https://github.com/vedakoshiya/anupalan/issues)
* Repository: [https://github.com/vedakoshiya/anupalan](https://github.com/vedakoshiya/anupalan)
