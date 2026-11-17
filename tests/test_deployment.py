import argparse
import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RENDER = runpy.run_path(str(ROOT / "scripts/render_caddy.py"))


def test_routes_require_distinct_valid_ports_and_preserve_tictactoe_paths():
    text = RENDER["render"](8123, 8124, 8125, "/srv/example/projects")
    assert "{{" not in text
    assert "127.0.0.1:8123" in text
    assert "127.0.0.1:8124" in text
    assert "127.0.0.1:8125" in text
    assert "handle /tictactoe/*" in text
    assert "handle_path /tictactoe/*" not in text
    assert "header_up X-Forwarded-Prefix /connect4" in text
    with pytest.raises(ValueError):
        RENDER["render"](8123, 8123, 8125, "/srv/example/projects")


@pytest.mark.parametrize("value", ["0", "65536", "abc", "8123; bad", "-1"])
def test_invalid_port_cannot_be_rendered(value):
    with pytest.raises(argparse.ArgumentTypeError):
        RENDER["port"](value)


def test_web_root_is_required_and_quoted():
    text = RENDER["render"](8123, 8124, 8125, "/srv/example/project files")
    assert 'root * "/srv/example/project files"' in text
    with pytest.raises(TypeError):
        RENDER["render"](8123, 8124, 8125)


@pytest.mark.parametrize(
    "value", ["relative/path", "/srv/site\nfile_server", "/srv/{value}"]
)
def test_invalid_web_root_is_rejected(value):
    with pytest.raises(argparse.ArgumentTypeError):
        RENDER["render"](8123, 8124, 8125, value)


def test_cli_has_no_site_specific_defaults(tmp_path):
    import subprocess
    import sys

    output = tmp_path / "routes"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/render_caddy.py"),
            "--tictactoe-port",
            "8123",
            "--output",
            str(output),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert not output.exists()
    for option in ("--wordle-port", "--connect4-port", "--web-root"):
        assert option in result.stderr


def test_deploy_requires_explicit_port_before_running_commands():
    import os
    import subprocess

    env = dict(os.environ)
    env.pop("HOST_PORT", None)
    result = subprocess.run(
        ["bash", str(ROOT / "deploy.sh")], env=env, capture_output=True, text=True
    )
    assert result.returncode != 0
    assert "Set HOST_PORT explicitly" in result.stderr
