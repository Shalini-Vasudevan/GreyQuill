import csv
import sys
from pathlib import Path

from score_pair import PLAN, score_pair


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit("None")
    path = Path(__file__).with_name("customer-records.csv")
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = {r["record_id"]: r for r in csv.DictReader(f)}
    for rid in sys.argv[1:]:
        if rid not in rows:
            sys.exit(f"no such record: {rid}")
    a, b = rows[sys.argv[1]], rows[sys.argv[2]]
    result = score_pair(a, b, PLAN)
    print(f"{a['record_id']}: {a['name']}")
    print(f"{b['record_id']}: {b['name']}")
    print(f"confidence: {result.confidence:.3f}")
    print(f"algorithm:  {result.algorithm}")
    for field, score in result.field_scores.items():
        print(f"  {field:14s} {score:.2f}")


if __name__ == "__main__":
    main()
