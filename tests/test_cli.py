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
    data = json.loads(capsys.readouterr().out)
    assert data["optimal_block_size"] > 0
    assert data["backend"] == "python"
    assert len(data["samples"]) >= 1
