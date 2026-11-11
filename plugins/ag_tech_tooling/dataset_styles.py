# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable

try:

    # SPDX-License-Identifier: GPL-2.0-or-later

    """Saved-map native styles, independent of immutable source/import snapshots.

    

    Only projectSaved commits. Append-only revisions and an observed revision guard

    prevent a stale/second map session from silently replacing newer saved styling.

    """

    from contextlib import closing

    from datetime import datetime, timezone

    import hashlib

    from pathlib import Path

    import sqlite3

    import uuid

    from zipfile import ZipFile, BadZipFile

    from xml.etree import ElementTree

    from qgis.PyQt.QtCore import QTimer

    from qgis.core import QgsMapLayerStyle, QgsProject

    from . import hierarchy as store

    

    TABLE = 'agtech_dataset_styles'

    CONTRACT = 'native-saved-style-v1'

    

    

    def latest(root):

        with closing(sqlite3.connect(store.database(root).resolve().as_uri() + '?mode=ro', uri=True)) as conn:

            if not conn.execute('SELECT 1 FROM sqlite_master WHERE name=?', (TABLE,)).fetchone():

                return {}

            conn.row_factory = sqlite3.Row

            rows = conn.execute(f'SELECT * FROM {TABLE} s WHERE revision=(SELECT MAX(revision) FROM {TABLE} WHERE dataset_id=s.dataset_id)')

            result = {row['dataset_id']: dict(row) for row in rows}

        if any(row['contract'] != CONTRACT for row in result.values()):

            raise ValueError('Saved styling requires a compatible Ag-GIS version; no styles were changed.')

        return result

    

    

    def restore(root, record, layer):

        row = latest(root).get(record['id'])

        if row:

            style = QgsMapLayerStyle(row['style_xml'])

            if not style.isValid():

                raise ValueError('Saved styling is unreadable. The project and original import style are retained.')

            style.writeToLayer(layer)

            # The durable snapshot is deliberate, not a new default-symbol candidate.

            layer.setCustomProperty('AgTechTooling/style_initialised', True)

    

    

    class SavedStyles:

        def __init__(self, warning, project=None):

            self.project = project or QgsProject.instance()

            self.warning = warning

            self.root = None

            self.expected = {}

            self.closed = False

            self.pending = None

            self.project.writeProject.connect(self.prepare_save)

            self.project.readProject.connect(self.observe)

            self.project.projectSaved.connect(self.saved)

            self.project.cleared.connect(self.clear)

            self.observe()

    

        def clear(self, *args):

            # Save-and-switch can clear before the queued callback. Finalize only

            # the captured old map's independently verified final save receipt.

            self.flush()

            self.root, self.expected = None, {}

            self.pending = None

    

        def workspace(self):

            project = self.project

            if not project.fileName() or project.readNumEntry('AgTechTooling', 'schema_version')[0] != 2:

                return None

            root = Path(project.fileName()).resolve().parent

            if Path(project.fileName()).name != 'Farm.qgz' or project.readEntry('AgTechTooling', 'farm_id')[0] != store.workspace_id(root):

                return None

            return root

    

        def observe(self, *args):

            self.clear()

            try:

                root = self.workspace()

                if root is None:

                    return

                rows = latest(root)

                digest = hashlib.sha256(Path(self.project.fileName()).read_bytes()).hexdigest()

                self.root = root

                # A restored/older map is not permission to supersede a newer snapshot.

                self.expected = {key: row['revision'] if row['project_sha256'] == digest else -1 for key, row in rows.items()}

            except (OSError, ValueError, sqlite3.Error) as error:

                self.warning(str(error))

    

        def prepare_save(self, document):

            # QGIS emits projectSaved for the temporary .qgs before replacing the

            # .qgz. Match a unique receipt in the final archive on the next turn.

            self.pending = None

            try:

                root = self.workspace()

                if root is None:

                    return

                snapshots = self.snapshots(root)

                nonce = uuid.uuid4().hex

                document.documentElement().setAttribute('aggisStyleSave', nonce)

                self.pending = (root, nonce, snapshots)

            except (OSError, ValueError, RuntimeError, sqlite3.Error) as error:

                self.warning('Recovery styling was not prepared: ' + str(error))

    

        def saved(self):

            QTimer.singleShot(0, self.flush)

    

        def flush(self):

            if self.closed:

                return

            try:

                self._save()

            except (OSError, ValueError, RuntimeError, sqlite3.Error, BadZipFile, ElementTree.ParseError) as error:

                self.warning('Recovery styling was not synchronized: ' + str(error))

    

        def snapshots(self, root):

            from .managed_data import records, dataset_uri

            catalogue = {row['id']: row for row in records(root)}

            snapshots = {}

            for layer in self.project.mapLayers().values():

                key = layer.customProperty('AgTechTooling/dataset_id', '')

                if not key or layer.customProperty('AgTechTooling/workspace') != store.workspace_id(root):

                    continue

                row = catalogue.get(key)

# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable
try:
                    from qgis.core import QgsProviderRegistry
except ImportError:
    pass  # QGIS not available, skip this import

except ImportError:

    pass  # QGIS not available, skip this module

            def identity(uri):

                decoded = QgsProviderRegistry.instance().decodeUri(layer.providerType(), uri)

                return (Path(decoded.get('path', '')).resolve(), decoded.get('layerName', ''), decoded.get('layerId', ''))

            if row is None or layer.providerType() != row['provider'] or identity(layer.source()) != identity(dataset_uri(root, row)):

                raise ValueError('Saved layer identity changed; catalogue styling was retained.')

            if key in snapshots:

                raise ValueError('Multiple map copies of one dataset need review; catalogue styling was retained.')

            style = QgsMapLayerStyle(); style.readFromLayer(layer)

            if not style.isValid():

                raise ValueError('A native layer style could not be serialized.')

            snapshots[key] = style.xmlData()

        return snapshots



    def _save(self):

        pending, self.pending = self.pending, None

        if pending is None:

            return

        saved_root, nonce, snapshots = pending

        root = saved_root

        project_path = root / 'Farm.qgz'

        if not snapshots:

            return

        with ZipFile(project_path) as archive:

            maps = [name for name in archive.namelist() if name.endswith('.qgs')]

            if len(maps) != 1 or ElementTree.fromstring(archive.read(maps[0])).get('aggisStyleSave') != nonce:

                raise ValueError('Final map archive did not match its save receipt; previous recovery styling retained.')

        if self.root is None:

            self.root = root

            self.expected = {key: -1 for key in latest(root)}

        if root != self.root:

            raise ValueError('Reopen this workspace before synchronizing its styling.')

        digest = hashlib.sha256(project_path.read_bytes()).hexdigest()

        updated = dict(self.expected)

        with closing(sqlite3.connect(store.database(root).as_uri() + '?mode=rw', uri=True)) as conn:

            conn.execute('PRAGMA foreign_keys=ON')

            with conn:

                conn.execute('BEGIN IMMEDIATE')

                conn.execute(f'''CREATE TABLE IF NOT EXISTS {TABLE} (

                    dataset_id TEXT NOT NULL, revision INTEGER NOT NULL,

                    contract TEXT NOT NULL, style_xml TEXT NOT NULL,

                    project_sha256 TEXT NOT NULL, saved_utc TEXT NOT NULL,

                    PRIMARY KEY(dataset_id,revision),

                    FOREIGN KEY(dataset_id) REFERENCES agtech_datasets(id))''')

                conn.execute(f'''CREATE TRIGGER IF NOT EXISTS agtech_styles_no_update BEFORE UPDATE ON {TABLE}

                    BEGIN SELECT RAISE(ABORT,'Saved style history is append-only'); END''')

                conn.execute(f'''CREATE TRIGGER IF NOT EXISTS agtech_styles_no_delete BEFORE DELETE ON {TABLE}

                    BEGIN SELECT RAISE(ABORT,'Saved style history is append-only'); END''')

                for key, xml in snapshots.items():

                    previous = conn.execute(f'SELECT revision,contract FROM {TABLE} WHERE dataset_id=? ORDER BY revision DESC LIMIT 1', (key,)).fetchone()

                    revision = previous[0] if previous else 0

                    if (previous and previous[1] != CONTRACT) or revision != self.expected.get(key, 0):

                        raise ValueError('Newer or unrecognized recovery styling exists. Keep this saved map and review before replacing recovery styling.')

                    conn.execute(f'INSERT INTO {TABLE} VALUES (?,?,?,?,?,?)', (key, revision + 1, CONTRACT, xml, digest, datetime.now(timezone.utc).isoformat()))

                    updated[key] = revision + 1

        self.expected = updated



    def close(self):

        if self.closed:

            return

        self.flush()

        self.closed = True

        self.project.writeProject.disconnect(self.prepare_save)

        self.project.readProject.disconnect(self.observe)

        self.project.projectSaved.disconnect(self.saved)

        self.project.cleared.disconnect(self.clear)

        self.clear()


