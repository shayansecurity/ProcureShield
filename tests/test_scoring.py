import pandas as pd
from app.config import DATA_PATH
from app.scoring import score_supplier
from app.validation import validate_expected_tiers, validate_repeatability, validate_sensitivity


def test_all_scenarios_hit_expected_tier():
    df = pd.read_csv(DATA_PATH)
    assert all(x.passed for x in validate_expected_tiers(df))


def test_score_is_repeatable():
    df = pd.read_csv(DATA_PATH)
    assert all(x.passed for x in validate_repeatability(df, repeats=3))


def test_sensitivity_direction():
    df = pd.read_csv(DATA_PATH)
    assert all(x.passed for x in validate_sensitivity(df.iloc[0].to_dict()))


def test_score_range():
    df = pd.read_csv(DATA_PATH)
    for _, row in df.iterrows():
        result = score_supplier(row.to_dict())
        assert 0 <= result.overall_score <= 100
