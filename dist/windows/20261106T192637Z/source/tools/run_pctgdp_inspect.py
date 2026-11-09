#!/usr/bin/env python
"""
Run the PCTGDP previewer on a file or NAS path.
This script runs in the project's Python environment.
"""

import sys
from pathlib import Path

# Add plugin directory
sys.path.insert(0, str(Path(__file__).parent.parent / "plugins" / "ag_tech_tooling"))

from pctgdp_preview import inspect_project

if len(sys.argv) < 2:
    print("Usage: python run_pctgdp_inspect.py <path_to_file>")
    sys.exit(1)

nas_path = Path(sys.argv[1])
print(f"Inspecting: {nas_path}")
print(f"Size: {nas_path.stat().st_size} bytes")

# Run inspection
result = inspect_project(nas_path)
import json
print(json.dumps(result, indent=2))
