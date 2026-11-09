# SPDX-License-Identifier: GPL-2.0-or-later
"""Read-only PCTGDP container inventory, not an undocumented geometry decoder."""
import hashlib
from pathlib import Path, PurePosixPath
from xml.parsers import expat
from zipfile import ZipFile

MAX_XML_BYTES = 2 * 1024 * 1024 * 1024
MAX_LAYERS = 500
MAX_ELEMENTS = 1000000
MAX_TEXT = 65536
CHUNK = 1024 * 1024


class PreviewCancelled(Exception):
    pass


def inspect_project(source, cancelled=lambda: False):
    """Stream bounded XML; discard grid text rather than loading gigabytes in RAM.

    Record only observed metadata. UTM zone/hemisphere do not identify a datum;
    no EPSG code, field assignment, grid orientation or pixel encoding is inferred.
    """
    source = Path(source)

    def check():
        if cancelled():
            raise PreviewCancelled()

    def digest():
        result = hashlib.sha256()
        with source.open("rb") as stream:
            while True:
                check()
                block = stream.read(CHUNK)
                if not block:
                    break
                result.update(block)
        return result.hexdigest()

    before = digest()
    with source.open("rb") as stream:
        if stream.read(6) != b"PCTGDP":
            raise ValueError("Missing PCTGDP signature; not a supported project container")
    layers, stack = [], []
    current = None
    elements = 0
    root_seen = False
    parser = expat.ParserCreate(namespace_separator="}")

    def local(name):
        return name.rsplit("}", 1)[-1]

    def start(name, attrs):
        nonlocal current, elements, root_seen
        check()
        name = local(name)
        elements += 1
        if elements > MAX_ELEMENTS or len(stack) >= 64:
            raise ValueError("Project XML exceeds structural preview limits")
        if not stack:
            if name != "ProjectVariables":
                raise ValueError("Unsupported project XML root")
            root_seen = True
        stack.append([name, "", 0])
        if name == "LayerVariables":
            if current is not None or len(layers) >= MAX_LAYERS:
                raise ValueError("Project exceeds layer preview limits")
            current = {"name": "Unnamed layer", "type": next(
                (value for key, value in attrs.items() if local(key) == "type"), "Unknown"),
                "grid_characters": 0}

    def text(value):
        if not stack:
            return
        node = stack[-1]
        node[2] += len(value)
        if node[0] == "GridString":
            return
        if node[2] > MAX_TEXT:
            raise ValueError("Project metadata text exceeds preview limits")
        node[1] += value

    def end(name):
        nonlocal current
        name = local(name)
        node = stack.pop()
        if current is None:
            return
        # Nested boundary records can contain zone 0: only use the layer's
        # direct metadata or its GridLayer, never overwrite it with nested data.
        path = [item[0] for item in stack]
        depth = len(path) - path.index("LayerVariables") if "LayerVariables" in path else 0
        value = node[1].strip()
        mapping = {"Id": "id", "DisplayName": "name", "DataUnits": "units",
                   "SurfaceType": "surface_type", "UtmZone": "utm_zone",
                   "UtmNS": "hemisphere", "UtmNs": "hemisphere",
                   "PixelSize": "pixel_size", "NullValue": "nodata"}
        if name in mapping and (depth == 1 or (depth == 2 and path[-1] == "GridLayer")):
            current[mapping[name]] = value
        if name in {"X", "Y"} and path[-2:] == ["GridLayer", "Origin"]:
            current["origin_" + name.lower()] = value
        if name == "GridString" and path[-1:] == ["GridLayer"]:
            current["grid_characters"] = node[2]
        if name == "LayerVariables":
            layers.append(current)
            current = None

    def reject(*args):
        raise ValueError("DTD/entity declarations are not accepted")

    parser.StartElementHandler = start
    parser.CharacterDataHandler = text
    parser.EndElementHandler = end
    parser.StartDoctypeDeclHandler = reject
    parser.EntityDeclHandler = reject
    parser.ExternalEntityRefHandler = reject

    def parse(block, final):
        try:
            parser.Parse(block, final)
        except expat.ExpatError as error:
            raise ValueError(f"Invalid project XML ({error})") from error

    with ZipFile(source) as archive:
        entries = archive.infolist()
        if len(entries) != 1:
            raise ValueError("Expected a single project XML member")
        entry = entries[0]
        name = entry.filename.replace("\\", "/")
        parts = PurePosixPath(name)
        if (parts.is_absolute() or ".." in parts.parts or ":" in name or
                entry.flag_bits & 1 or entry.is_dir() or parts.suffix.lower() != ".pctgdp"):
            raise ValueError("Unsafe, encrypted or unsupported project member")
        if entry.file_size > MAX_XML_BYTES:
            raise ValueError("Project exceeds 2 GiB uncompressed preview limit")
        total = 0
        with archive.open(entry) as stream:
            while True:
                check()
                block = stream.read(CHUNK)
                if not block:
                    break
                total += len(block)
                if total > MAX_XML_BYTES:
                    raise ValueError("Project exceeds uncompressed preview limit")
                parse(block, False)
            parse(b"", True)
    if not root_seen:
        raise ValueError("Missing project XML")
    unchanged = digest() == before
    if not unchanged:
        raise ValueError("Source changed during inspection; finish exporting and rescan")
    return {"format": "pctgdp", "layers": layers, "sha256": before,
            "source_unchanged": unchanged, "xml_bytes": total,
            "limitations": ["Coordinate datum is not established by UTM zone/hemisphere",
                            "Grid encoding, orientation and polygon topology need verification",
                            "Inspection only; no map data imported"]}
