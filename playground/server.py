#!/usr/bin/env python3
"""
Zafira Language - Playground Server Entrypoint
Usage:
    python playground/server.py [--port 5000] [--no-browser]
"""

import sys
import os

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.playground_server import start_playground_server


def main():
    port = 5000
    open_browser = True

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        arg = args[i]
        if arg in ('--port', '-p') and i + 1 < len(args):
            try:
                port = int(args[i + 1])
                i += 1
            except ValueError:
                pass
        elif arg.startswith('--port='):
            try:
                port = int(arg.split('=', 1)[1])
            except ValueError:
                pass
        elif arg == '--no-browser':
            open_browser = False
        elif arg.isdigit():
            port = int(arg)
        i += 1

    start_playground_server(port=port, open_browser=open_browser)


if __name__ == '__main__':
    main()
