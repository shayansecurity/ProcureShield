from app.rag import LocalTfidfRetriever
from app.validation import validate_rag


def test_local_retriever_returns_evidence():
    r = LocalTfidfRetriever()
    hits = r.query("MFA remote supplier access", k=3)
    assert hits
    assert any("mfa" in h.text.lower() or "multi-factor" in h.text.lower() for h in hits)


def test_curated_rag_validation_cases():
    assert all(x.passed for x in validate_rag())
