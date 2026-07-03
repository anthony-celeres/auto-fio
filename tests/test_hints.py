"""Tests for the fio-install suggestion logic (pure, no I/O)."""

import pytest

from auto_fio.hints import fio_install_command, fio_missing_warning


@pytest.mark.parametrize(
    "platform, expected_snippet",
    [
        ("darwin", "brew install fio"),
        ("linux", "apt install fio"),
        ("linux2", "apt install fio"),  # legacy sys.platform value
        ("win32", "choco install fio"),
    ],
)
def test_install_command_per_platform(platform, expected_snippet):
    assert expected_snippet in fio_install_command(platform)


def test_install_command_unknown_platform_falls_back():
    assert "fio.readthedocs.io" in fio_install_command("sunos5")


def test_warning_on_auto_fallback_names_the_command():
    msg = fio_missing_warning("auto", "python", platform="darwin")
    assert msg is not None
    assert "brew install fio" in msg
    assert "--backend python" in msg  # tells the user how to silence it


def test_no_warning_when_fio_was_used():
    assert fio_missing_warning("auto", "fio") is None


def test_no_warning_when_python_was_explicit():
    # User asked for python outright — the fallback is not a surprise.
    assert fio_missing_warning("python", "python") is None
