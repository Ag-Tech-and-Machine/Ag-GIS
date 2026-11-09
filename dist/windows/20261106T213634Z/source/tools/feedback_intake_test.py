"""Check explicit submission, duplicate lookup and exact body transfer; no network."""
import json
from pathlib import Path
import tempfile
from unittest.mock import Mock, patch
from import_feedback import import_report

with tempfile.TemporaryDirectory(prefix="aggis-intake-test-") as temporary:
    path = Path(temporary) / "report.md"
    body = "# Synthetic Unicode é report\n\nDetails: test\nReport ID: 32dfeb3e-3ac0-4a6c-9112-688630f78b82\n"
    path.write_text(body, encoding="utf-8")
    with patch("import_feedback.subprocess.run") as run:
        result = import_report(path, "bug")
        assert result["repository"] == "JamRov/Ag-GIS-Feedback"
        assert not result["submitted"] and result["body"] == body
        run.assert_not_called()
    def cli(arguments, **kwargs):
        if "list" in arguments:
            return Mock(returncode=0, stdout="[]", stderr="")
        assert Path(arguments[arguments.index("--body-file") + 1]).read_text(encoding="utf-8") == body
        return Mock(returncode=0, stdout="https://github.com/JamRov/Ag-GIS-Feedback/issues/123\n", stderr="")
    with patch("import_feedback.shutil.which", return_value="gh"), patch("import_feedback.subprocess.run", side_effect=cli):
        assert import_report(path, "bug", submit=True)["submitted"]
    duplicate = [{"url": "https://github.com/JamRov/Ag-GIS-Feedback/issues/123", "body": body}]
    with patch("import_feedback.shutil.which", return_value="gh"), patch("import_feedback.subprocess.run", return_value=Mock(
            returncode=0, stdout=json.dumps(duplicate), stderr="")) as run:
        result = import_report(path, "bug", submit=True)
        assert result["duplicate"] and not result["submitted"] and run.call_count == 1
    with patch("import_feedback.shutil.which", return_value=None):
        try:
            import_report(path, "bug", submit=True)
            raise AssertionError("Missing CLI accepted")
        except RuntimeError:
            pass
print("Feedback intake preview, explicit submission, exact body, duplicate and missing-CLI checks passed")
