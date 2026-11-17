# ProcureShield — Step-by-Step Implementation Guide

This guide is written so you can move from the provided project folder to a live demonstration without rewriting the system.

## 0. What you already have
The package contains the scoring engine, synthetic dataset, knowledge base, Streamlit dashboard code, SQLite storage, offline RAG fallback, OpenAI/Chroma integration, n8n workflow, Docker files, validation scripts, and tests.

The correct architecture is:

`Supplier record → validate inputs → deterministic score → domain breakdown / risk drivers → RAG evidence → AI explanation → dashboard → optional High/Critical automation`

The language model never calculates the numeric score.

---

## 1. Put the project in a normal local folder
Unzip `ProcureShield_Graduate_Project.zip` somewhere easy to reach.

Windows example:
`C:\Users\<you>\Documents\ProcureShield_Graduate_Project`

Do not run the project from inside the ZIP file.

---

## 2. Open a terminal in the project folder
In Windows File Explorer, open the folder, click the address bar, type `powershell`, and press Enter.

Check Python:

```powershell
py --version
```

Python 3.11 or 3.12 is recommended.

---

## 3. Create a virtual environment
Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation for the current session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

macOS/Linux equivalent:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

You should now see `(.venv)` at the beginning of your terminal prompt.

---

## 4. Install the project dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

This installs Streamlit, Pandas, Plotly, PyYAML, scikit-learn, OpenAI, ChromaDB, dotenv, requests, and pytest.

---

## 5. Prove the core project works before touching AI
Run the automated tests:

```powershell
pytest -q
```

Expected result from the provided package:

`8 passed`

Then run the validation suite:

```powershell
python scripts/run_validation.py
```

The supplied synthetic validation set currently produces:
- 16/16 expected-tier checks passed.
- 16/16 repeatability scenario checks passed, representing 48 repeated scoring executions.
- 10/10 sensitivity tests passed.
- 6/6 curated offline RAG relevance tests passed.

These numbers validate the deterministic core and offline retriever. They are not a claim that the OpenAI output has already been validated.

---

## 6. Run the command-line demo

```powershell
python scripts/cli_demo.py
```

This selects a Critical synthetic supplier and shows:
- overall score and tier;
- top risk drivers;
- retrieved evidence;
- evidence-grounded risk brief.

Without an API key, the brief uses the safe local fallback. That is intentional so you always have a working demo.

---

## 7. Launch the Streamlit dashboard

```powershell
streamlit run streamlit_app.py
```

Streamlit should open a browser automatically. If it does not, open the localhost URL printed in the terminal, normally port 8501.

### What to demonstrate
1. Select `Critical Scenario Supplier 1`.
2. Show its deterministic score and five domain scores.
3. Show the top risk drivers.
4. Open **Edit supplier inputs for a what-if assessment**.
5. Change MFA from `no` to `yes`, or change sole source from `yes` to `no`.
6. Click **Run assessment**.
7. Show that the score changes in the expected direction.
8. Open **Evidence + AI Brief** and show the retrieved guidance.
9. Save the assessment and show it in **Assessment History**.
10. Open **Validation**, click **Run validation suite**, and show the reproducible checks.

This is your best live demonstration because it proves the project is more than a static dashboard.

---

## 8. Load your own supplier CSV
The sidebar has an optional CSV uploader.

Use `data/supplier_upload_template.csv` as the column template. Copy the row, create additional synthetic suppliers, and upload the CSV. Do not use confidential employer/vendor data without permission.

---

## 9. Enable the OpenAI risk-brief layer
The current OpenAI integration uses the Responses API. The app still works without it.

Copy the environment template:

```powershell
Copy-Item .env.example .env
```

Open `.env` and add your key:

```text
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-6-luna
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
PREFER_CHROMA=true
```

Keep `.env` private. It is already excluded by `.gitignore`.

Restart Streamlit after editing `.env`.

When the API call succeeds, the dashboard's generation mode will show an OpenAI model instead of local fallback.

If your account does not expose the default model name, replace `OPENAI_MODEL` with a text model available to your API project.

---

## 10. Enable the ChromaDB RAG path
ChromaDB is already included in `requirements.txt` and `app/rag.py`.

When all three are true:
1. `chromadb` is installed;
2. `OPENAI_API_KEY` exists;
3. `PREFER_CHROMA` is enabled in practice through the dashboard toggle;

the retriever will:
- read the markdown files in `knowledge_base/`;
- split them into sections;
- generate embeddings;
- upsert the chunks into a persistent Chroma collection under `data/chroma/`;
- embed the risk query;
- retrieve the most similar evidence.

If any part of that fails, the app automatically falls back to local TF-IDF retrieval so the demonstration still runs.

On the Evidence tab, confirm the backend says `chroma-openai` when the full RAG path is working.

---

## 11. Validate the OpenAI responses instead of assuming they are correct
After the API is enabled, run:

```powershell
python scripts/export_ai_eval_set.py
```

This creates:

`outputs/ai_evaluation_set.csv`

For each generated brief, compare it against:
1. the supplier record;
2. the deterministic score and risk drivers;
3. the retrieved evidence.

Fill in the review columns:
- Supported
- Partially Supported
- Unsupported
- Incorrect
- Reviewer Notes

This creates the actual AI-validation numbers you can use in your final report. Do not invent a percentage before reviewing these outputs.

---

## 12. SQLite assessment history
The dashboard's **Save assessment** button stores the assessment in:

`data/procureshield.db`

The record includes the supplier, timestamp, score, risk tier, domain scores, top drivers, evidence, brief, and scoring-model version.

This supports traceability and repeatability.

To initialize the database manually:

```powershell
python scripts/init_db.py
```

---

## 13. Connect the optional n8n workflow
The file is:

`n8n/high_risk_followup_workflow.json`

In n8n:
1. Create or open your n8n workspace.
2. Import the JSON workflow.
3. Open the Webhook node.
4. Copy its production webhook URL.
5. Add the URL to `.env`:

```text
N8N_WEBHOOK_URL=https://your-n8n-host/webhook/procureshield-risk
```

6. Add your desired action after **Build Follow-up Payload**. For the class demo, a Gmail/SMTP node is sufficient. A real enterprise implementation could create a ticket or GRC remediation task.
7. Activate the workflow.
8. Restart Streamlit.
9. Assess a High or Critical supplier.
10. Click **Trigger High/Critical follow-up**.

Do not make n8n a dependency for the core project. It is an automation extension after the risk result exists.

---

## 14. Docker is optional, but the package supports it
After Docker Desktop is installed:

```powershell
Copy-Item .env.example .env
# edit .env if needed
docker compose up --build
```

Then open the Streamlit address on port 8501.

Docker demonstrates reproducibility, but it is not required for your scoring/dashboard/testing deliverable.

---

## 15. Put the project under Git version control
Inside the project folder:

```powershell
git init
git add .
git commit -m "Build ProcureShield graduate project prototype"
```

Then create a private or public GitHub repository and follow GitHub's push instructions. Never commit `.env` or real supplier information.

Useful later commits:
- `Add deterministic supplier scoring model`
- `Add Streamlit dashboard and SQLite history`
- `Add RAG evidence retrieval`
- `Add AI response validation set`
- `Add n8n high-risk follow-up`

---

## 16. What to show at the progress presentation
You can honestly say the following once you have completed Steps 1–7 locally:

> Since my last report, I moved from requirements/design into a working prototype. The deterministic scoring engine now evaluates five risk domains, the dashboard can select or load synthetic suppliers, the system identifies risk drivers and retrieves supporting evidence, and assessments can be stored in SQLite. I also created a reproducible validation suite. The current synthetic set has 16 supplier scenarios across four tiers; all 16 land in the expected tier, repeated scoring is deterministic, 10 sensitivity checks move in the expected direction, and the curated offline retrieval checks return relevant guidance. My next step is completing live OpenAI/Chroma validation and manually reviewing AI briefs for unsupported or incorrect claims.

Only claim the OpenAI/Chroma part as completed after you have enabled it and verified it on your own machine.

---

## 17. Final-project testing targets
For the final submission, keep these as separate result categories:

### Deterministic score
- Expected tier accuracy across known scenarios.
- Repeatability with identical input.
- Sensitivity tests with one-factor changes.
- Boundary tests near tier thresholds.
- Missing/Not Verified input behavior.

### RAG
- Top-k evidence relevance for known findings.
- Source traceability.
- Unsupported query behavior.

### AI brief
- Supported statements.
- Partially supported statements.
- Unsupported statements.
- Incorrect/contradictory statements.
- Whether the model ever attempts to override the deterministic score.

The score, retriever, and AI should remain separately testable because each can fail for a different reason.

---

## 18. Files you will work with most
- `streamlit_app.py` — dashboard UI and workflow.
- `app/scoring.py` — deterministic risk model.
- `config/scoring.yaml` — domain weights and risk tiers.
- `data/suppliers.csv` — 16 controlled synthetic validation scenarios.
- `data/supplier_upload_template.csv` — upload format.
- `knowledge_base/*.md` — RAG evidence documents.
- `app/rag.py` — local and Chroma retrieval.
- `app/ai.py` — OpenAI risk brief and safe fallback.
- `app/database.py` — SQLite history.
- `app/validation.py` — validation cases.
- `tests/` — automated regression tests.
- `n8n/` — optional automation workflow.

---

## 19. Do not change these things casually
- Do not let the LLM calculate the score.
- Do not silently treat missing evidence as compliant.
- Do not change scoring weights without documenting the reason and rerunning tests.
- Do not use real confidential vendor records for the academic demo.
- Do not report AI accuracy until you have manually validated actual generated outputs.
