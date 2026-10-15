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
                   and (source.suffix in {".py", ".txt", ".svg"} or source.name == "LICENSE")]
        expected = {f"ag_tech_tooling/{source.name}" for source in sources}
        expected.add("ag_tech_tooling/USER_GUIDE.txt")
        assert set(archive.namelist()) == expected, "Package contains missing or unexpected files"
        for source in sources:
            assert archive.read(f"ag_tech_tooling/{source.name}") == source.read_bytes()
        assert archive.read("ag_tech_tooling/USER_GUIDE.txt") == (ROOT / "docs/USER_GUIDE.md").read_bytes()
        archive.extractall(temporary)  # Entry names validated against the explicit expected set above.
    environment = os.environ.copy()
    environment["AGTECH_TEST_PLUGIN_ROOT"] = temporary
    for script in ("updates_test.py", "smoke_test.py", "farm_project_test.py", "hierarchy_test.py", "default_workspace_test.py", "farm_browser_test.py", "deere_preview_test.py", "data_in_test.py", "import_placement_test.py"):
        subprocess.run([sys.executable, str(ROOT / "tools" / script)], env=environment, check=True)
print("Extracted plugin ZIP passed lifecycle and farm workflow checks")
