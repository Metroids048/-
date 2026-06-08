from pathlib import Path

from app.services.alpha_adapter import clear_alpha_summary_cache, get_alpha_dir, load_alpha_summary


def test_get_alpha_dir_uses_env_override(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("ALPHA_DATA_DIR", str(tmp_path))
    clear_alpha_summary_cache()
    assert get_alpha_dir() == tmp_path


def test_load_alpha_summary_gracefully_degrades_when_dir_empty(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("ALPHA_DATA_DIR", str(tmp_path))
    clear_alpha_summary_cache()
    summary = load_alpha_summary()

    assert summary["available"] is False
    assert summary["feedback_rows"] == 0
    assert summary["asset_metrics"]["scanned_factors"] == 0
    assert summary["asset_metrics"]["factor_families"] == 0
