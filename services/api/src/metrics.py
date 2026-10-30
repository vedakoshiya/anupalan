"""Prometheus operational metrics collector for Anupalan compliance services.

Tracks HTTP traffic, p95 query latencies, abstention ratios, and feedback ratings
exporting standard Prometheus text exposition format (Spec Section 8.1 & 11).
"""

import time
from collections import defaultdict
from typing import Any


class PrometheusMetricsCollector:
    """In-memory thread-safe metrics collector with Prometheus text exporter."""

    def __init__(self):
        # Counters
        self.http_requests: dict[tuple[str, str, int], int] = defaultdict(int)
        self.answers_generated: dict[tuple[str, bool], int] = defaultdict(int)
        self.feedback_recorded: dict[str, int] = defaultdict(int)
        self.dpdp_purges_total = 0
        self.cache_hits_total = 0
        self.cache_misses_total = 0

        # Latencies in seconds
        self.latencies: list[float] = []

    def record_cache_hit(self) -> None:
        """Records a query cache hit."""
        self.cache_hits_total += 1

    def record_cache_miss(self) -> None:
        """Records a query cache miss."""
        self.cache_misses_total += 1

    def record_request(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        duration_sec: float,
    ) -> None:
        """Records an HTTP transaction and its latency."""
        self.http_requests[(method.upper(), endpoint, status_code)] += 1
        self.latencies.append(round(duration_sec, 4))
        # Keep recent 1000 latencies to avoid unbounded memory growth
        if len(self.latencies) > 1000:
            self.latencies.pop(0)

    def record_answer(self, language: str, abstained: bool) -> None:
        """Records an answer synthesis event."""
        self.answers_generated[(language, abstained)] += 1

    def record_feedback(self, rating: int) -> None:
        """Records user thumbs-up / thumbs-down evaluation."""
        key = "thumbs_up" if rating > 0 else "thumbs_down"
        self.feedback_recorded[key] += 1

    def record_dpdp_purge(self, count: int) -> None:
        """Records records purged under DPDP retention policies."""
        self.dpdp_purges_total += count

    def calculate_p95_latency(self) -> float:
        """Computes p95 latency across recent requests."""
        if not self.latencies:
            return 0.0
        sorted_latencies = sorted(self.latencies)
        p95_idx = int(len(sorted_latencies) * 0.95)
        return sorted_latencies[min(p95_idx, len(sorted_latencies) - 1)]

    def export_prometheus_text(self, indexed_chunks_count: int = 0) -> str:
        """Exports metrics in standard Prometheus exposition format."""
        lines = []

        # 1. HTTP Requests Total
        lines.append("# HELP anupalan_http_requests_total Total HTTP requests handled.")
        lines.append("# TYPE anupalan_http_requests_total counter")
        for (m, ep, code), count in sorted(self.http_requests.items()):
            lines.append(f'anupalan_http_requests_total{{method="{m}",endpoint="{ep}",status="{code}"}} {count}')
        if not self.http_requests:
            lines.append('anupalan_http_requests_total{method="GET",endpoint="/v1/health",status="200"} 0')

        # 2. Answers Generated
        lines.append("\n# HELP anupalan_answers_total Total statutory answers generated.")
        lines.append("# TYPE anupalan_answers_total counter")
        for (lang, abstained), count in sorted(self.answers_generated.items()):
            lines.append(f'anupalan_answers_total{{language="{lang}",abstained="{str(abstained).lower()}"}} {count}')

        # 3. User Feedback
        lines.append("\n# HELP anupalan_feedback_total Total end-user satisfaction ratings.")
        lines.append("# TYPE anupalan_feedback_total counter")
        for rating_key, count in sorted(self.feedback_recorded.items()):
            lines.append(f'anupalan_feedback_total{{rating="{rating_key}"}} {count}')

        # 4. Indexed Chunks Gauge
        lines.append("\n# HELP anupalan_indexed_chunks_total Active statutory chunks indexed.")
        lines.append("# TYPE anupalan_indexed_chunks_total gauge")
        lines.append(f"anupalan_indexed_chunks_total {indexed_chunks_count}")

        # 5. Latency p95 Gauge
        lines.append("\n# HELP anupalan_query_latency_p95_seconds Estimated 95th percentile query latency.")
        lines.append("# TYPE anupalan_query_latency_p95_seconds gauge")
        lines.append(f"anupalan_query_latency_p95_seconds {self.calculate_p95_latency():.4f}")

        # 6. DPDP Purges Total
        lines.append("\n# HELP anupalan_dpdp_purged_records_total Records purged under DPDP Act 2023.")
        lines.append("# TYPE anupalan_dpdp_purged_records_total counter")
        lines.append(f"anupalan_dpdp_purged_records_total {self.dpdp_purges_total}")

        # 7. Query Cache Counters
        lines.append("\n# HELP anupalan_cache_hits_total Total query cache hits.")
        lines.append("# TYPE anupalan_cache_hits_total counter")
        lines.append(f"anupalan_cache_hits_total {self.cache_hits_total}")

        lines.append("\n# HELP anupalan_cache_misses_total Total query cache misses.")
        lines.append("# TYPE anupalan_cache_misses_total counter")
        lines.append(f"anupalan_cache_misses_total {self.cache_misses_total}")

        return "\n".join(lines) + "\n"
