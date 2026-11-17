from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Callable

from .config import load_scoring_config

CFG = load_scoring_config()
UNKNOWN = float(CFG.get("unknown_risk_default", 60))


@dataclass(frozen=True)
class Finding:
    domain: str
    factor: str
    label: str
    input_value: Any
    risk_points: float
    rationale: str
    recommendation: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ScoreResult:
    overall_score: float
    tier: str
    domain_scores: dict[str, float]
    findings: list[Finding]
    top_drivers: list[Finding]
    model_name: str
    model_version: str

    def to_dict(self) -> dict:
        return {
            "overall_score": self.overall_score,
            "tier": self.tier,
            "domain_scores": self.domain_scores,
            "findings": [f.to_dict() for f in self.findings],
            "top_drivers": [f.to_dict() for f in self.top_drivers],
            "model_name": self.model_name,
            "model_version": self.model_version,
        }


def _norm(value: Any) -> str:
    if value is None:
        return "unknown"
    text = str(value).strip().lower()
    if text in {"", "nan", "null", "n/a", "na", "unknown", "not verified"}:
        return "unknown"
    return text


def _bool_risk(value: Any, yes_risk: float, no_risk: float = 0, unknown: float = UNKNOWN) -> float:
    v = _norm(value)
    if v in {"yes", "true", "1", "y"}:
        return yes_risk
    if v in {"no", "false", "0", "n"}:
        return no_risk
    return unknown


def _inverse_bool_risk(value: Any, yes_risk: float = 0, no_risk: float = 100, unknown: float = UNKNOWN) -> float:
    return _bool_risk(value, yes_risk=yes_risk, no_risk=no_risk, unknown=unknown)


def _num(value: Any) -> float | None:
    try:
        if _norm(value) == "unknown":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _cat(value: Any, mapping: dict[str, float], unknown: float = UNKNOWN) -> float:
    return float(mapping.get(_norm(value), unknown))


def tier_for(score: float) -> str:
    for tier, bounds in CFG["tiers"].items():
        lo, hi = float(bounds[0]), float(bounds[1])
        if lo <= score <= hi:
            return tier
    return "Critical" if score > 100 else "Low"


def _patch_risk(days: Any) -> float:
    d = _num(days)
    if d is None:
        return UNKNOWN
    if d <= 7: return 0
    if d <= 30: return 25
    if d <= 60: return 60
    return 100


def _lead_time_risk(days: Any) -> float:
    d = _num(days)
    if d is None: return UNKNOWN
    if d <= 14: return 10
    if d <= 30: return 30
    if d <= 60: return 65
    return 95


def _inventory_risk(days: Any) -> float:
    d = _num(days)
    if d is None: return UNKNOWN
    if d >= 60: return 0
    if d >= 30: return 20
    if d >= 14: return 50
    return 90


def _sku_risk(count: Any) -> float:
    n = _num(count)
    if n is None: return UNKNOWN
    if n <= 10: return 10
    if n <= 50: return 30
    if n <= 150: return 60
    return 90


def _breach_notice_risk(hours: Any) -> float:
    h = _num(hours)
    if h is None: return UNKNOWN
    if h <= 24: return 0
    if h <= 72: return 30
    if h <= 168: return 70
    return 100


def _factor_specs() -> list[tuple[str, str, str, Callable[[Any], float], str, str]]:
    return [
        ("security_controls", "mfa_enabled", "Multi-factor authentication", lambda v: _inverse_bool_risk(v),
         "MFA reduces the likelihood that compromised credentials alone lead to supplier-account compromise.",
         "Require MFA for supplier and privileged access; document enforcement evidence."),
        ("security_controls", "patch_sla_days", "Patch remediation SLA", _patch_risk,
         "Longer patch windows increase the period in which known vulnerabilities may remain exploitable.",
         "Define and verify remediation SLAs based on severity and exposure."),
        ("security_controls", "encryption_status", "Encryption coverage", lambda v: _cat(v, {"full":0,"partial":45,"none":100}),
         "Encryption helps reduce confidentiality impact if data or systems are exposed.",
         "Require encryption in transit and at rest for sensitive data where applicable."),
        ("security_controls", "backup_recovery", "Backup & recovery maturity", lambda v: _cat(v, {"tested":0,"exists_not_tested":45,"none":100}),
         "Backups that are not tested may not provide reliable recovery during ransomware or outage events.",
         "Require tested recovery procedures and evidence of recent restore exercises."),
        ("security_controls", "incident_response_plan", "Incident response plan", lambda v: _inverse_bool_risk(v),
         "A documented incident response process supports coordinated containment and notification.",
         "Require a documented incident response plan and named escalation contacts."),

        ("system_data_exposure", "system_access_level", "System access level", lambda v: _cat(v, {"none":0,"limited":25,"standard":55,"privileged":100}),
         "Higher supplier access privileges increase the potential impact of account or vendor compromise.",
         "Apply least privilege, time-bounded access, and periodic access recertification."),
        ("system_data_exposure", "data_sensitivity", "Data sensitivity", lambda v: _cat(v, {"public":0,"internal":30,"confidential":65,"regulated":100}),
         "More sensitive data increases the consequence of unauthorized disclosure or misuse.",
         "Limit supplier data access to the minimum required and verify handling requirements."),
        ("system_data_exposure", "erp_api_connected", "ERP/API connectivity", lambda v: _bool_risk(v, 80, 0),
         "Direct ERP or API connectivity increases technical dependency and attack surface.",
         "Inventory integration points, use strong authentication, and monitor supplier-connected interfaces."),
        ("system_data_exposure", "remote_access", "Remote access", lambda v: _bool_risk(v, 55, 0),
         "Remote access creates an additional path into organizational systems.",
         "Restrict remote access through approved secure methods and MFA."),

        ("business_criticality", "supplier_criticality", "Supplier criticality", lambda v: _cat(v, {"low":10,"medium":40,"high":75,"critical":100}),
         "Critical suppliers can create material business impact when disrupted.",
         "Prioritize due diligence, monitoring, and continuity planning for critical suppliers."),
        ("business_criticality", "sole_source", "Sole-source dependency", lambda v: _bool_risk(v, 100, 0),
         "Sole-source dependency reduces recovery options when a supplier is disrupted.",
         "Develop alternate-source or contingency options for critical sole-source suppliers."),
        ("business_criticality", "active_skus", "Active SKU dependency", _sku_risk,
         "A larger dependent SKU footprint can amplify the operational impact of supplier disruption.",
         "Identify critical SKUs and prioritize contingency planning for concentrated supplier exposure."),
        ("business_criticality", "process_dependency", "Business process dependency", lambda v: _cat(v, {"low":10,"medium":40,"high":75,"critical":100}),
         "High process dependency increases business interruption impact.",
         "Map dependent business processes and define recovery priorities."),

        ("operational_resilience", "lead_time_days", "Lead time", _lead_time_risk,
         "Long lead times reduce the speed at which disrupted supply can be replenished.",
         "Maintain contingency stock or alternate supply strategies for long-lead critical items."),
        ("operational_resilience", "alternate_source_status", "Alternate-source availability", lambda v: _cat(v, {"available":0,"partial":50,"none":100}),
         "Limited alternate sourcing increases recovery time following supplier disruption.",
         "Qualify alternate suppliers or document a substitution/recovery plan."),
        ("operational_resilience", "logistics_concentration", "Logistics concentration", lambda v: _cat(v, {"low":10,"medium":40,"high":75,"critical":100}),
         "Concentrated lanes, ports, carriers, or regions increase common-mode disruption risk.",
         "Identify alternate lanes, carriers, or routing options for critical flows."),
        ("operational_resilience", "inventory_buffer_days", "Inventory buffer", _inventory_risk,
         "Low inventory buffer reduces the time available to recover from supply interruption.",
         "Set resilience inventory targets based on lead time and supplier criticality."),
        ("operational_resilience", "international_freight_dependency", "International freight dependency", lambda v: _bool_risk(v, 60, 10),
         "International freight can add lead-time, port, geopolitical, and carrier dependencies.",
         "Document alternate transport modes and critical-lane contingencies."),

        ("third_fourth_party", "security_documentation_status", "Security documentation", lambda v: _cat(v, {"current":0,"partial":40,"outdated":70,"missing":100}),
         "Missing or outdated evidence limits confidence in the supplier's security posture.",
         "Request current security documentation and track evidence expiration dates."),
        ("third_fourth_party", "breach_notification_hours", "Breach notification requirement", _breach_notice_risk,
         "Slow or undefined breach notification can delay containment and stakeholder response.",
         "Define contractual incident notification requirements and escalation contacts."),
        ("third_fourth_party", "fourth_party_visibility", "Fourth-party visibility", lambda v: _cat(v, {"high":10,"medium":40,"low":75,"none":100}),
         "Low downstream visibility can hide concentrated or inherited supplier dependencies.",
         "Require disclosure or oversight of material subcontractors and critical service dependencies."),
        ("third_fourth_party", "security_clause_contract", "Security clauses in contract", lambda v: _cat(v, {"yes":0,"partial":40,"no":100}),
         "Security obligations are harder to enforce when contract requirements are incomplete or absent.",
         "Include security, incident, access, evidence, and termination requirements in supplier agreements."),
    ]


def score_supplier(record: dict[str, Any]) -> ScoreResult:
    domain_points: dict[str, list[float]] = {k: [] for k in CFG["domains"]}
    findings: list[Finding] = []
    for domain, factor, label, fn, rationale, recommendation in _factor_specs():
        raw = record.get(factor)
        points = float(max(0, min(100, fn(raw))))
        domain_points[domain].append(points)
        findings.append(Finding(domain, factor, label, raw, round(points, 2), rationale, recommendation))

    domain_scores = {
        domain: round(sum(values) / len(values), 2) if values else 0.0
        for domain, values in domain_points.items()
    }
    overall = 0.0
    for domain, meta in CFG["domains"].items():
        overall += domain_scores[domain] * float(meta["weight"])
    overall = round(overall, 2)
    tier = tier_for(overall)
    top = sorted(findings, key=lambda f: f.risk_points, reverse=True)[:6]
    return ScoreResult(
        overall_score=overall,
        tier=tier,
        domain_scores=domain_scores,
        findings=findings,
        top_drivers=top,
        model_name=CFG["model_name"],
        model_version=str(CFG["version"]),
    )
