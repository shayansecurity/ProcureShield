# 3-Minute Live Demo Script

## 0:00–0:30 — What changed
“Since my last report I moved from organizing the architecture into a working prototype. The core scoring logic, synthetic supplier scenarios, evidence retrieval, validation checks, and dashboard workflow are now implemented.”

## 0:30–1:10 — Show the score
Select `Critical Scenario Supplier 1`.

“The score is deterministic. This supplier is 86.8 out of 100 and Critical because several controls and business dependencies are severe. The AI does not calculate this score.”

Point to the five domain bars and top drivers.

## 1:10–1:45 — Prove sensitivity
Open the input editor and change one risk factor, preferably MFA `no → yes` or sole source `yes → no`. Run the assessment again.

“This is one of the ways I validate the model. I change one input while keeping the others fixed and verify that the score moves in the expected direction.”

## 1:45–2:15 — Evidence and AI
Open Evidence + AI Brief.

“The next layer retrieves guidance related to the major findings. The generated narrative receives the deterministic score and retrieved evidence, but it is instructed not to override the score or invent missing controls.”

## 2:15–2:45 — Validation
Open Validation and run the suite.

“The current controlled dataset has 16 suppliers across four expected tiers. All 16 currently classify into their expected tier. The repeated scoring checks are deterministic, all 10 sensitivity checks move in the expected direction, and six curated offline RAG cases retrieve relevant evidence. These validate the core prototype; I still need to complete the separate manual evaluation of live AI-generated briefs.”

## 2:45–3:00 — Next step
“My next step is to run the full ChromaDB and OpenAI path with my API key, manually grade those AI briefs for supported versus unsupported statements, and then refine the scoring model based on the documented results.”
