"""Tests for the command-line interface."""

import json

from auto_fio.cli import main


def test_cli_table(tmp_path, capsys):
    rc = main([str(tmp_path), "--backend", "python", "--file-size", str(2 << 20)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Optimal block size:" in out


def test_cli_json(tmp_path, capsys):
    rc = main(
        [str(tmp_path), "--backend", "python", "--file-size", str(2 << 20), "--json"]
    )
    assert rc == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["optimal_block_size"] > 0
    assert data["backend"] == "python"
    assert len(data["samples"]) >= 1
    # Explicit --backend python must not emit the fio nag, and stdout (the JSON)
    # must stay clean regardless.
    assert "fio not found" not in captured.err


def test_cli_suggests_fio_on_auto_fallback(tmp_path, capsys, monkeypatch):
    # Force the auto backend to fall back to python by hiding fio.
    monkeypatch.setattr("auto_fio.backends.FioBackend.available", lambda self: False)
    rc = main(
        [str(tmp_path), "--backend", "auto", "--file-size", str(2 << 20), "--json"]
    )
    assert rc == 0
    captured = capsys.readouterr()
    # Suggestion goes to stderr; stdout stays valid JSON.
    assert "fio not found" in captured.err
    assert json.loads(captured.out)["backend"] == "python"
