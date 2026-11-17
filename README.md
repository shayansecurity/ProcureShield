# ProcureShield

**AI-assisted supplier cyber risk and operational resilience assessment.**

ProcureShield is a graduate cybersecurity portfolio project that turns supplier control and operational dependency data into an auditable risk assessment. A Streamlit dashboard presents risk drivers, supporting evidence, recommended remediation, and assessment history.

## What it demonstrates

- **Deterministic scoring:** configurable rules produce an overall score, domain scores, and Low / Medium / High / Critical tiers with traceable findings.
- **Operational resilience:** supplier criticality, sourcing alternatives, inventory buffers, logistics concentration, and lead times inform the assessment.
- **Evidence retrieval:** local policy documents support risk explanations, with offline retrieval and optional Chroma integration.
- **AI-assisted briefs:** optional OpenAI integration explains the authoritative score; a local fallback works without an API key.
- **Persistence and automation:** SQLite stores assessment history; an optional n8n webhook prepares High / Critical risk follow-up payloads.
- **Validation:** automated tests and scenario checks cover scoring, repeatability, sensitivity, retrieval, persistence, and fallback behavior.

The numeric score is calculated by rules. AI provides explanatory decision support and does not control the score.

## Run locally

Use Python 3.12. From the repository root:

```bash
python -m venv .venv
```

Activate the environment on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Or on macOS / Linux:

```bash
source .venv/bin/activate
```

Install dependencies and launch:

```bash
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```

Open the local URL printed by Streamlit. The included supplier CSV provides demonstration scenarios. The local brief fallback requires no external credentials.

For optional integrations, copy `.env.example` to `.env`, provide your own credentials, and select an OpenAI model available to your account. Keep `.env` private. The n8n sample builds a follow-up payload; downstream ticketing or notification actions require configuration.

## Verify

Run from the repository root:

```bash
python -m pytest -q
python -m scripts.run_validation
```

The validation command writes `outputs/validation_summary.json`. Test results apply to the included scenarios; they do not establish production accuracy or validate live AI-generated briefs.

## Project structure

| Path | Purpose |
| --- | --- |
| `streamlit_app.py` | Interactive assessment dashboard |
| `app/scoring.py` | Deterministic scoring and risk findings |
| `config/scoring.yaml` | Scoring configuration |
| `app/rag.py`, `knowledge_base/` | Retrieval and supporting policy evidence |
| `app/ai.py` | AI briefs and local fallback |
| `app/database.py` | SQLite assessment persistence |
| `app/automation.py`, `n8n/` | Optional remediation workflow integration |
| `data/` | Supplier scenarios and upload template |
| `tests/`, `app/validation.py` | Automated checks and scenario validation |

See [Demo script](DEMO_SCRIPT.md) and [Implementation guide](IMPLEMENTATION_GUIDE.md) for additional walkthroughs and integration details.

## Scope

This is an educational prototype using demonstration supplier records and local policy material. It supports analyst review and does not replace a supplier audit or certify compliance. Live AI behavior and external workflow delivery require separate evaluation.

## Resume description

Built a Python and Streamlit supplier cyber risk platform combining deterministic scoring, operational resilience analysis, evidence retrieval, AI-assisted risk briefs, SQLite assessment history, and optional n8n remediation automation.
