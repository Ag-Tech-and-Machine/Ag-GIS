"""Package only plugin source files into a QGIS-installable archive."""
import argparse
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
from check_plugin import PLUGIN, ROOT, check


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    version = check()
    output = args.output or ROOT / "dist" / f"qgis_plugin_work-{version}.zip"
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        for source in sorted(PLUGIN.iterdir()):
            if source.is_file() and source.suffix in {".py", ".txt", ".svg"}:
                archive.write(source, f"qgis_plugin_work/{source.name}")
    with ZipFile(output) as archive:
        if archive.testzip() is not None:
            raise ValueError("Invalid plugin archive")
        required = {"qgis_plugin_work/__init__.py", "qgis_plugin_work/metadata.txt", "qgis_plugin_work/plugin.py"}
        if not required.issubset(archive.namelist()):
            raise ValueError("Archive is missing required files")
    print(f"Plugin ZIP ready: {output}")


if __name__ == "__main__":
    main()
