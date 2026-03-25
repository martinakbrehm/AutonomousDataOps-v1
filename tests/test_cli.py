import sys
import pytest


def test_cli_help_exits(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["autodops", "--help"])
    with pytest.raises(SystemExit):
        import autodops.cli as cli
        cli.main()


def test_run_pipeline_missing_file(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["autodops", "run-pipeline", "nonexistent.csv"])
    with pytest.raises(SystemExit) as exc:
        import autodops.cli as cli
        cli.main()
    assert exc.value.code == 2
