"""CLI runner for generation and citation benchmark evaluation."""

import sys
from pathlib import Path

# Add project root to sys.path if invoked directly
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from eval.evaluator import BenchmarkEvaluator


def main():
    print("=" * 60)
    print("ANUPALAN BENCHMARK: GENERATION & CITATION EVALUATION")
    print("=" * 60)

    evaluator = BenchmarkEvaluator()
    metrics = evaluator.evaluate_end_to_end_generation()

    print(f"Citation Precision:         {metrics['citation_precision']:.3f} (Target >= 0.950)")
    print(f"Citation Recall:            {metrics['citation_recall']:.3f} (Target >= 0.900)")
    print(f"Numeric Hallucination Rate: {metrics['numeric_hallucination_rate']:.3f} (Target < 0.010)")
    print(f"Abstention Accuracy:        {metrics['abstention_accuracy']:.3f} (Target >= 0.900)")
    print("=" * 60)

    return metrics


if __name__ == "__main__":
    main()
