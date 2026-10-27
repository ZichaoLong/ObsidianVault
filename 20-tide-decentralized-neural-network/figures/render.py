#!/usr/bin/env python3
"""Render the tracked Tide figures without relying on temporary source files."""
import argparse
from pathlib import Path
import subprocess
import sys

BASE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--group', choices=['legacy'], default='legacy')
    parser.add_argument('--output-dir', type=Path, default=BASE)
    args = parser.parse_args()
    for name in ['tide_structure.py', 'psuf_simple.py', 'psuf_complete.py']:
        subprocess.run([sys.executable, str(BASE / 'src' / 'legacy' / name),
                        '--output-dir', str(args.output_dir.resolve())], check=True)


if __name__ == '__main__':
    main()
