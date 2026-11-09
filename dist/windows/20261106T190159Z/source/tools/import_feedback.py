"""Maintainer intake of a user-approved saved report; preview unless --submit is given."""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

REPOSITORY = "JamRov/Ag-GIS-Feedback"
REPORT_ID = re.compile(r"^Report ID: ([0-9a-fA-F-]{36})$", re.MULTILINE)


def read_report(path):
    if path.stat().st_size > 256 * 1024:
        raise ValueError("Report is over 256 KiB; review and reduce it before importing")
    body = path.read_text(encoding="utf-8-sig")
    matches = REPORT_ID.findall(body)
    if not matches:
        raise ValueError("Expected an Ag-GIS saved report with a Report ID; review other reports manually")
    import uuid
    report_id = str(uuid.UUID(matches[-1]))
    title = next((line[2:].strip() for line in body.splitlines() if line.startswith("# ")), "Feedback report")[:140]
    return title, body, report_id


def import_report(path, kind, repository=REPOSITORY, submit=False):
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("Repository must be owner/name")
    title, body, report_id = read_report(path)
    if not submit:
        return {"submitted": False, "repository": repository, "title": title, "report_id": report_id,
                "labels": ["feedback", kind], "body": body}
    gh = shutil.which("gh")
    if not gh:
        raise RuntimeError("Install GitHub CLI and sign in to an account with access first; no report was submitted")
    def run(arguments):
        result = subprocess.run([gh, *arguments], capture_output=True, text=True, encoding="utf-8", check=False)
        if result.returncode:
            raise RuntimeError("GitHub CLI failed. Check sign-in/repository access and existing issues before retrying. " + result.stderr.strip())
        return result.stdout.strip()
    # Search is best-effort: GitHub indexing is asynchronous; concurrent imports need human review.
    existing = json.loads(run(["issue", "list", "--repo", repository, "--state", "all", "--search",
                               f'"{report_id}" in:body', "--json", "url,body", "--limit", "100"]))
    for issue in existing:
        if report_id in [value.lower() for value in REPORT_ID.findall(issue.get("body") or "")]:
            return {"submitted": False, "duplicate": True, "url": issue["url"], "report_id": report_id}
    with tempfile.TemporaryDirectory(prefix="aggis-feedback-intake-") as temporary:
        body_file = Path(temporary) / "report.md"
        body_file.write_text(body, encoding="utf-8")
        url = run(["issue", "create", "--repo", repository, "--title", title, "--body-file", str(body_file),
                   "--label", "feedback", "--label", kind])
    if not url.startswith(f"https://github.com/{repository}/issues/"):
        raise RuntimeError("GitHub returned an unexpected response; check the tracker before retrying")
    return {"submitted": True, "url": url, "report_id": report_id}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--kind", choices=("bug", "enhancement", "question"), default="bug")
    parser.add_argument("--repository", default=REPOSITORY)
    parser.add_argument("--submit", action="store_true", help="Create a GitHub issue after you have reviewed permission/content")
    args = parser.parse_args()
    print(json.dumps(import_report(args.report, args.kind, args.repository, args.submit), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
