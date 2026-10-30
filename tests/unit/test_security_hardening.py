"""Unit tests for the SecurityAuditor and injection defenses."""

import unittest
from scripts.security_audit import SecurityAuditor


class TestSecurityHardening(unittest.TestCase):
    def setUp(self):
        self.auditor = SecurityAuditor()

    def test_gitignore_rules(self):
        gi_checks = self.auditor.audit_gitignore_coverage()
        self.assertTrue(gi_checks[".env"])
        self.assertTrue(gi_checks["secrets/"])
        self.assertTrue(gi_checks["pycache"])
        self.assertTrue(gi_checks["traces"])

    def test_no_secrets_in_repo(self):
        leaks = self.auditor.audit_secrets_in_codebase()
        self.assertEqual(len(leaks), 0, f"Found secret leaks: {leaks}")

    def test_prompt_injection_defense(self):
        results = self.auditor.audit_prompt_injections()
        self.assertEqual(len(results), len(self.auditor.INJECTION_PAYLOADS))
        for r in results:
            self.assertTrue(
                r["defended"],
                f"Payload failed prompt injection defense: {r['payload']}",
            )

    def test_full_security_audit_pass(self):
        report = self.auditor.run_full_security_audit()
        self.assertEqual(report["status"], "PASS")
        self.assertTrue(report["zero_secrets_detected"])
        self.assertTrue(report["prompt_injections_defended"])


if __name__ == "__main__":
    unittest.main()
