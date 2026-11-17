from __future__ import annotations

import os
from typing import Any
import requests


def trigger_high_risk_followup(supplier: dict[str, Any], score: dict[str, Any], brief: str) -> tuple[bool, str]:
    """Send a small JSON payload to an optional n8n webhook for High/Critical assessments."""
    if score.get("tier") not in {"High", "Critical"}:
        return False, "Workflow not required for Low/Medium risk."
    url = os.getenv("N8N_WEBHOOK_URL", "").strip()
    if not url:
        return False, "N8N_WEBHOOK_URL is not configured."
    payload = {
        "supplier_id": supplier.get("supplier_id"),
        "supplier_name": supplier.get("supplier_name"),
        "overall_score": score.get("overall_score"),
        "tier": score.get("tier"),
        "top_drivers": score.get("top_drivers", [])[:5],
        "brief": brief,
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        return True, f"n8n webhook accepted the assessment ({resp.status_code})."
    except requests.RequestException as exc:
        return False, f"n8n webhook failed: {exc}"
