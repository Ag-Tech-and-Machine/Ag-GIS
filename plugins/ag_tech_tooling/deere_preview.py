"""Read-only GS3 RCD inventory. This module does not decode Deere geometry."""
import hashlib
from pathlib import Path
import xml.etree.ElementTree as ET


SETUP_NS = "urn:schemas-johndeere-com:RCD:Setup"
CATALOG_NS = "urn:schemas-johndeere-com:RCD:SpatialCatalog:FieldImportExport"
XML_LIMIT = 10 * 1024 * 1024


def _local(tag):
    return tag.rsplit("}", 1)[-1]


def _hash(path, cancelled=None):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            if cancelled and cancelled():
                raise RuntimeError("Inspection cancelled")
            digest.update(block)
    return digest.hexdigest()


def _inside(root, path):
    resolved = path.resolve(strict=True)
    if not resolved.is_relative_to(root):
        raise ValueError("Export contains a link outside the selected folder")
    return resolved


def _files(root, cancelled=None):
    # Reject directory links before descending, including Windows junctions.
    pending, result = [root], []
    while pending:
        for path in sorted(pending.pop().iterdir()):
            if cancelled and cancelled():
                raise RuntimeError("Inspection cancelled")
            if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
                raise ValueError("Export contains a linked file or folder")
            _inside(root, path)
            if path.is_dir():
                pending.append(path)
            elif path.is_file():
                result.append(path)
    return sorted(result)


def _xml(path):
    with path.open("rb") as source:
        data = source.read(XML_LIMIT + 1)
    if len(data) > XML_LIMIT:
        raise ValueError("XML metadata exceeds the 10 MiB preview limit")
    # No DTD or entity expansion; UTF-16/32 encodings are also covered.
    markup = data.replace(b"\x00", b"").upper()
    if b"<!DOCTYPE" in markup or b"<!ENTITY" in markup:
        raise ValueError("DTD/entity declarations are not accepted")
    return ET.fromstring(data)


def inspect_export(folder, probe_native=False, cancelled=None):
    """Return a JSON-compatible preview, keeping machine IDs and parent refs.

    Accept the GS3_2630 folder, a profile, or its RCD folder. No source writes,
    project changes, hierarchy inserts or geometry conversions are performed.
    Native probing requires an initialised QgsApplication.
    """
    root = Path(folder).resolve(strict=True)
    if not root.is_dir():
        raise ValueError("Select an unpacked Deere export folder")
    paths = _files(root, cancelled)
    manifest = [{"path": p.relative_to(root).as_posix(), "bytes": p.stat().st_size,
                 "sha256": _hash(p, cancelled) if cancelled else _hash(p)} for p in paths]
    report = {"format": "unrecognised", "files": manifest, "profiles": [],
              "entities": [], "spatial_items": [], "issues": [],
              "native_probe": "not_run", "source_unchanged": False,
              "geometry_import_supported": False}
    entities = {}

    def issue(message, path):
        report["issues"].append({"path": path.relative_to(root).as_posix(),
                                 "message": message})

    for path in paths:
        if cancelled and cancelled():
            raise RuntimeError("Inspection cancelled")
        if path.suffix.lower() not in {".fds", ".spatialcatalog"}:
            continue
        # Only recognise the observed EIC layout; unrelated XML is not Deere setup.
        eic = next((p for p in path.parents if p.name.lower() == "eic"
                    and p.parent.name.lower() == "rcd"), None)
        if eic is None:
            continue
        try:
            tree = _xml(path)
        except (ValueError, ET.ParseError) as error:
            issue(f"Cannot read metadata: {error}", path)
            continue
        expected = {f"{{{SETUP_NS}}}SetupFile", f"{{{CATALOG_NS}}}SpatialCatalog"}
        if tree.tag not in expected:
            issue("Unrecognised metadata namespace or root", path)
            continue
        report["format"] = "deere_gs3_rcd"
        profile = eic.parent.parent
        profile_key = profile.relative_to(root).as_posix() if profile.is_relative_to(root) else "."
        if profile_key not in report["profiles"]:
            report["profiles"].append(profile_key)
        for node in tree.iter():
            if node.tag not in {f"{{{SETUP_NS}}}{kind}" for kind in ("Client", "Farm", "Field")}:
                continue
            kind = _local(node.tag).lower()
            machine_id = node.get("erid", "")
            if not machine_id:
                issue(f"{kind} has no machine identifier", path)
                continue
            parent_ref = node.get("clientRef" if kind == "farm" else "farmRef", "") if kind != "client" else ""
            record = {"profile": profile_key, "kind": kind, "id": machine_id,
                      "name": node.get("name", ""), "parent_id": parent_ref,
                      "attributes": dict(node.attrib)}
            key = (profile_key, kind, machine_id.casefold())
            if key in entities and entities[key] != record:
                issue(f"Conflicting {kind} metadata for the same machine identifier", path)
            else:
                entities[key] = record
        for group in tree.iter():
            if _local(group.tag) != "SpatialItems":
                continue
            for item in group:
                filename = item.get("fileName", "")
                resource = None
                if filename:
                    # Resource references are a single filename, never a path/URI.
                    if "/" in filename or "\\" in filename or ":" in filename or filename in {".", ".."}:
                        issue("Unsafe spatial resource filename", path)
                    else:
                        candidate = path.parent / (filename if filename.lower().endswith(".fdshape") else filename + ".fdShape")
                        if candidate.is_file():
                            resource = _inside(root, candidate).relative_to(root).as_posix()
                        else:
                            issue("Referenced spatial resource is missing", path)
                else:
                    issue("Spatial item has no resource filename", path)
                report["spatial_items"].append({
                    "profile": profile_key, "kind": _local(item.tag),
                    "id": item.get("erid", ""), "name": item.get("name", ""),
                    "field_id": group.get("eridFieldRef", ""), "resource": resource,
                    "catalog": path.relative_to(root).as_posix(),
                    "attributes": dict(item.attrib),
                    "properties": [{"tag": child.tag, "attributes": dict(child.attrib),
                                    "text": child.text} for child in item],
                    "native_layers": [], "geometry_status": "not_decoded"})
    report["entities"] = list(entities.values())
    for entity in report["entities"]:
        parent_kind = {"farm": "client", "field": "farm"}.get(entity["kind"])
        if parent_kind and (entity["profile"], parent_kind, entity["parent_id"].casefold()) not in entities:
            report["issues"].append({"message": f"{entity['kind']} has an unresolved parent", "id": entity["id"]})
    for item in report["spatial_items"]:
        if (item["profile"], "field", item["field_id"].casefold()) not in entities:
            report["issues"].append({"message": "Spatial item has an unresolved field", "id": item["id"]})
    if probe_native:
        from qgis.core import QgsProviderRegistry
        report["native_probe"] = "completed"
        for item in report["spatial_items"]:
            if item["resource"]:
                details = QgsProviderRegistry.instance().querySublayers(str(root / item["resource"]))
                item["native_layers"] = [{"name": d.name(), "provider": d.providerKey()}
                                         for d in details]
                # Discovery alone does not establish safe geometry conversion.
                item["geometry_status"] = "native_candidate" if details else "adapter_required"
    if paths != _files(root, cancelled) or any(
            (_hash(root / f["path"], cancelled) if cancelled else _hash(root / f["path"])) != f["sha256"]
            for f in manifest):
        raise RuntimeError("Source changed during preview; discard this result and retry")
    report["source_unchanged"] = True
    return report
