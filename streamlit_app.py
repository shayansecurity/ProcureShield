from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

from app.ai import generate_risk_brief
from app.automation import trigger_high_risk_followup
from app.config import DATA_PATH, ROOT
from app.database import list_assessments, save_assessment
from app.rag import get_retriever, query_from_drivers
from app.scoring import CFG, score_supplier
from app.validation import validate_expected_tiers, validate_repeatability, validate_sensitivity, validate_rag

load_dotenv()

st.set_page_config(
    page_title="ProcureShield | Supplier Cyber Risk",
    page_icon="",
    layout="wide",
)

st.markdown(
    """
<style>
.block-container {padding-top: 1.3rem; padding-bottom: 2.4rem; max-width: 1450px;}
[data-testid="stSidebar"] {background: #172033;}
[data-testid="stSidebar"] * {color: #F8FAFC;}
[data-testid="stSidebar"] [data-baseweb="select"] * {color:#172033 !important;}
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] * {color:#172033 !important;}
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button * {color:#172033 !important;}
.hero {background: linear-gradient(120deg,#172033,#24324d); padding: 26px 30px; border-radius: 18px; color:white; margin-bottom: 18px;}
.hero h1 {font-size: 2.1rem; margin:0 0 6px 0;}
.hero p {color:#D7DDEA; margin:0; font-size:1rem;}
.card {background:#FFFFFF; border:1px solid #E5E7EB; border-radius:16px; padding:18px; box-shadow:0 5px 20px rgba(23,32,51,.06);}
.section-label {font-size:.78rem; text-transform:uppercase; letter-spacing:.08em; color:#667085; font-weight:700;}
.risk-low {color:#1B7F5A;font-weight:800}.risk-medium {color:#9A6700;font-weight:800}.risk-high {color:#B54708;font-weight:800}.risk-critical {color:#B42318;font-weight:800}
.small-muted {color:#667085;font-size:.86rem;}
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_data
def load_suppliers() -> pd.DataFrame:
    return pd.read_csv(DATA_PATH)


@st.cache_resource
def load_retriever(prefer_chroma: bool):
    return get_retriever(prefer_chroma=prefer_chroma)


def _select(label: str, current, options: list[str], key: str):
    current = str(current).lower() if current is not None else "unknown"
    if current not in options:
        current = "unknown" if "unknown" in options else options[0]
    return st.selectbox(label, options, index=options.index(current), key=key)


def supplier_editor(base: dict, key_prefix: str) -> dict:
    """Render supplier-specific what-if controls without leaking state across suppliers."""
    r = dict(base)
    prefix = f"editor_{key_prefix}_"

    with st.expander("Edit supplier inputs for a what-if assessment", expanded=False):
        st.caption("Change one or more fields, then click **Run assessment**. This is useful for sensitivity demonstrations.")

        # Reset only the currently selected supplier's editor values back to CSV baseline.
        if st.button("Reset selected supplier to baseline", key=f"{prefix}reset"):
            for state_key in list(st.session_state.keys()):
                if state_key.startswith(prefix) and state_key != f"{prefix}reset":
                    del st.session_state[state_key]
            st.session_state.pop("assessment", None)
            st.rerun()

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("**Security controls**")
            r["mfa_enabled"] = _select("MFA enabled", r.get("mfa_enabled"), ["yes","no","unknown"], f"{prefix}mfa")
            r["patch_sla_days"] = st.number_input("Patch SLA (days)", 1, 365, int(float(r.get("patch_sla_days",30))), key=f"{prefix}patch")
            r["encryption_status"] = _select("Encryption", r.get("encryption_status"), ["full","partial","none","unknown"], f"{prefix}enc")
            r["backup_recovery"] = _select("Backup/recovery", r.get("backup_recovery"), ["tested","exists_not_tested","none","unknown"], f"{prefix}backup")
            r["incident_response_plan"] = _select("Incident response plan", r.get("incident_response_plan"), ["yes","no","unknown"], f"{prefix}ir")
            st.markdown("**System & data exposure**")
            r["system_access_level"] = _select("System access", r.get("system_access_level"), ["none","limited","standard","privileged","unknown"], f"{prefix}access")
            r["data_sensitivity"] = _select("Data sensitivity", r.get("data_sensitivity"), ["public","internal","confidential","regulated","unknown"], f"{prefix}data")
        with c2:
            st.markdown("**Business criticality**")
            r["erp_api_connected"] = _select("ERP/API connected", r.get("erp_api_connected"), ["yes","no","unknown"], f"{prefix}erp")
            r["remote_access"] = _select("Remote access", r.get("remote_access"), ["yes","no","unknown"], f"{prefix}remote")
            r["supplier_criticality"] = _select("Supplier criticality", r.get("supplier_criticality"), ["low","medium","high","critical","unknown"], f"{prefix}crit")
            r["sole_source"] = _select("Sole source", r.get("sole_source"), ["yes","no","unknown"], f"{prefix}sole")
            r["active_skus"] = st.number_input("Active SKUs", 0, 10000, int(float(r.get("active_skus",10))), key=f"{prefix}skus")
            r["process_dependency"] = _select("Process dependency", r.get("process_dependency"), ["low","medium","high","critical","unknown"], f"{prefix}process")
            st.markdown("**Operational resilience**")
            r["lead_time_days"] = st.number_input("Lead time (days)", 0, 365, int(float(r.get("lead_time_days",30))), key=f"{prefix}lead")
        with c3:
            r["alternate_source_status"] = _select("Alternate source", r.get("alternate_source_status"), ["available","partial","none","unknown"], f"{prefix}alternate")
            r["logistics_concentration"] = _select("Logistics concentration", r.get("logistics_concentration"), ["low","medium","high","critical","unknown"], f"{prefix}logistics")
            r["inventory_buffer_days"] = st.number_input("Inventory buffer (days)", 0, 365, int(float(r.get("inventory_buffer_days",30))), key=f"{prefix}buffer")
            r["international_freight_dependency"] = _select("International freight dependency", r.get("international_freight_dependency"), ["yes","no","unknown"], f"{prefix}intl")
            st.markdown("**Evidence / downstream risk**")
            r["security_documentation_status"] = _select("Security documentation", r.get("security_documentation_status"), ["current","partial","outdated","missing","unknown"], f"{prefix}docs")
            r["breach_notification_hours"] = st.number_input("Breach notification (hours)", 0, 720, int(float(r.get("breach_notification_hours",72))), key=f"{prefix}breach")
            r["fourth_party_visibility"] = _select("Fourth-party visibility", r.get("fourth_party_visibility"), ["high","medium","low","none","unknown"], f"{prefix}fourth")
            r["security_clause_contract"] = _select("Security contract clauses", r.get("security_clause_contract"), ["yes","partial","no","unknown"], f"{prefix}clause")
    return r


def run_assessment(supplier: dict, prefer_chroma: bool) -> dict:
    score = score_supplier(supplier).to_dict()
    retriever = load_retriever(prefer_chroma)
    query = query_from_drivers(score["top_drivers"][:5])
    evidence = [e.to_dict() for e in retriever.query(query, k=4)]
    brief, ai_mode = generate_risk_brief(supplier, score, evidence)
    return {"supplier": supplier, "score": score, "evidence": evidence, "brief": brief, "ai_mode": ai_mode, "prefer_chroma": prefer_chroma}


suppliers = load_suppliers()

with st.sidebar:
    st.markdown("##  ProcureShield")
    st.caption("Supplier cyber risk + operational resilience")
    uploaded = st.file_uploader("Optional supplier CSV", type=["csv"], help="Use the same columns as data/supplier_upload_template.csv.")
    active_suppliers = suppliers
    if uploaded is not None:
        try:
            candidate = pd.read_csv(uploaded)
            required = {"supplier_id", "supplier_name"}
            if not required.issubset(candidate.columns):
                st.error("Uploaded CSV must include supplier_id and supplier_name.")
            else:
                active_suppliers = candidate
                st.success(f"Loaded {len(candidate)} uploaded supplier record(s).")
        except Exception as exc:
            st.error(f"Could not read CSV: {exc}")
    options = active_suppliers.apply(lambda x: f"{x['supplier_id']} — {x['supplier_name']}", axis=1).tolist()
    chosen = st.selectbox("Supplier", options, key="supplier_choice")
    idx = options.index(chosen)
    st.caption(f"Selected: **{chosen}**")
    st.divider()
    prefer_chroma = st.toggle("Prefer ChromaDB + OpenAI embeddings", value=True, help="Falls back to local TF-IDF if dependencies or API key are unavailable.")
    st.caption("**Runtime status**")
    st.write("OpenAI API:", "configured" if os.getenv("OPENAI_API_KEY") else "local fallback")
    st.write("n8n webhook:", "configured" if os.getenv("N8N_WEBHOOK_URL") else "optional / off")
    st.divider()
    st.caption("Model version: 1.1 • Synthetic academic data")

base = active_suppliers.iloc[idx].to_dict()
selected_supplier_id = str(base.get("supplier_id", ""))

# One-time migration: old global editor keys caused values to leak between suppliers.
if not st.session_state.get("supplier_state_v2_migrated"):
    for legacy_key in [
        "mfa","patch","enc","backup","ir","access","data","erp","remote","crit",
        "sole","skus","process","lead","alternate","logistics","buffer","intl","docs",
        "breach","fourth","clause"
    ]:
        st.session_state.pop(legacy_key, None)
    st.session_state["supplier_state_v2_migrated"] = True

# Keep the displayed assessment synchronized with the sidebar selection and RAG preference.
current_assessment = st.session_state.get("assessment")
assessment_supplier_id = str((current_assessment or {}).get("supplier", {}).get("supplier_id", ""))
assessment_prefer_chroma = (current_assessment or {}).get("prefer_chroma")
if (
    current_assessment is None
    or assessment_supplier_id != selected_supplier_id
    or assessment_prefer_chroma != prefer_chroma
):
    st.session_state["assessment"] = run_assessment(base, prefer_chroma)

st.markdown(
    """<div class="hero"><div class="section-label" style="color:#E7B64A">GRADUATE PROJECT PROTOTYPE</div>
    <h1>Supplier Cyber Risk & Operational Resilience Dashboard</h1>
    <p>Deterministic scoring first. Evidence retrieval second. AI explanation last.</p></div>""",
    unsafe_allow_html=True,
)

edited = supplier_editor(base, selected_supplier_id)
if st.button("Run assessment", type="primary", width="stretch"):
    st.session_state["assessment"] = run_assessment(edited, prefer_chroma)


A = st.session_state["assessment"]
supplier = A["supplier"]
score = A["score"]

m1, m2, m3, m4 = st.columns(4)
m1.metric("Overall risk score", f"{score['overall_score']:.1f} / 100")
m2.metric("Risk tier", score["tier"])
m3.metric("Supplier criticality", str(supplier.get("supplier_criticality", "unknown")).title())
m4.metric("Assessment mode", "OpenAI" if A["ai_mode"].startswith("openai") else "Safe local fallback")

st.caption(f"Selected supplier: **{supplier.get('supplier_name')}** • Synthetic scenario • Expected test tier: {supplier.get('expected_tier')}")

tab1, tab2, tab3, tab4 = st.tabs(["Assessment", "Evidence + AI Brief", "Validation", "Assessment History"])

with tab1:
    left, right = st.columns([1.05, 1], gap="large")
    with left:
        st.subheader("Domain risk breakdown")
        rows = []
        for domain, val in score["domain_scores"].items():
            rows.append({"Domain": CFG["domains"][domain]["label"], "Risk": val, "Weight": CFG["domains"][domain]["weight"]})
        chart_df = pd.DataFrame(rows).sort_values("Risk")
        fig = px.bar(chart_df, x="Risk", y="Domain", orientation="h", text="Risk", range_x=[0,100])
        fig.update_traces(texttemplate="%{text:.0f}", textposition="outside", marker_color="#E7B64A")
        fig.update_layout(height=340, margin=dict(l=0,r=35,t=10,b=0), xaxis_title="Risk points (0–100)", yaxis_title="", plot_bgcolor="white", paper_bgcolor="white")
        st.plotly_chart(fig, width="stretch")
        st.caption("Overall score = weighted average of the five domain scores. AI does not calculate or modify this number.")
    with right:
        st.subheader("Top risk drivers")
        drivers_df = pd.DataFrame([
            {"Risk factor": d["label"], "Observed": str(d["input_value"]), "Risk points": d["risk_points"], "Domain": CFG["domains"][d["domain"]]["label"]}
            for d in score["top_drivers"]
        ])
        st.dataframe(drivers_df, hide_index=True, width="stretch", height=330)

    st.subheader("Recommended remediation")
    for n, d in enumerate(score["top_drivers"][:5], 1):
        st.markdown(f"**{n}. {d['label']}** — {d['recommendation']}")

with tab2:
    left, right = st.columns([1.05, 1], gap="large")
    with left:
        st.subheader("Retrieved evidence")
        st.caption(f"Retrieval backend: {A['evidence'][0]['backend'] if A['evidence'] else 'none'}")
        for i, e in enumerate(A["evidence"], 1):
            with st.container(border=True):
                st.markdown(f"**{i}. {e['section']}**  ")
                st.caption(f"{e['source']} • relevance {e['score']:.3f}")
                st.write(e["text"])
    with right:
        st.subheader("Evidence-grounded risk brief")
        st.info(A["brief"])
        st.caption(f"Generation mode: {A['ai_mode']}. The score remains deterministic regardless of narrative mode.")
        c1, c2 = st.columns(2)
        if c1.button("Save assessment", width="stretch"):
            row_id = save_assessment(supplier, score, A["evidence"], A["brief"])
            st.success(f"Saved assessment #{row_id} to SQLite.")
        if c2.button("Trigger High/Critical follow-up", width="stretch"):
            ok, msg = trigger_high_risk_followup(supplier, score, A["brief"])
            (st.success if ok else st.warning)(msg)

with tab3:
    st.subheader("Validation matrix")
    st.caption("These checks run against the deterministic engine and the offline evidence retriever so they can be reproduced without an API key.")
    if st.button("Run validation suite", key="validation"):
        groups = {
            "Expected tier": validate_expected_tiers(suppliers),
            "Repeatability": validate_repeatability(suppliers, repeats=3),
            "Sensitivity": validate_sensitivity(suppliers.iloc[0].to_dict()),
            "RAG relevance": validate_rag(),
        }
        st.session_state["validation_groups"] = groups
    groups = st.session_state.get("validation_groups")
    if groups:
        cols = st.columns(4)
        for col, (name, items) in zip(cols, groups.items()):
            passed = sum(x.passed for x in items)
            col.metric(name, f"{passed}/{len(items)}", f"{100*passed/len(items):.0f}%")
        details=[]
        for group, items in groups.items():
            for x in items:
                details.append({"Group":group,"Test":x.name,"Pass":x.passed,"Observed":str(x.observed),"Expected":str(x.expected)})
        st.dataframe(pd.DataFrame(details), hide_index=True, width="stretch")
    else:
        st.write("Run the suite to display reproducible validation results.")

with tab4:
    st.subheader("Saved SQLite assessments")
    history = list_assessments(limit=50)
    if history:
        hist_df = pd.DataFrame(history)[["id","supplier_name","assessed_at","overall_score","tier","model_version"]]
        st.dataframe(hist_df, hide_index=True, width="stretch")
    else:
        st.write("No saved assessments yet. Save one from the Evidence + AI Brief tab.")

st.divider()
st.caption("Academic prototype • Synthetic data • Decision support, not a production TPRM system • Numeric scoring is deterministic and independently testable")



# Final sidebar selectbox visibility cleanup.



st.markdown("""
<style>

/* FINAL_ProcureShield_SIDEBAR_SELECT_FIX */

section[data-testid="stSidebar"] div[data-baseweb="select"] > div {
    background: #ffffff !important;
    border-color: #d9dde5 !important;
}

/* Force the selected supplier text to remain visible. */
section[data-testid="stSidebar"] div[data-baseweb="select"] *,
section[data-testid="stSidebar"] div[data-baseweb="select"] input,
section[data-testid="stSidebar"] div[data-baseweb="select"] span,
section[data-testid="stSidebar"] div[data-baseweb="select"] div {
    color: #17233a !important;
    -webkit-text-fill-color: #17233a !important;
    opacity: 1 !important;
}

/* Dropdown arrow */
section[data-testid="stSidebar"] div[data-baseweb="select"] svg {
    fill: #17233a !important;
    color: #17233a !important;
}

/* Keep the sidebar brand clean and aligned. */
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] strong {
    letter-spacing: 0 !important;
}

</style>
""", unsafe_allow_html=True)


