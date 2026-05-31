#!/usr/bin/env python
"""Entry point: `python run.py resolve` / `python run.py write`."""
import sys

from zotero_marker.cli import main

if __name__ == "__main__":
    sys.exit(main())
