#!/usr/bin/env python3
"""ui_lint: counts known UI-guide breaks so they can only go down (a ratchet).

Usage:
  python ui_lint.py --kind wpf  --repo <Ag-Build checkout>  --baseline <file.json> [--write-baseline] [--report out.json]
  python ui_lint.py --kind qgis --repo <Ag-GIS checkout>    --baseline <file.json> [--write-baseline] [--report out.json]

Exit 0 = no rule count went up versus the baseline. Exit 1 = a new break (listed). Exit 2 = usage error.
Rules map to the product's UI_GUIDE.md (B-xx for Ag-Build, G-xx for Ag-GIS). Standard library only.
"""
import argparse, json, os, re, sys
from collections import Counter

SKIP_DIRS = {".git", "bin", "obj", "node_modules", "dist", "build", "__pycache__", ".venv", "venv", "tests", "test", "worktrees"}

def walk(root, exts):
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS and not x.startswith(".")]
        for f in files:
            if f.lower().endswith(exts):
                yield os.path.join(d, f)

def line_of(text, pos):
    return text.count("\n", 0, pos) + 1

# ---------------- WPF (Ag-Build) ----------------
FONT_SCALE = {12, 14, 18, 24, 28, 34}
INTERACTIVE = r"Button|ToggleButton|RepeatButton|TextBox|ComboBox|CheckBox|RadioButton|Slider|ListBox|ListView|DataGrid|PasswordBox"
TAP = r"Button|ToggleButton|RepeatButton|CheckBox|RadioButton|ComboBox"

def lint_wpf(repo):
    out = []
    src = os.path.join(repo, "src") if os.path.isdir(os.path.join(repo, "src")) else repo
    for p in walk(src, (".xaml",)):
        rel = os.path.relpath(p, repo).replace("\\", "/")
        t = open(p, encoding="utf-8-sig", errors="replace").read()
        is_theme = os.path.basename(p).lower() in ("app.xaml",) or "/themes/" in rel.lower() or "resourcedictionary" in os.path.basename(p).lower()
        if not is_theme:
            for m in re.finditer(r'"\s*(#[0-9A-Fa-f]{6,8})\s*"', t):
                out.append(("B-30 hex colour outside App.xaml", rel, line_of(t, m.start()), m.group(1)))
        for m in re.finditer(r'FontSize\s*=\s*"([0-9.]+)"', t):
            v = float(m.group(1))
            if v < 12:
                out.append(("B-32 text smaller than 12", rel, line_of(t, m.start()), m.group(1)))
            elif v not in FONT_SCALE:
                out.append(("B-32 font size off the scale", rel, line_of(t, m.start()), m.group(1)))
        for m in re.finditer(r"<(%s)\b([^>]*)>" % INTERACTIVE, t):
            tag, attrs = m.group(1), m.group(2)
            if "AutomationProperties.Name" not in attrs:
                out.append(("B-70 control without automation name", rel, line_of(t, m.start()), tag))
            if re.match(TAP + r"$", tag):
                for hm in re.finditer(r'\b(MinHeight|Height)\s*=\s*"([0-9.]+)"', attrs):
                    if float(hm.group(2)) < 48:
                        out.append(("B-20 tap target under 48 px", rel, line_of(t, m.start()), f"{tag} {hm.group(1)}={hm.group(2)}"))
    for p in walk(src, (".cs",)):
        rel = os.path.relpath(p, repo).replace("\\", "/")
        t = open(p, encoding="utf-8-sig", errors="replace").read()
        for m in re.finditer(r'Color\.FromRgb\(|Color\.FromArgb\(|ConvertFromString\(\s*"#|new\s+SolidColorBrush\(\s*Color\.From', t):
            out.append(("B-30 colour set in code", rel, line_of(t, m.start()), m.group(0)[:30]))
    return out

# ---------------- QGIS plugin (Ag-GIS) ----------------
UI_CALL = r"(?:\btr\(|setText\(|setToolTip\(|setWindowTitle\(|setPlaceholderText\(|setStatusTip\(|QMessageBox\.\w+\(|QLabel\(|QPushButton\(|QAction\(|QToolButton\(|addAction\(|pushMessage\(|setLabelText\(|QCheckBox\(|QGroupBox\()"
DEV_WORDS = re.compile(r"\b(schema|exception|traceback|null|NoneType|stack trace|errno|provider|sqlite|uuid|json)\b", re.I)
MONEY_WORDS = re.compile(r"(\$\s?\d|\bprice|\bpricing|\bsubscription|\bpayment|\bpurchase|\bbuy now|\bpaid plan|\binvoice)", re.I)
STRING = re.compile(r"""(?P<q>'''|\"\"\"|'|")(?P<s>.*?)(?P=q)""", re.S)

def lint_qgis(repo):
    out = []
    root = os.path.join(repo, "plugins") if os.path.isdir(os.path.join(repo, "plugins")) else repo
    for p in walk(root, (".py",)):
        rel = os.path.relpath(p, repo).replace("\\", "/")
        if "/test" in rel.lower():
            continue
        t = open(p, encoding="utf-8-sig", errors="replace").read()
        lines = t.splitlines()
        for i, ln in enumerate(lines, 1):
            if re.search(UI_CALL, ln):
                for sm in STRING.finditer(ln):
                    s = sm.group("s")
                    if DEV_WORDS.search(s):
                        out.append(("G-33 developer word in UI text", rel, i, DEV_WORDS.search(s).group(0)))
                    if MONEY_WORDS.search(s):
                        out.append(("G-35 money word in UI text", rel, i, MONEY_WORDS.search(s).group(0)))
            if re.search(r"setStyleSheet\(|QColor\(", ln) and re.search(r"#[0-9A-Fa-f]{6}\b|rgb\(", ln):
                out.append(("G-22 hard-coded colour", rel, i, "colour"))
        for m in re.finditer(r"(\b[\w.]+)\s*=\s*(QPushButton|QToolButton|QAction)\(", t):
            var = m.group(1)
            if not re.search(re.escape(var) + r"\.(setToolTip|setAccessibleName|setStatusTip)\(", t):
                out.append(("G-60 control without tooltip or accessible name", rel, line_of(t, m.start()), var))
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", choices=("wpf", "qgis"), required=True)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--write-baseline", action="store_true")
    ap.add_argument("--report")
    a = ap.parse_args()
    if not os.path.isdir(a.repo):
        print("repo not found:", a.repo); return 2
    found = lint_wpf(a.repo) if a.kind == "wpf" else lint_qgis(a.repo)
    counts = Counter(r for r, *_ in found)
    if a.report:
        json.dump({"counts": counts, "findings": [dict(rule=r, file=f, line=l, detail=d) for r, f, l, d in found]}, open(a.report, "w"), indent=1)
    if a.write_baseline or not os.path.exists(a.baseline):
        json.dump(dict(sorted(counts.items())), open(a.baseline, "w"), indent=1)
        print("baseline written:", a.baseline)
        for r, n in sorted(counts.items()): print(f"  {n:4}  {r}")
        return 0
    base = json.load(open(a.baseline))
    worse = {r: (base.get(r, 0), n) for r, n in counts.items() if n > base.get(r, 0)}
    better = {r: (n0, counts.get(r, 0)) for r, n0 in base.items() if counts.get(r, 0) < n0}
    for r, (b, n) in sorted(better.items()): print(f"BETTER {r}: {b} -> {n} (run with --write-baseline to lock it in)")
    if worse:
        for r, (b, n) in sorted(worse.items()):
            print(f"WORSE  {r}: {b} -> {n}")
            for rr, f, l, d in found:
                if rr == r: print(f"   {f}:{l}  {d}")
        print("UI guide check FAILED: a change added new guide breaks. Fix them, or propose a guide change.")
        return 1
    print("UI guide check passed. Totals:", dict(sorted(counts.items())))
    return 0

if __name__ == "__main__":
    sys.exit(main())
