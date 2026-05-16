import argparse
import sys
import time
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.log_generator import generate_log


def main():
    parser = argparse.ArgumentParser(description="Send simulated application logs to the monitoring API.")
    parser.add_argument("--api-url", default="http://localhost:5000/logs", help="Log ingestion endpoint")
    parser.add_argument("--count", type=int, default=20, help="Number of logs to send")
    parser.add_argument("--interval", type=float, default=0.2, help="Delay between logs in seconds")
    parser.add_argument("--mode", choices=["normal", "anomaly", "mixed"], default="mixed")
    args = parser.parse_args()

    for index in range(args.count):
        payload = generate_log(mode=args.mode)
        response = requests.post(args.api_url, json=payload, timeout=10)
        response.raise_for_status()
        print(f"sent={index + 1} status={response.status_code} service={payload['service']} level={payload['level']}")
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
