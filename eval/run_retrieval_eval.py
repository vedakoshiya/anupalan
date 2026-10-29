"""CLI runner for retrieval benchmark evaluation."""

import json
import sys
from pathlib import Path

# Add project root to sys.path if invoked directly
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from eval.evaluator import BenchmarkEvaluator


def main():
    print("=" * 60)
    print("ANUPALAN BENCHMARK: RETRIEVAL EVALUATION")
    print("=" * 60)

    evaluator = BenchmarkEvaluator()
    metrics = evaluator.evaluate_retrieval()

    print(f"Retrieval Recall@5: {metrics['recall@5']:.3f} (Target >= 0.900)")
    print(f"Retrieval MRR:      {metrics['mrr']:.3f} (Target >= 0.800)")
    print(f"Retrieval nDCG@5:   {metrics['ndcg@5']:.3f} (Target >= 0.850)")
    print("=" * 60)

    return metrics


if __name__ == "__main__":
    main()
