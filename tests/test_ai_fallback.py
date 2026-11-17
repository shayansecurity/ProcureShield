from app.ai import fallback_brief


def test_fallback_uses_authoritative_score():
    supplier={"supplier_name":"Demo"}
    score={"overall_score":81.2,"tier":"Critical","top_drivers":[{"label":"MFA","risk_points":100,"recommendation":"Require MFA."}]}
    text=fallback_brief(supplier,score,[])
    assert "81.2/100" in text
    assert "Critical" in text
    assert "Require MFA" in text
