"""Check exact package content and execute tests against an extracted ZIP."""
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from zipfile import ZipFile
from check_plugin import ROOT, PLUGIN, check

version = check()
package = ROOT / "dist" / f"ag_tech_tooling-{version}.zip"
with tempfile.TemporaryDirectory(prefix="agtech-package-test-") as temporary:
    with ZipFile(package) as archive:
        sources = [source for source in PLUGIN.iterdir() if source.is_file()
                   and (source.suffix in {".py", ".txt", ".svg", ".ico"} or source.name == "LICENSE")]
        expected = {f"ag_tech_tooling/{source.name}" for source in sources}
        expected.update({"ag_tech_tooling/USER_GUIDE.txt", "ag_tech_tooling/START_HERE.txt"})
        assert set(archive.namelist()) == expected, "Package contains missing or unexpected files"
        for source in sources:
            assert archive.read(f"ag_tech_tooling/{source.name}") == source.read_bytes()
        assert archive.read("ag_tech_tooling/USER_GUIDE.txt") == (ROOT / "docs/USER_GUIDE.md").read_bytes()
        assert archive.read("ag_tech_tooling/START_HERE.txt") == (ROOT / "START_HERE.md").read_bytes()
        archive.extractall(temporary)  # Entry names validated against the explicit expected set above.
    environment = os.environ.copy()
    environment["AGTECH_TEST_PLUGIN_ROOT"] = temporary
    for script in ("github_session_test.py", "branding_test.py", "windows_taskbar_test.py", "feedback_test.py", "update_catalog_test.py", "updates_test.py", "update_native_test.py", "smoke_test.py", "classification_test.py", "classification_registry_test.py", "classification_resolution_test.py", "operation_style_test.py", "dataset_style_test.py", "data_dictionary_test.py", "farm_project_test.py", "hierarchy_test.py", "default_workspace_test.py", "farm_browser_test.py","farmer_view_test.py","background_maps_test.py", "esri_background_test.py", "background_checkbox_paint_test.py", "background_render_test.py", "archive_sources_test.py", "deere_preview_test.py", "pctgdp_test.py", "data_in_test.py", "season_review_test.py", "season_boundary_test.py", "reviewed_import_test.py", "import_placement_test.py", "managed_data_test.py"):
        subprocess.run([sys.executable, str(ROOT / "tools" / script)], env=environment, check=True)
    subprocess.run([sys.executable, str(ROOT / 'tools' / 'run_github_connection_test.py'),
                    '--plugin-root', str(Path(temporary) / 'ag_tech_tooling')], check=True)
print("Extracted plugin ZIP passed lifecycle and farm workflow checks")
