"""External sync entrypoint for cron / CI scheduler.

Usage:
  python -m scripts.run_sync --region US --period 7d
"""

from __future__ import annotations

import argparse
import logging

from app.api.routes_trends import get_trends_service
from app.config import settings

logging.basicConfig(level=logging.INFO)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one sync cycle")
    parser.add_argument("--region", default=settings.default_region)
    parser.add_argument("--period", default=settings.default_period)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    service = get_trends_service()
    saved = service.sync(region=args.region, period=args.period)
    logging.info("sync_finished saved=%s region=%s period=%s", saved, args.region, args.period)


if __name__ == "__main__":
    main()
