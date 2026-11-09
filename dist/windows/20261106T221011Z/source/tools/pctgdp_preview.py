"""Print a read-only PCTGDP metadata inventory; keep reports outside Git."""
import argparse
import json
from pathlib import Path
import sys
from zipfile import BadZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "plugins"))
from ag_tech_tooling.pctgdp_preview import inspect_project


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    arguments = parser.parse_args()
    try:
        print(json.dumps(inspect_project(arguments.source), indent=2))
    except (OSError, ValueError, BadZipFile, RuntimeError) as error:
        parser.exit(1, f"Cannot inspect project: {error}\n")


if __name__ == "__main__":
    main()
