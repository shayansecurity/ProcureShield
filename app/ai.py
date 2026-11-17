from __future__ import annotations

import os
from typing import Any


def _evidence_text(evidence: list[dict]) -> str:
    parts = []
    for i, item in enumerate(evidence, 1):
        parts.append(f"[{i}] {item.get('source')} / {item.get('section')}: {item.get('text')}")
    return "\n".join(parts)


def fallback_brief(supplier: dict[str, Any], score: dict[str, Any], evidence: list[dict]) -> str:
    drivers = score.get("top_drivers", [])[:4]
    driver_lines = "; ".join(f"{d['label']} ({d['risk_points']:.0f}/100)" for d in drivers)
    actions = []
    for d in drivers:
        rec = d.get("recommendation")
        if rec and rec not in actions:
            actions.append(rec)
    evidence_sources = ", ".join(sorted({e.get("source", "") for e in evidence if e.get("source")})) or "No evidence retrieved"
    return (
        f"{supplier.get('supplier_name','Supplier')} is assessed at {score['overall_score']:.1f}/100 ({score['tier']} risk). "
        f"The strongest current risk drivers are {driver_lines}. "
        f"Priority actions: {' '.join(actions[:3])} "
        f"Evidence reviewed: {evidence_sources}. "
        "This brief is decision support only; unknown or missing supplier evidence should remain Not Verified rather than assumed compliant."
    )


def generate_risk_brief(supplier: dict[str, Any], score: dict[str, Any], evidence: list[dict]) -> tuple[str, str]:
    """Return (brief, mode). Uses OpenAI Responses API when configured; otherwise safe local fallback."""
    if not os.getenv("OPENAI_API_KEY"):
        return fallback_brief(supplier, score, evidence), "local-fallback"
    try:
        from openai import OpenAI
        client = OpenAI()
        model = os.getenv("OPENAI_MODEL", "gpt-6-luna")
        prompt = f"""You are a supplier cyber-risk analyst. Write a concise risk brief using ONLY the supplied facts and evidence.
Rules:
- The numeric score and tier are authoritative; never recalculate or override them.
- Do not invent controls, certifications, incidents, or contract terms.
- If evidence is missing, say Not Verified.
- Separate observed risk drivers from recommended actions.
- Keep the brief under 220 words.

SUPPLIER RECORD:\n{supplier}\n\nDETERMINISTIC SCORE:\n{score}\n\nRETRIEVED EVIDENCE:\n{_evidence_text(evidence)}
"""
        response = client.responses.create(model=model, input=prompt)
        text = (response.output_text or "").strip()
        if not text:
            raise RuntimeError("Empty model response")
        return text, f"openai:{model}"
    except Exception:
        return fallback_brief(supplier, score, evidence), "local-fallback-after-error"
