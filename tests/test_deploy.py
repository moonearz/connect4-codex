from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


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
