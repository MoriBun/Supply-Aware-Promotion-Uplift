"""``python -m dashboard [--host 127.0.0.1] [--port 8050] [--reload]``: serve the dashboard with uvicorn."""

from __future__ import annotations

import argparse


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m dashboard", description="Simulator management dashboard.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8050)
    parser.add_argument("--reload", action="store_true", help="restart on code changes (development)")
    args = parser.parse_args(argv)
    try:
        import uvicorn
    except ImportError:  # pragma: no cover
        parser.error('thiếu fastapi/uvicorn: chạy  pip install -e ".[dashboard]"')
    print(f"Dashboard: http://{args.host}:{args.port}/   (Ctrl+C để dừng)")
    uvicorn.run("dashboard.server:app", host=args.host, port=args.port, reload=args.reload, log_level="info")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
