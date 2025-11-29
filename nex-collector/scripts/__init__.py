#!/usr/bin/env python3
"""Make seed script executable."""
import sys
from pathlib import Path

if __name__ == "__main__":
    seed_path = Path(__file__).parent / "scripts" / "seed_demo.py"
    if seed_path.exists():
        seed_path.chmod(0o755)
        print(f"Made {seed_path} executable")
    else:
        print(f"Seed script not found at {seed_path}")

