from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Callable

import pandas as pd

from .scoring import score_supplier
from .rag import LocalTfidfRetriever


@dataclass
class ValidationResult:
    name: str
    passed: bool
    observed: str
    expected: str

    def to_dict(self) -> dict:
        return self.__dict__.copy()


def validate_expected_tiers(df: pd.DataFrame) -> list[ValidationResult]:
    results = []
    for _, row in df.iterrows():
        record = row.to_dict()
        score = score_supplier(record)
        expected = str(record["expected_tier"])
        results.append(ValidationResult(
            f"Tier: {record['supplier_id']}", score.tier == expected,
            f"{score.overall_score:.2f} -> {score.tier}", expected
        ))
    return results


def validate_repeatability(df: pd.DataFrame, repeats: int = 3) -> list[ValidationResult]:
    results = []
    for _, row in df.iterrows():
        record = row.to_dict()
        scores = [score_supplier(record).overall_score for _ in range(repeats)]
        results.append(ValidationResult(
            f"Repeatability: {record['supplier_id']}", len(set(scores)) == 1,
            str(scores), "identical scores"
        ))
    return results


def sensitivity_cases(base: dict) -> list[tuple[str, str, object, object, str]]:
    return [
        ("MFA absent increases risk", "mfa_enabled", "yes", "no", "increase"),
        ("Longer patch SLA increases risk", "patch_sla_days", 7, 90, "increase"),
        ("Privileged access increases risk", "system_access_level", "none", "privileged", "increase"),
        ("ERP/API connection increases risk", "erp_api_connected", "no", "yes", "increase"),
        ("Sole source increases risk", "sole_source", "no", "yes", "increase"),
        ("Long lead time increases risk", "lead_time_days", 10, 90, "increase"),
        ("No alternate source increases risk", "alternate_source_status", "available", "none", "increase"),
        ("Low inventory increases risk", "inventory_buffer_days", 75, 5, "increase"),
        ("Missing documentation increases risk", "security_documentation_status", "current", "missing", "increase"),
        ("No security clause increases risk", "security_clause_contract", "yes", "no", "increase"),
    ]


def validate_sensitivity(base: dict) -> list[ValidationResult]:
    results = []
    for name, field, low_value, high_value, direction in sensitivity_cases(base):
        low = copy.deepcopy(base); high = copy.deepcopy(base)
        low[field] = low_value; high[field] = high_value
        low_score = score_supplier(low).overall_score
        high_score = score_supplier(high).overall_score
        passed = high_score > low_score if direction == "increase" else high_score < low_score
        results.append(ValidationResult(name, passed, f"{low_score:.2f} -> {high_score:.2f}", direction))
    return results


def validate_rag() -> list[ValidationResult]:
    retriever = LocalTfidfRetriever()
    cases = [
        ("MFA", "supplier remote access MFA requirement", ["mfa", "multi-factor", "remote access"]),
        ("Backups", "supplier ransomware backup recovery testing", ["backup", "recovery", "restore"]),
        ("Incident", "supplier incident breach notification", ["incident", "notification"]),
        ("Encryption", "sensitive supplier data encryption", ["encrypt", "encryption"]),
        ("Sole source", "critical sole-source supplier business continuity alternate sourcing", ["sole-source", "alternate", "continuity"]),
        ("Fourth party", "supplier subcontractor fourth-party dependency visibility", ["fourth-party", "subcontractor", "dependency"]),
    ]
    results = []
    for name, query, expected_terms in cases:
        hits = retriever.query(query, k=3)
        combined = " ".join(h.text.lower() for h in hits)
        passed = any(term.lower() in combined for term in expected_terms)
        results.append(ValidationResult(
            f"RAG relevance: {name}", passed,
            "; ".join(f"{h.source}:{h.section}" for h in hits),
            f"one of {expected_terms} in top-3"
        ))
    return results
