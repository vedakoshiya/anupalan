#!/usr/bin/env python3
"""Production Regulatory Gazette Crawler Runner for Anupalan.

Executes ethical, rate-limited crawling across official Indian portals:
- CBIC GST Notifications & Circulars
- MCA Corporate Affairs & MSME Rule Amendments

Discovers new statutory instruments, extracts notification metadata,
enforces SHA-256 CAS deduplication, and indexes into persistent storage.
"""

import argparse
import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.ingestion.src.crawler import RegulatoryGazetteCrawler
from services.ingestion.src.pipeline import IngestionPipeline
from services.ingestion.src.storage import LocalImmutableStorage


async def run_crawler(
    sources: list[str],
    max_items: int = 5,
    dry_run: bool = False,
    data_dir: Path | None = None,
) -> int:
    target_data_dir = data_dir or (PROJECT_ROOT / "data" / "documents")
    target_data_dir.mkdir(parents=True, exist_ok=True)

    storage = LocalImmutableStorage(base_directory=target_data_dir)
    pipeline = IngestionPipeline(storage=storage) if not dry_run else None
    crawler = RegulatoryGazetteCrawler(rate_limit_delay=0.5, timeout_seconds=15.0)

    print("=" * 80)
    print("        ANUPALAN REGULATORY GAZETTE CRAWLER & DISCOVERY DAEMON")
    print("=" * 80)
    print(f"[*] Started at:      {datetime.utcnow().isoformat()}Z")
    print(f"[*] Mode:            {'DRY RUN (Discovery Only)' if dry_run else 'PERSISTENT INGESTION'}")
    print(f"[*] Storage Dir:     {target_data_dir}")
    print(f"[*] Sources Target:  {', '.join(sources)}")
    print(f"[*] Max per Source:  {max_items}")
    print("-" * 80)

    total_discovered = 0
    total_ingested = 0
    total_skipped = 0
    total_errors = 0

    for source_key in sources:
        print(f"\n[+] Crawling source: {source_key} ...")
        report = await crawler.crawl_source(
            source_key=source_key,
            pipeline=pipeline,
            max_entries=max_items,
        )

        print(f"    - Discovered:  {report.items_discovered}")
        print(f"    - Downloaded:  {report.items_downloaded}")
        print(f"    - Ingested:    {report.items_ingested}")
        print(f"    - Skipped:     {report.items_skipped} (Deduplicated)")
        if report.errors:
            print(f"    - Errors ({len(report.errors)}):")
            for err in report.errors[:3]:
                print(f"        * {err}")
            if len(report.errors) > 3:
                print(f"        * ... and {len(report.errors) - 3} more")

        total_discovered += report.items_discovered
        total_ingested += report.items_ingested
        total_skipped += report.items_skipped
        total_errors += len(report.errors)

    print("\n" + "=" * 80)
    print(f"CRAWL COMPLETE: Discovered={total_discovered} | Ingested={total_ingested} | Skipped={total_skipped} | Errors={total_errors}")
    print("=" * 80)
    return 0 if total_errors == 0 else 1


def main():
    parser = argparse.ArgumentParser(description="Anupalan Regulatory Gazette Crawler CLI")
    parser.add_argument(
        "--source",
        choices=["CBIC_GST_NOTIFICATIONS", "CBIC_GST_CIRCULARS", "MCA_NOTIFICATIONS", "ALL"],
        default="ALL",
        help="Regulatory source to crawl (default: ALL)",
    )
    parser.add_argument(
        "--max",
        type=int,
        default=5,
        help="Maximum entries to scrape per source (default: 5)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Discover and parse entries without storing PDFs or chunks",
    )
    args = parser.parse_args()

    if args.source == "ALL":
        target_sources = list(RegulatoryGazetteCrawler.SOURCES.keys())
    else:
        target_sources = [args.source]

    exit_code = asyncio.run(
        run_crawler(
            sources=target_sources,
            max_items=args.max,
            dry_run=args.dry_run,
        )
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
