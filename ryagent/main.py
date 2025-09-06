#!/usr/bin/env python3
"""Main entry point for RyAgent daemon."""

import argparse
import sys

import uvicorn


def main() -> None:
    """Main entry point for RyAgent daemon."""
    parser = argparse.ArgumentParser(
        description="RyAgent - Local AI agent daemon with React web UI"
    )
    parser.add_argument(
        "--host", default="127.0.0.1", help="Host to bind to (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Port to bind to (default: 8000)"
    )
    parser.add_argument(
        "--dev", action="store_true", help="Enable development mode with auto-reload"
    )
    parser.add_argument(
        "--reload", action="store_true", help="Enable auto-reload on code changes"
    )

    args = parser.parse_args()

    # Development mode enables reload by default
    if args.dev:
        args.reload = True

    try:
        uvicorn.run(
            "ryagent.app.server:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level="info" if not args.dev else "debug",
            access_log=args.dev,
        )
    except KeyboardInterrupt:
        print("\nRyAgent daemon stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error starting RyAgent daemon: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
