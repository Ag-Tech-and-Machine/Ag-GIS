"""Package plugin runtime files and the user guide into a QGIS-installable archive."""
import argparse
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
from check_plugin import PLUGIN, ROOT, check


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    version = check()
    output = args.output or ROOT / "dist" / f"ag_tech_tooling-{version}.zip"
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        for source in sorted(PLUGIN.iterdir()):
            if source.is_file() and (source.suffix in {".py", ".txt", ".svg"} or source.name == "LICENSE"):
                archive.write(source, f"ag_tech_tooling/{source.name}")
        archive.write(ROOT / "docs" / "USER_GUIDE.md", "ag_tech_tooling/USER_GUIDE.txt")
    with ZipFile(output) as archive:
        if archive.testzip() is not None:
            raise ValueError("Invalid plugin archive")
        required = {f"ag_tech_tooling/{name}" for name in (
            "__init__.py", "metadata.txt", "plugin.py", "LICENSE", "icon.svg",
            "simple_view.py", "farm_dialog.py", "farm_project.py", "hierarchy.py",
            "hierarchy_dialog.py", "ui_icons.py", "workspace_defaults.py", "farm_browser.py", "USER_GUIDE.txt",
            "import_dialog.py", "import_sources.py", "deere_preview.py",
            "import_destination.py", "import_placement.py",
            "agtech_organisation.svg", "agtech_client.svg", "agtech_farm.svg",
            "agtech_field.svg", "agtech_season.svg", "agtech_crop.svg",
            "agtech_whole.svg", "agtech_plan.svg", "agtech_job.svg", "agtech_result.svg")}
        if not required.issubset(archive.namelist()):
            raise ValueError("Archive is missing required files")
    print(f"Plugin ZIP ready: {output}")


if __name__ == "__main__":
    main()
