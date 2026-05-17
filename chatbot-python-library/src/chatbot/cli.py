"""CLI — chatbot serve --config config.yaml --port 8000"""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="chatbot", description="Chatbot standalone server")
    sub = parser.add_subparsers(dest="command")

    serve_parser = sub.add_parser("serve", help="Start standalone HTTP server")
    serve_parser.add_argument("--config", "-c", default="config.yaml", help="Config YAML path")
    serve_parser.add_argument("--host", default=None)
    serve_parser.add_argument("--port", "-p", type=int, default=None)

    args = parser.parse_args(argv)

    if args.command == "serve":
        return _serve(args)
    parser.print_help()
    return 1


def _serve(args: argparse.Namespace) -> int:
    try:
        import uvicorn
    except ImportError:
        print("Install chatbot[server]: pip install 'chatbot[server]'", file=sys.stderr)
        return 1

    from chatbot.env import load_project_dotenv

    load_project_dotenv()

    from chatbot.server.app import create_app
    from chatbot.server.config import load_config

    config = load_config(args.config)
    host = args.host or config.host
    port = args.port or config.port
    app = create_app(config)
    uvicorn.run(app, host=host, port=port)
    return 0


if __name__ == "__main__":
    sys.exit(main())
