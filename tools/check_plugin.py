"""Check syntax and mandatory metadata without needing a QGIS runtime."""
import ast
import configparser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "ag_tech_tooling"


def check():
    for source in PLUGIN.glob("*.py"):
        ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
    metadata = configparser.ConfigParser()
    metadata.read(PLUGIN / "metadata.txt", encoding="utf-8")
    for field in ("name", "description", "version", "qgisMinimumVersion", "author", "email"):
        if not metadata.get("general", field, fallback="").strip():
            raise ValueError(f"Missing metadata field: {field}")
    if not (PLUGIN / metadata["general"]["icon"]).is_file():
        raise ValueError("Missing plugin icon")
    print("Plugin syntax and metadata OK")
    return metadata["general"]["version"]


if __name__ == "__main__":
    check()
