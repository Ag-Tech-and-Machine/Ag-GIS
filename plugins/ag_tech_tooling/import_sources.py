# SPDX-License-Identifier: GPL-2.0-or-later
"""Local discovery adapters. Return plain records so UI and future sources stay separate."""
from pathlib import Path, PurePosixPath
from zipfile import ZipFile, BadZipFile

from qgis.core import QgsFeedback, QgsProviderRegistry, QgsMapLayerType, QgsWkbTypes
from .deere_preview import inspect_export
from .pctgdp_preview import inspect_project, PreviewCancelled


MAX_FILES = 10000
MAX_ARCHIVE_BYTES = 512 * 1024 * 1024
GIS_EXTENSIONS = {".shp", ".gpkg", ".geojson", ".json", ".kml", ".gml", ".gpx",
                  ".tif", ".tiff", ".img", ".vrt", ".asc", ".dem", ".csv", ".sqlite"}
SIDECARS = {".dbf", ".shx", ".prj", ".cpg", ".qix", ".aux", ".ovr"}


class ScanCancelled(Exception):
    pass


def scan_local(source, feedback=None, progress=None):
    """Discover folders/files without writing, extracting archives or opening layers.

    QGIS sublayer discovery supplies provider URIs and types. These records are
    candidates, not promises of successful decoding. The UI validates on opening.
    A future cloud adapter can return this same result contract after obtaining
    a local file, without adding network/account handling to this scanner.
    """
    feedback = feedback or QgsFeedback()
    progress = progress or (lambda message: None)
    source = Path(source).expanduser().resolve(strict=True)
    result = {"source_kind": "local", "source": str(source), "items": [],
              "warnings": [], "files_scanned": 0}
    seen_layers, deere_roots = set(), set()

    def check():
        if feedback.isCanceled():
            raise ScanCancelled()

    def warning(path, message):
        result["warnings"].append(f"{path}: {message}")

    def probe(uri, label):
        check()
        try:
            # Ask the native vector/raster providers directly. Other providers
            # (e.g. point clouds) can misidentify JSON members in virtual ZIPs.
            suffix = Path(uri).suffix.lower()
            providers = ("gdal",) if suffix in {".tif", ".tiff", ".img", ".asc", ".dem"} else (
                ("ogr", "gdal") if suffix in {".gpkg", ".sqlite", ".vrt"} or suffix not in GIS_EXTENSIONS else ("ogr",))
            layers = []
            for key in providers:
                check()
                metadata = QgsProviderRegistry.instance().providerMetadata(key)
                if metadata:
                    layers.extend(metadata.querySublayers(uri, feedback=feedback))
        except Exception as error:
            warning(label, f"Could not inspect data ({error})")
            return
        for layer in layers:
            check()
            if layer.type() not in (QgsMapLayerType.VectorLayer, QgsMapLayerType.RasterLayer):
                continue
            key = (layer.providerKey(), layer.uri())
            if key in seen_layers:
                continue
            seen_layers.add(key)
            result["items"].append({"kind": "layer", "name": layer.name() or label,
                "format": layer.driverName() or layer.providerKey(), "source": label,
                "uri": layer.uri(), "provider": layer.providerKey(),
                "layer_type": "vector" if layer.type() == QgsMapLayerType.VectorLayer else "raster",
                "representation": ({QgsWkbTypes.PointGeometry: "point", QgsWkbTypes.LineGeometry: "line",
                    QgsWkbTypes.PolygonGeometry: "polygon", QgsWkbTypes.NullGeometry: "table"}.get(
                        QgsWkbTypes.geometryType(layer.wkbType()), "unknown") if layer.type() == QgsMapLayerType.VectorLayer else "raster"),
                "status": "Ready — field checked when importing"})
        if not layers:
            warning(label, "No readable map layers found")

    def archive(path):
        # Validate before asking providers to look inside. No files are extracted.
        try:
            with ZipFile(path) as archive_file:
                from .archive_sources import validated_members
                entries = list(validated_members(archive_file, check,
                    max_entries=MAX_FILES, max_bytes=MAX_ARCHIVE_BYTES).values())
                machine = any(
                    PurePosixPath(e.filename).suffix.lower() in {'.fds', '.spatialcatalog'}
                    and '/rcd/eic/' in ('/' + e.filename.lower().replace('\\', '/'))
                    for e in entries if not e.is_dir())
                if machine:
                    check()
                    metadata = inspect_export(path, cancelled=feedback.isCanceled)
                    check()
                    if metadata['format'] == 'deere_gs3_rcd':
                        # Setup/catalogue preview has no operation records to classify.
                        # Preserve metadata until a verified adapter supplies them.
                        
                        result['items'].append({'kind': 'deere', 'name': path.stem,
                            'format': 'Deere GS3 RCD ZIP', 'source': str(path),
                            'metadata': metadata, 'status': 'Farm structure found; guidance decoder needed'})
                        for issue in metadata['issues']:
                            warning(path.name, issue['message'])
                    else:
                        warning(path.name, 'No recognised Deere setup or spatial catalogue found')
                for entry in entries:
                    check()
                    if not entry.is_dir() and PurePosixPath(entry.filename).suffix.lower() in GIS_EXTENSIONS:
                        probe(f"/vsizip/{path.as_posix()}/{entry.filename}", f"{path.name} / {entry.filename}")
                    elif PurePosixPath(entry.filename).suffix.lower() == ".zip":
                        warning(entry.filename, "Nested archive; unpack it to scan")
        except (BadZipFile, OSError, ValueError, RuntimeError) as error:
            check()
            warning(path.name, f"Cannot read archive ({error})")

    def inspect_file(path):
        check()
        result["files_scanned"] += 1
        progress(f"Checking {path.name}")
        if path.suffix.lower() == ".pctgdp":
            try:
                metadata = inspect_project(path, cancelled=feedback.isCanceled)
                result["items"].append({"kind": "pctgdp", "name": path.stem,
                    "format": "PCT GDP project", "source": str(path), "metadata": metadata,
                    "status": "Project identified — decoder verification needed"})
            except PreviewCancelled:
                raise ScanCancelled()
            except (OSError, ValueError, BadZipFile, RuntimeError) as error:
                warning(path.name, f"Cannot preview PCT GDP project ({error})")
        elif path.suffix.lower() == ".zip":
            archive(path)
        elif path.suffix.lower() in GIS_EXTENSIONS:
            probe(str(path), str(path))
        elif path.suffix.lower() in {".fds", ".spatialcatalog", ".fdshape", ".ver"} or path.name.lower() == "host":
            for parent in path.parents:
                if parent.name.lower() == "eic" and parent.parent.name.lower() == "rcd":
                    deere_roots.add(parent.parent)
                    break
        elif path == source and path.suffix.lower() not in SIDECARS:
            # Directly selected files also get a provider probe, even with unknown extensions.
            probe(str(path), str(path))

    if source.is_file():
        if source.suffix.lower() in SIDECARS:
            shape = source.with_suffix(".shp")
            if shape.is_file():
                inspect_file(shape)
            else:
                warning(source.name, "Select the matching .shp file or the complete folder")
        else:
            inspect_file(source)
    else:
        pending = [source]
        while pending:
            check()
            directory = pending.pop()
            try:
                for path in directory.iterdir():
                    check()
                    if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
                        warning(path.name, "Linked folder/file skipped")
                        continue
                    if path.is_dir():
                        pending.append(path)
                    elif path.is_file():
                        if result["files_scanned"] >= MAX_FILES:
                            raise ValueError("Folder contains more than 10,000 files. Select a smaller folder.")
                        try:
                            inspect_file(path)
                        except OSError as error:
                            warning(path.name, f"Cannot access file ({error})")
            except OSError as error:
                warning(directory, f"Cannot access folder ({error})")

    for rcd in sorted(deere_roots):
        check()
        progress("Reading Deere farm structure…")
        try:
            metadata = inspect_export(rcd, cancelled=feedback.isCanceled)
            if metadata["format"] == "unrecognised":
                warning(rcd, "No recognised Deere setup or spatial catalogue found")
                continue
            result["items"].append({"kind": "deere", "name": rcd.parent.name,
                "format": "Deere GS3 RCD", "source": str(rcd), "metadata": metadata,
                "status": "Farm structure found; guidance decoder needed"})
            for issue in metadata["issues"]:
                warning(rcd.name, issue["message"])
        except (OSError, ValueError, RuntimeError) as error:
            check()
            warning(rcd, f"Cannot preview Deere export ({error})")
    check()
    result["items"].sort(key=lambda row: (row["source"].casefold(), row["name"].casefold()))
    return result
