from __future__ import annotations

import pandas as pd
from app.config import DATA_PATH
from app.scoring import score_supplier
from app.rag import get_retriever, query_from_drivers
from app.ai import generate_risk_brief

if __name__ == "__main__":
    df = pd.read_csv(DATA_PATH)
    supplier = df[df["expected_tier"] == "Critical"].iloc[0].to_dict()
    score = score_supplier(supplier).to_dict()
    retriever = get_retriever(prefer_chroma=True)
    evidence = [e.to_dict() for e in retriever.query(query_from_drivers(score["top_drivers"]), k=4)]
    brief, mode = generate_risk_brief(supplier, score, evidence)
    print(f"SUPPLIER: {supplier['supplier_name']}")
    print(f"SCORE: {score['overall_score']} / 100 ({score['tier']})")
    print("TOP DRIVERS:")
    for d in score["top_drivers"][:5]:
        print(f"  - {d['label']}: {d['risk_points']}/100")
    print("EVIDENCE:")
    for e in evidence:
        print(f"  - {e['source']} / {e['section']} [{e['score']:.3f}]")
    print(f"BRIEF MODE: {mode}\n{brief}")
