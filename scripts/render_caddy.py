"""Render the Caddy routes with explicitly chosen local backend ports."""

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def port(value):
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Port must be an integer.") from exc
    if not 1 <= number <= 65535:
        raise argparse.ArgumentTypeError("Port must be between 1 and 65535.")
    return number


def absolute_root(value):
    if not Path(value).is_absolute() or any(ord(c) < 32 or c in "{}" for c in value):
        raise argparse.ArgumentTypeError("Web root must be an absolute literal path.")
    return value


def render(tictactoe_port, wordle_port, connect4_port, web_root):
    ports = dict(
        TICTACTOE_PORT=port(str(tictactoe_port)),
        WORDLE_PORT=port(str(wordle_port)),
        CONNECT4_PORT=port(str(connect4_port)),
    )
    if len(set(ports.values())) != 3:
        raise ValueError("Each application needs a distinct backend port.")
    text = (ROOT / "deploy/Caddy.routes.template").read_text()
    for key, value in ports.items():
        text = text.replace("{{" + key + "}}", str(value))
    return text.replace("{{WEB_ROOT}}", json.dumps(absolute_root(str(web_root))))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tictactoe-port",
        type=port,
        required=True,
        help="Actual host port from docker ps / current Caddyfile.",
    )
    parser.add_argument("--wordle-port", type=port, required=True)
    parser.add_argument("--connect4-port", type=port, required=True)
    parser.add_argument("--web-root", type=absolute_root, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(
        render(args.tictactoe_port, args.wordle_port, args.connect4_port, args.web_root)
    )
    print(f"Wrote {args.output}; validate with Caddy before installing.")


if __name__ == "__main__":
    main()
