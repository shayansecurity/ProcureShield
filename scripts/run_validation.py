from __future__ import annotations

import json
from pathlib import Path
import pandas as pd

from app.config import DATA_PATH, ROOT
from app.validation import validate_expected_tiers, validate_repeatability, validate_sensitivity, validate_rag


def main() -> None:
    df = pd.read_csv(DATA_PATH)
    groups = {
        "tier_accuracy": validate_expected_tiers(df),
        "repeatability": validate_repeatability(df, repeats=3),
        "sensitivity": validate_sensitivity(df.iloc[0].to_dict()),
        "rag_relevance": validate_rag(),
    }
    summary = {}
    all_results = {}
    for name, items in groups.items():
        passed = sum(1 for x in items if x.passed)
        summary[name] = {"passed": passed, "total": len(items), "pct": round(100 * passed / len(items), 1) if items else 0}
        all_results[name] = [x.to_dict() for x in items]
    payload = {"summary": summary, "results": all_results}
    out = ROOT / "outputs" / "validation_summary.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    failed = [x for items in groups.values() for x in items if not x.passed]
    if failed:
        print("\nFAILED CHECKS:")
        for x in failed:
            print(f"- {x.name}: {x.observed} (expected {x.expected})")
        raise SystemExit(1)

if __name__ == "__main__":
    main()
