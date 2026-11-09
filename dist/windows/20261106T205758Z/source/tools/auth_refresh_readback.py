"""UNWIRED synthetic readback gates; NOT production protected-storage adapters.

Caller metadata/time/readback remain fixtures, not trusted native admission.
The committed variant composes a terminal nonsecret disk receipt before model ack;
no native atomicity, recovery/rearm or provider rotation is implied. No real secrets.
"""


def start_bound_fixture_refresh(*, fence, revision, expires_at, now, clock,
                                client_id, readback, write_bound):
    """UNWIRED old-pair -> durable uncertainty -> bound write/read -> model request.

    Synthetic callbacks, clocks and native storage remain independent trust
    boundaries. The SQLite writer reservation does NOT lock the native auth DB.
    No request is sent, no credential is rearmed and no production login is wired.
    Any failure after admission leaves terminal uncertainty, never automatic retry.
    """
    from copy import deepcopy
    from auth_flow_model import RefreshFlow, secret_text
    from auth_refresh_fence import _revision_valid

    slot = fence.slot
    if (not _revision_valid(slot) or not _revision_valid(revision)
            or type(expires_at) is not int or not 0 < expires_at < 2**63
            or not secret_text(client_id) or len(client_id) > 256):
        return None
    try:
        record = deepcopy(readback())
        expected = dict(slot=slot, revision=revision, expires_at=expires_at, attempt='')
        names = {'access_token', 'refresh_token', 'token_type', 'expires_in',
                 'refresh_token_expires_in'}
        if (type(record) is not dict or set(record) != set(expected) | {'pair'}
                or any(type(record[name]) is not type(value) or record[name] != value
                       for name, value in expected.items())
                or not RefreshFlow._valid_pair(record['pair']) or set(record['pair']) != names):
            return None
        attempt = fence.begin_bound(revision, expires_at=expires_at, now=now())
        if attempt is None:
            return None
        original = deepcopy(record)
        record['attempt'] = attempt

        def same_record(value, expected):
            return (type(value) is dict and value == expected and set(value) == set(expected)
                    and all(type(value[name]) is type(item) for name, item in expected.items())
                    and type(value['pair']) is dict
                    and all(type(value['pair'][name]) is type(item)
                            for name, item in expected['pair'].items()))

        def bind_and_start():
            # Detect a known intervening change; this is NOT a native CAS/lock.
            if not same_record(readback(), original):
                return None
            if write_bound(deepcopy(record)) is not True:
                return None
            recovered = readback()
            if not same_record(recovered, record):
                return None
            current = now()
            if type(current) is not int or not 0 < current < expires_at:
                return None
            flow = RefreshFlow(clock, record['pair'])
            request = flow.start(client_id)
            return (attempt, flow, request) if request is not None else None

        return fence.read_attempt(attempt, revision=revision, expires_at=expires_at,
                                  now=now(), readback=bind_and_start)
    except Exception:
        # Deliberately retain no callback prose, payloads or fallback credential.
        return None


def acknowledge_fixture_readback(flow, key, *, write_ok, revision, expires_at, readback):
    """Acknowledge the live fixture only after reading its exact replacement."""
    candidate = flow.pending_save(key)
    if candidate is None:
        return False
    if write_ok is not True:
        flow.saved(key, False)
        return False
    try:
        record = readback()
    except Exception:
        # Callback failures must not leave an acknowledgement eligible for retry.
        # Deliberately retain no exception prose or credential-bearing payload.
        flow.saved(key, False)
        return False
    valid = (write_ok is True and type(revision) is str and bool(revision)
             and type(expires_at) is int and 0 < expires_at < 2**63
             and type(record) is dict and set(record) == {'revision', 'expires_at', 'pair'}
             and type(record['revision']) is str and record['revision'] == revision
             and type(record['expires_at']) is int and record['expires_at'] == expires_at
             and type(record['pair']) is dict and record['pair'] == candidate
             and set(record['pair']) == set(candidate)
             and all(type(record['pair'][name]) is type(value) for name, value in candidate.items()))
    accepted = flow.saved(key, valid)
    return valid and accepted


def acknowledge_attempt_fixture_readback(flow, key, *, write_ok, revision, expires_at,
                                         binding, readback):
    """Require an encrypted fixture envelope's slot, attempt and old revision.

    UNWIRED: caller must obtain binding under read_attempt. This gate does not
    lock native records, commit success, rearm or make handoff atomic.
    """
    def label_valid(value):
        return (type(value) is str and 1 <= len(value) <= 128
                and all(33 <= ord(char) <= 126 for char in value))

    if (type(binding) is not dict or set(binding) != {'slot', 'attempt', 'old_revision'}
            or not label_valid(binding['slot']) or not label_valid(binding['old_revision'])
            or type(binding['attempt']) is not str or len(binding['attempt']) != 32
            or any(char not in '0123456789abcdef' for char in binding['attempt'])):
        flow.saved(key, False)
        return False
    binding = dict(binding)

    def bound_readback():
        record = readback()
        if (type(record) is not dict
                or set(record) != {'slot', 'attempt', 'old_revision', 'revision', 'expires_at', 'pair'}
                or any(type(record[name]) is not str or record[name] != value
                       for name, value in binding.items())):
            return None
        return {name: record[name] for name in ('revision', 'expires_at', 'pair')}

    return acknowledge_fixture_readback(
        flow, key, write_ok=write_ok, revision=revision, expires_at=expires_at,
        readback=bound_readback)


def acknowledge_committed_fixture_readback(flow, key, *, fence, write_ok, revision,
                                           expires_at, old_expires_at, now, binding, readback):
    """UNWIRED same-read fixture validation -> terminal commit -> live model ack.

    A committed receipt may outlive Cancel/expiry or a crash before acknowledgement.
    That terminal fixture must never be replayed/rearmed to recover a pair. This is
    not an atomic native-store transaction or production protected admission.
    """
    if (any(type(value) is not int or not 0 < value < 2**63
            for value in (old_expires_at, expires_at, now))
            or old_expires_at <= now or expires_at <= now):
        flow.saved(key, False)
        return False
    receipt = {}

    def capture():
        nonlocal receipt
        record = readback()
        if type(record) is dict:
            receipt = {name: record[name] for name in
                       ('slot', 'attempt', 'old_revision', 'revision', 'expires_at')
                       if name in record}
        return record

    class CommitBeforeAck:
        def pending_save(self, request_key):
            return flow.pending_save(request_key)

        def saved(self, request_key, valid):
            committed = False
            if valid is True and flow.pending_save(request_key) is not None:
                try:
                    committed = fence.record_replacement(
                        receipt['attempt'], revision=receipt['old_revision'],
                        expires_at=old_expires_at, now=now,
                        replacement_revision=revision, replacement_expires_at=expires_at,
                        readback=lambda: receipt) is True
                except Exception:
                    # No callback error prose or credential payload is retained.
                    committed = False
            accepted = flow.saved(request_key, committed)
            return committed and accepted

    return acknowledge_attempt_fixture_readback(
        CommitBeforeAck(), key, write_ok=write_ok, revision=revision,
        expires_at=expires_at, binding=binding, readback=capture)
