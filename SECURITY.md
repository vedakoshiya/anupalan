# Security Policy

## 🔒 Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

---

## 🛡️ Reporting a Vulnerability

The Anupalan engineering team takes data privacy, secret leak prevention, and regulatory accuracy seriously.

If you discover a security vulnerability, private data leakage (e.g. failure in PII scrubbing under the DPDP Act 2023), prompt injection bypass, or secret credential exposure:

1. **DO NOT** create a public GitHub issue.
2. Email the maintainer directly at: `vedakoshiya@users.noreply.github.com` with the subject line `[SECURITY REPORT] Anupalan Vulnerability`.
3. Please include:
   - Type of issue (e.g. prompt injection, PII leak, denial of service)
   - Steps or payload to reproduce the issue
   - Potential impact
4. We will acknowledge receipt within 48 hours and work with you to patch and disclose the issue responsibly.

---

## 🏛️ DPDP Act 2023 Commitment

Anupalan operates under strict data minimization guidelines:
* Real-time automated PII scrubbing (PAN, GSTIN, Aadhaar, Phone, Email).
* Rolling 30-day query retention TTL.
* Instant user session deletion via `DELETE /v1/sessions/{id}`.
