"""CI Quality Gate: Evaluates metrics against thresholds in Section 1.4 & 9.2.

Exits with code 0 if all quality gates pass, exits with code 1 if any metric regresses.
"""

import sys
from pathlib import Path

# Add project root to sys.path if invoked directly
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from eval.evaluator import BenchmarkEvaluator

GATED_THRESHOLDS = {
    "retrieval_recall_at_5": 0.85,          # Staging threshold (Target 0.90)
    "retrieval_mrr": 0.75,                  # Staging threshold (Target 0.80)
    "citation_precision": 0.90,             # Staging threshold (Target 0.95)
    "numeric_hallucination_rate": 0.02,     # Staging threshold (Target < 0.01)
    "abstention_accuracy": 0.85,            # Staging threshold (Target >= 0.90)
}


def run_gate_check() -> bool:
    print("Running Anupalan CI Evaluation Gate Check...")
    evaluator = BenchmarkEvaluator()
    summary = evaluator.run_full_benchmark()

    failures = []

    # Check Recall@5
    if summary.retrieval_recall_at_5 < GATED_THRESHOLDS["retrieval_recall_at_5"]:
        failures.append(
            f"Recall@5 {summary.retrieval_recall_at_5:.3f} is below threshold {GATED_THRESHOLDS['retrieval_recall_at_5']:.3f}"
        )

    # Check MRR
    if summary.retrieval_mrr < GATED_THRESHOLDS["retrieval_mrr"]:
        failures.append(
            f"MRR {summary.retrieval_mrr:.3f} is below threshold {GATED_THRESHOLDS['retrieval_mrr']:.3f}"
        )

    # Check Citation Precision
    if summary.citation_precision < GATED_THRESHOLDS["citation_precision"]:
        failures.append(
            f"Citation Precision {summary.citation_precision:.3f} is below threshold {GATED_THRESHOLDS['citation_precision']:.3f}"
        )

    # Check Numeric Hallucination
    if summary.numeric_hallucination_rate > GATED_THRESHOLDS["numeric_hallucination_rate"]:
        failures.append(
            f"Numeric Hallucination Rate {summary.numeric_hallucination_rate:.3f} exceeds threshold {GATED_THRESHOLDS['numeric_hallucination_rate']:.3f}"
        )

    # Check Abstention
    if summary.abstention_accuracy < GATED_THRESHOLDS["abstention_accuracy"]:
        failures.append(
            f"Abstention Accuracy {summary.abstention_accuracy:.3f} is below threshold {GATED_THRESHOLDS['abstention_accuracy']:.3f}"
        )

    if failures:
        print("\n[FAIL] CI EVALUATION GATE FAILED with the following regressions:")
        for f in failures:
            print(f"  - {f}")
        return False

    print("\n[PASS] ALL CI EVALUATION GATES PASSED CLEANLY!")
    print(f"  * Recall@5:                    {summary.retrieval_recall_at_5:.3f}")
    print(f"  * MRR:                         {summary.retrieval_mrr:.3f}")
    print(f"  * Citation Precision:          {summary.citation_precision:.3f}")
    print(f"  * Numeric Hallucination Rate:  {summary.numeric_hallucination_rate:.3f}")
    print(f"  * Abstention Accuracy:         {summary.abstention_accuracy:.3f}")
    return True


if __name__ == "__main__":
    passed = run_gate_check()
    sys.exit(0 if passed else 1)
