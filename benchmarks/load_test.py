"""Load testing and burst benchmark framework for Anupalan compliance API.

Simulates 20 QPS burst query streams across trilingual queries (Gujarati, Hindi, English, Gujlish)
and verifies latency SLAs: p50 < 4.0s, p95 < 8.0s, 0.00% error rate (Spec Section 5 & 11).
"""

import json
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from packages.generation.src.generation.schemas import AskRequest, AskResponse
from services.api.src.main import ask_question, health_check


@dataclass
class LoadBenchmarkResult:
    total_queries: int
    successful_queries: int
    failed_queries: int
    duration_seconds: float
    actual_qps: float
    p50_latency_sec: float
    p90_latency_sec: float
    p95_latency_sec: float
    p99_latency_sec: float
    min_latency_sec: float
    max_latency_sec: float
    avg_latency_sec: float
    error_rate: float
    sla_met: bool
    target_p95_sla_sec: float
    target_p50_sla_sec: float


class LoadTestRunner:
    """Multi-threaded synthetic burst load tester for statutory Q&A services."""

    SAMPLE_QUERIES = [
        {"query": "Job work par GST kevi rite lage?", "as_of": "2026-10-26", "lang": "gu"},
        {"query": "Textile job work rate in Surat 5% or 12%?", "as_of": "2024-01-01", "lang": "en"},
        {"query": "કમ્પોઝિશન સ્કીમ માટે ટર્નઓવર મર્યાદા શું છે?", "as_of": "2026-10-26", "lang": "gu"},
        {"query": "गुजरात एमएसएमई कैपिटल सब्सिडी के लिए पात्रता क्या है?", "as_of": "2026-10-26", "lang": "hi"},
        {"query": "Composition scheme limit in 2018?", "as_of": "2018-01-01", "lang": "en"},
        {"query": "What is the payment timeline under Section 43B(h)?", "as_of": "2026-10-26", "lang": "en"},
        {"query": "Kapda na job work par ketlo tax lage che?", "as_of": "2026-10-26", "lang": "gu"},
        {"query": "MSME interest subsidy scheme for Gujarat textile units", "as_of": "2026-10-26", "lang": "en"},
    ]

    def __init__(
        self,
        target_p50_sla: float = 4.0,
        target_p95_sla: float = 8.0,
    ):
        self.target_p50_sla = target_p50_sla
        self.target_p95_sla = target_p95_sla

    def _execute_single_query(self, query_spec: dict[str, str]) -> tuple[bool, float, str | None]:
        """Executes a single compliance request and returns (success, latency_seconds, error_message)."""
        start_time = time.time()
        try:
            req = AskRequest(
                query=query_spec["query"],
                as_of=date.fromisoformat(query_spec["as_of"]),
                language=query_spec.get("lang"),
            )
            resp = ask_question(req)
            duration = time.time() - start_time
            return True, duration, None
        except Exception as e:
            duration = time.time() - start_time
            return False, duration, str(e)

    def run_burst_benchmark(
        self,
        total_queries: int = 50,
        concurrency: int = 10,
    ) -> LoadBenchmarkResult:
        """Executes concurrent burst queries and computes statistical latency distribution."""
        latencies: list[float] = []
        failures: list[str] = []

        wall_start = time.time()

        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = []
            for i in range(total_queries):
                spec = self.SAMPLE_QUERIES[i % len(self.SAMPLE_QUERIES)]
                futures.append(executor.submit(self._execute_single_query, spec))

            for fut in as_completed(futures):
                success, duration, err = fut.result()
                latencies.append(duration)
                if not success:
                    failures.append(err or "Unknown error")

        wall_duration = time.time() - wall_start
        actual_qps = round(total_queries / wall_duration, 2) if wall_duration > 0 else 0.0

        sorted_latencies = sorted(latencies)
        p50 = statistics.median(sorted_latencies) if sorted_latencies else 0.0
        p90 = sorted_latencies[int(len(sorted_latencies) * 0.90)] if sorted_latencies else 0.0
        p95 = sorted_latencies[int(len(sorted_latencies) * 0.95)] if sorted_latencies else 0.0
        p99 = sorted_latencies[int(len(sorted_latencies) * 0.99)] if sorted_latencies else 0.0

        avg_lat = statistics.mean(sorted_latencies) if sorted_latencies else 0.0
        min_lat = min(sorted_latencies) if sorted_latencies else 0.0
        max_lat = max(sorted_latencies) if sorted_latencies else 0.0

        error_rate = len(failures) / total_queries if total_queries > 0 else 0.0
        sla_met = (
            p95 <= self.target_p95_sla
            and p50 <= self.target_p50_sla
            and error_rate == 0.0
        )

        return LoadBenchmarkResult(
            total_queries=total_queries,
            successful_queries=total_queries - len(failures),
            failed_queries=len(failures),
            duration_seconds=round(wall_duration, 3),
            actual_qps=actual_qps,
            p50_latency_sec=round(p50, 4),
            p90_latency_sec=round(p90, 4),
            p95_latency_sec=round(p95, 4),
            p99_latency_sec=round(p99, 4),
            min_latency_sec=round(min_lat, 4),
            max_latency_sec=round(max_lat, 4),
            avg_latency_sec=round(avg_lat, 4),
            error_rate=round(error_rate, 4),
            sla_met=sla_met,
            target_p95_sla_sec=self.target_p95_sla,
            target_p50_sla_sec=self.target_p50_sla,
        )

    def save_report(self, result: LoadBenchmarkResult, output_path: Path | None = None) -> Path:
        """Saves structured JSON benchmark metrics report."""
        if output_path is None:
            output_dir = Path(__file__).resolve().parent / "results"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / "load_test_report.json"

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(asdict(result), f, indent=2)

        return output_path


if __name__ == "__main__":
    print("Executing Anupalan 20 QPS Burst Load Test...")
    runner = LoadTestRunner()
    res = runner.run_burst_benchmark(total_queries=50, concurrency=10)
    out_file = runner.save_report(res)

    print("\n--- Load Test Benchmark Results ---")
    print(f"Total Queries:     {res.total_queries}")
    print(f"Successful:        {res.successful_queries} ({100 - res.error_rate * 100:.1f}%)")
    print(f"Failed:            {res.failed_queries}")
    print(f"Duration:          {res.duration_seconds:.2f}s")
    print(f"Throughput:        {res.actual_qps:.1f} queries/sec")
    print(f"p50 Latency:       {res.p50_latency_sec * 1000:.1f}ms (SLA target: < {res.target_p50_sla_sec}s)")
    print(f"p95 Latency:       {res.p95_latency_sec * 1000:.1f}ms (SLA target: < {res.target_p95_sla_sec}s)")
    print(f"p99 Latency:       {res.p99_latency_sec * 1000:.1f}ms")
    print(f"SLA Target Met:    {'YES [PASS]' if res.sla_met else 'NO [FAIL]'}")
    print(f"Report JSON:       {out_file}")
