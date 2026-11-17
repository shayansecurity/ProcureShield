from pathlib import Path
from app.database import init_db, save_assessment, list_assessments


def test_sqlite_roundtrip(tmp_path: Path):
    db = tmp_path / "test.db"
    init_db(db)
    supplier = {"supplier_id":"T01","supplier_name":"Test Supplier"}
    score = {"overall_score":50.0,"tier":"Medium","domain_scores":{"x":50},"top_drivers":[],"model_version":"1.0"}
    row_id = save_assessment(supplier, score, [], "brief", db)
    assert row_id == 1
    rows = list_assessments(path=db)
    assert rows[0]["supplier_name"] == "Test Supplier"
