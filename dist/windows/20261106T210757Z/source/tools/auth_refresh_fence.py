"""UNWIRED synthetic refresh fence, NOT a credential store or product login.

Only nonsecret fixture-slot/revision labels, expiry and random attempt IDs go here.
A caller must commit admission BEFORE sending any refresh request. Admission is
uncertain unless exact synthetic replacement metadata is committed as a terminal
reconciled receipt in schema 3. Neither state can rearm or hand off tokens. A valid
observed expiry commits a terminal expired state, so earlier injected time cannot
resurrect it. Schema 1/2 are refused without migration. No product adapter is wired.
"""
from contextlib import closing
import os
from pathlib import Path
import sqlite3
import uuid


def _revision_valid(value):
    return (type(value) is str and 1 <= len(value) <= 128
            and all(33 <= ord(char) <= 126 for char in value))


class RefreshFence:
    def __init__(self, path, slot):
        self.path = Path(path).resolve()
        self.slot = slot

    @staticmethod
    def create(path, slot, *, revision, expires_at):
        """Explicit synthetic enrollment only; never overwrite an existing fence."""
        if not _revision_valid(revision) or type(expires_at) is not int or not 0 < expires_at < 2**63:
            raise ValueError('Invalid synthetic revision or absolute expiry')
        path = Path(path).resolve()
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(fd)
        with closing(sqlite3.connect(path)) as conn:
            conn.execute('PRAGMA synchronous=FULL')
            conn.execute('CREATE TABLE refresh_fence ('
                         'slot TEXT PRIMARY KEY, state TEXT NOT NULL, attempt TEXT NOT NULL, '
                         'revision TEXT NOT NULL, expires_at INTEGER NOT NULL)')
            conn.execute('CREATE TABLE refresh_replacement ('
                         'slot TEXT PRIMARY KEY, attempt TEXT NOT NULL, '
                         'old_revision TEXT NOT NULL, old_expires_at INTEGER NOT NULL, '
                         'revision TEXT NOT NULL, expires_at INTEGER NOT NULL)')
            conn.execute('PRAGMA user_version=3')
            conn.execute('INSERT INTO refresh_fence VALUES (?, ?, ?, ?, ?)',
                         (slot, 'ready', '', revision, expires_at))
            conn.commit()

    def begin(self, revision, *, now):
        """Admit exact revision before absolute expiry; now is injected UNIX seconds.

        No protected record is read. A production adapter must independently verify
        revision/expiry and trustworthy time. This fixture only prevents reuse after
        a committed expiry observation; it cannot detect an earlier stale clock or
        restoration of an older database snapshot, and a failed commit cannot latch.
        """
        return self._begin(revision, now=now, expected_expires_at=None)

    def begin_bound(self, revision, *, expires_at, now):
        """Require exact readback expiry as well as revision in the admission lock.

        Metadata is still caller supplied. This does not read protected storage,
        lock its record, bind a token pair, or make injected time trustworthy.
        """
        if type(expires_at) is not int or not 0 < expires_at < 2**63:
            return None
        return self._begin(revision, now=now, expected_expires_at=expires_at)

    def read_attempt(self, attempt, *, revision, expires_at, now, readback):
        """Read a fixture only under its exact uncertain admission's writer lock.

        Does not acknowledge success or rearm. The callback must read/validate the
        protected replacement separately. SQLite cannot lock native credential
        storage atomically, and injected time is not trusted. No secrets persisted.
        """
        if (type(attempt) is not str or len(attempt) != 32
                or any(char not in '0123456789abcdef' for char in attempt)
                or not _revision_valid(revision)
                or type(expires_at) is not int or not 0 < expires_at < 2**63
                or type(now) is not int or not 0 < now < 2**63):
            return None
        try:
            with closing(sqlite3.connect(self.path.as_uri() + '?mode=rw', uri=True,
                                         timeout=0)) as conn:
                conn.execute('BEGIN IMMEDIATE')
                if conn.execute('PRAGMA user_version').fetchone()[0] != 3:
                    return None
                row = conn.execute("SELECT 1 FROM refresh_fence WHERE slot=? "
                                   "AND state='uncertain' AND attempt=? AND revision=? "
                                   "AND typeof(expires_at)='integer' AND expires_at=? AND expires_at>?",
                                   (self.slot, attempt, revision, expires_at, now)).fetchone()
                if row is None:
                    return None
                return readback()
        except (sqlite3.Error, OSError, ValueError):
            return None

    def record_replacement(self, attempt, *, revision, expires_at, now,
                           replacement_revision, replacement_expires_at, readback):
        """Commit a terminal NONSECRET fixture receipt, never rearm or release tokens.

        A callback must return exact minimal replacement metadata. This method
        cannot authenticate that callback or lock a separate native auth store.
        It is not model acknowledgement, trusted time or production recovery.
        Schema 1/2 are refused without migration; only new synthetic fixtures use 3.
        """
        slot = self.slot
        if (not _revision_valid(slot) or not _revision_valid(revision)
                or not _revision_valid(replacement_revision) or replacement_revision == revision
                or type(attempt) is not str or len(attempt) != 32
                or any(char not in '0123456789abcdef' for char in attempt)
                or any(type(value) is not int or not 0 < value < 2**63
                       for value in (expires_at, replacement_expires_at, now))
                or expires_at <= now or replacement_expires_at <= now):
            return False
        expected = dict(slot=slot, attempt=attempt, old_revision=revision,
                        revision=replacement_revision, expires_at=replacement_expires_at)
        try:
            with closing(sqlite3.connect(self.path.as_uri() + '?mode=rw', uri=True,
                                         timeout=0)) as conn:
                conn.execute('PRAGMA synchronous=FULL')
                conn.execute('BEGIN IMMEDIATE')
                if conn.execute('PRAGMA user_version').fetchone()[0] != 3:
                    return False
                row = conn.execute("SELECT 1 FROM refresh_fence WHERE slot=? "
                                   "AND state='uncertain' AND attempt=? AND revision=? "
                                   "AND typeof(expires_at)='integer' AND expires_at=?",
                                   (slot, attempt, revision, expires_at)).fetchone()
                if row is None:
                    return False
                try:
                    record = readback()
                except Exception:
                    return False  # Never retain arbitrary callback prose/payloads.
                if (type(record) is not dict or set(record) != set(expected)
                        or any(type(record[name]) is not type(value) or record[name] != value
                               for name, value in expected.items())):
                    return False
                conn.execute('INSERT INTO refresh_replacement VALUES (?,?,?,?,?,?)',
                             (slot, attempt, revision, expires_at,
                              replacement_revision, replacement_expires_at))
                result = conn.execute("UPDATE refresh_fence SET state='reconciled' "
                                      "WHERE slot=? AND state='uncertain' AND attempt=? AND revision=? "
                                      "AND expires_at=?", (slot, attempt, revision, expires_at))
                if result.rowcount != 1:
                    return False
                conn.commit()
                return True
        except (sqlite3.Error, OSError, ValueError):
            return False

    def _begin(self, revision, *, now, expected_expires_at):
        if not _revision_valid(revision) or type(now) is not int or not 0 < now < 2**63:
            return None
        try:
            with closing(sqlite3.connect(self.path.as_uri() + '?mode=rw', uri=True,
                                         timeout=0)) as conn:
                conn.execute('PRAGMA synchronous=FULL')
                conn.execute('BEGIN IMMEDIATE')
                if conn.execute('PRAGMA user_version').fetchone()[0] != 3:
                    return None
                if expected_expires_at is not None:
                    bound = conn.execute("SELECT 1 FROM refresh_fence WHERE slot=? AND revision=? "
                                         "AND typeof(expires_at)='integer' AND expires_at=?",
                                         (self.slot, revision, expected_expires_at)).fetchone()
                    if bound is None:
                        return None
                expired = conn.execute("UPDATE refresh_fence SET state='expired' "
                                       "WHERE slot=? AND state='ready' AND attempt='' AND revision=? "
                                       "AND typeof(expires_at)='integer' AND expires_at>0 AND expires_at<=?",
                                       (self.slot, revision, now))
                if expired.rowcount == 1:
                    conn.commit()
                    return None
                attempt = uuid.uuid4().hex
                result = conn.execute("UPDATE refresh_fence SET state='uncertain',attempt=? "
                                      "WHERE slot=? AND state='ready' AND attempt='' AND revision=? "
                                      "AND typeof(expires_at)='integer' AND expires_at>?",
                                      (attempt, self.slot, revision, now))
                if result.rowcount != 1:
                    return None
                conn.commit()
                return attempt
        except (sqlite3.Error, OSError, ValueError):
            return None
