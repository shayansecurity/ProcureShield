# ProcureShield Project Status

## Working now
- Deterministic five-domain supplier risk scoring engine.
- 16 synthetic supplier scenarios: 4 Low, 4 Medium, 4 High, 4 Critical.
- Scenario editing / what-if analysis logic.
- Offline evidence retrieval using TF-IDF so the demo can run without an API key.
- SQLite assessment persistence.
- Evidence-grounded local fallback risk brief.
- Validation suite and automated pytest tests.
- Streamlit dashboard code with supplier selection, CSV upload, risk breakdown, evidence, brief, validation tab, and history tab.
- Optional OpenAI Responses API integration for risk briefs.
- Optional ChromaDB + OpenAI embeddings RAG path.
- Optional n8n High/Critical webhook workflow.
- Optional Docker deployment.

## Verified in the build environment
- 8 automated tests pass.
- 16/16 predefined suppliers land in their expected risk tier.
- 48 scoring executions (16 suppliers × 3 repeated runs) are deterministic within each scenario.
- 10/10 one-factor sensitivity checks move risk in the expected direction.
- 6/6 curated offline RAG relevance checks return relevant evidence in the top 3 results.

## Still to validate on the student's machine
- Live Streamlit rendering after dependencies are installed.
- Live OpenAI-generated risk briefs using the student's API key.
- ChromaDB persistent vector retrieval using the configured embeddings model.
- n8n webhook/email or ticket action after the workflow is imported and activated.
- Manual AI-response evaluation for unsupported or incorrect claims.
