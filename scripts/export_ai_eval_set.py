from __future__ import annotations

from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from app.ai import generate_risk_brief
from app.config import DATA_PATH, ROOT
from app.rag import get_retriever, query_from_drivers
from app.scoring import score_supplier


def main() -> None:
    # Explicitly load the project .env file when running outside Streamlit.
    env_path = ROOT / ".env"
    loaded = load_dotenv(dotenv_path=env_path, override=False)

    print("=" * 65)
    print("PROCURESHIELD LIVE AI EVALUATION EXPORT")
    print("=" * 65)
    print(f"Environment file: {env_path}")
    print(f".env loaded: {loaded}")

    import os

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY was not found. "
            "The live AI evaluation cannot run in local-fallback mode."
        )

    print("OpenAI API key: detected")
    print(f"OpenAI model: {os.getenv('OPENAI_MODEL', 'gpt-6-luna')}")
    print(
        f"Embedding model: "
        f"{os.getenv('OPENAI_EMBEDDING_MODEL', 'text-embedding-3-small')}"
    )

    # Require the full Chroma/OpenAI RAG path.
    retriever = get_retriever(prefer_chroma=True)
    retriever_name = type(retriever).__name__

    print(f"Retriever: {retriever_name}")

    if retriever_name != "ChromaOpenAIRetriever":
        raise RuntimeError(
            "The export script fell back to the local TF-IDF retriever. "
            "Fix the Chroma/OpenAI configuration before generating the AI "
            "evaluation dataset."
        )

    df = pd.read_csv(DATA_PATH)

    print(f"Supplier scenarios: {len(df)}")
    print()
    print("Generating live AI briefs...")
    print()

    rows = []

    for number, (_, series) in enumerate(df.iterrows(), start=1):
        supplier = series.to_dict()
        supplier_id = str(supplier["supplier_id"])
        supplier_name = str(supplier["supplier_name"])

        print(
            f"[{number:02d}/{len(df):02d}] "
            f"{supplier_id} - {supplier_name}"
        )

        score = score_supplier(supplier).to_dict()

        query = query_from_drivers(score["top_drivers"])

        evidence_objects = retriever.query(query, k=4)
        evidence = [item.to_dict() for item in evidence_objects]

        evidence_backends = sorted(
            {str(item.get("backend", "")) for item in evidence}
        )

        if "chroma-openai" not in evidence_backends:
            raise RuntimeError(
                f"{supplier_id}: expected Chroma/OpenAI evidence, "
                f"but received backends: {evidence_backends}"
            )

        brief, mode = generate_risk_brief(
            supplier,
            score,
            evidence,
        )

        print(
            f"    Score: {score['overall_score']} "
            f"| Tier: {score['tier']} "
            f"| Generation: {mode}"
        )

        if not mode.startswith("openai:"):
            raise RuntimeError(
                f"{supplier_id}: OpenAI generation failed. "
                f"Received generation mode: {mode}. "
                "The evaluation export has been stopped so local fallback "
                "results are not mixed into the live AI dataset."
            )

        rows.append(
            {
                "supplier_id": supplier_id,
                "supplier_name": supplier_name,
                "expected_tier": supplier.get("expected_tier", ""),
                "score": score["overall_score"],
                "calculated_tier": score["tier"],
                "retrieval_backend": "chroma-openai",
                "generation_mode": mode,
                "brief": brief,
                "evidence_sources": " | ".join(
                    sorted(
                        {
                            item["source"]
                            for item in evidence
                            if item.get("source")
                        }
                    )
                ),
                "supported": "",
                "partially_supported": "",
                "unsupported": "",
                "incorrect": "",
                "reviewer_notes": "",
            }
        )

    output_dir = ROOT / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    out = output_dir / "ai_evaluation_set.csv"

    pd.DataFrame(rows).to_csv(out, index=False)

    print()
    print("=" * 65)
    print("LIVE AI EXPORT COMPLETE")
    print("=" * 65)
    print(f"Rows written: {len(rows)}")
    print(f"Retrieval backend: chroma-openai")
    print(
        f"Generation mode: "
        f"{rows[0]['generation_mode'] if rows else 'N/A'}"
    )
    print(f"Output file: {out}")
    print()
    print(
        "Next step: manually review each brief against the supplier "
        "record, deterministic score, risk drivers, and retrieved evidence."
    )


if __name__ == "__main__":
    main()
