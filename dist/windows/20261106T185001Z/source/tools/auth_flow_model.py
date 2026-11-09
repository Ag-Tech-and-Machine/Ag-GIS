"""UNWIRED developer-only device-flow model, not a production OAuth client.

Pure transitions and synthetic request descriptions; no network, Qt, credential
storage, browser, settings or report publication. A future adapter requires its
own native request/logging review and source/package/desktop acceptance.
"""
from dataclasses import dataclass, field
import re


def positive_seconds(value, maximum):
    """Local fail-closed bounds, not provider lifetime guarantees."""
    return type(value) is int and 0 < value <= maximum


def secret_text(value):
    return isinstance(value, str) and 0 < len(value) <= 8192 and all(
        32 < ord(char) < 127 for char in value)


@dataclass(frozen=True)
class Request:
    key: tuple
    endpoint: str
    payload: dict = field(repr=False)


class DeviceFlow:
    def __init__(self, clock):
        self.clock = clock
        self.state = 'idle'
        self.generation = 0
        self.sequence = 0
        self.active = None
        self._tokens = None
        self._client = None
        self._device = None
        self.interval = 0
        self.deadline = 0
        self.next_poll = 0
        self.sent_at = 0
        self.request_deadline = 0
        self._events = []

    def _record(self, event, label):
        # Deliberate allowlist: never accept provider prose, bodies or headers.
        allowed = {'state': {'idle', 'requesting', 'waiting', 'authorized', 'cancelled',
                             'expired', 'failed', 'denied', 'unconfigured'},
                   'request': {'device', 'token'}, 'callback': {'accepted', 'stale'}}
        if event not in allowed or label not in allowed[event]:
            raise ValueError('Invalid diagnostic label')
        self._events.append((event, label))
        del self._events[:-32]

    def diagnostics(self):
        return {'state': self.state, 'generation': self.generation,
                'in_flight': self.active is not None, 'events': list(self._events)}

    def _request(self, endpoint, payload):
        self.sequence += 1
        self.active = (self.generation, self.sequence)
        self.sent_at = self.clock()
        self.request_deadline = self.sent_at + 30  # model-only request limit
        self._record('request', endpoint)
        return Request(self.active, endpoint, payload)

    def start(self, client_id):
        self._stop('idle')
        if not secret_text(client_id) or len(client_id) > 256:
            self.state = 'unconfigured'
            return None
        self._client = client_id
        self.state = 'requesting'
        return self._request('device', {'client_id': client_id, 'scope': 'offline_access'})

    def _stop(self, state):
        self.generation += 1
        self.state = state
        self.active = None
        self._device = None
        self._client = None
        self._tokens = None
        self._record('state', state)

    def cancel(self):
        self._stop('cancelled')

    def tick(self):
        if self.state == 'waiting' and self.clock() >= self.deadline:
            self._stop('expired')
        elif self.active and self.clock() >= self.request_deadline:
            self._stop('failed')

    def poll(self):
        self.tick()
        if self.state != 'waiting' or self.active or self.clock() < self.next_poll:
            return None
        return self._request('token', {
            'client_id': self._client, 'device_code': self._device,
            'grant_type': 'urn:ietf:params:oauth:grant-type:device_code'})

    def receive(self, key, status, body):
        self.tick()
        if self.active is None or key != self.active:
            self._record('callback', 'stale')
            return False
        self._record('callback', 'accepted')
        self.active = None
        if type(status) is not int or status != 200 or type(body) is not dict:
            self._stop('failed')
        elif self.state == 'requesting':
            self._accept_grant(body)
        else:
            self._accept_poll(body)
        return True

    def _accept_grant(self, body):
        device = body.get('device_code')
        user = body.get('user_code')
        if (not secret_text(device) or len(device) != 40
                or not isinstance(user, str) or not re.fullmatch(r'[A-Z0-9]{4}-[A-Z0-9]{4}', user)
                or body.get('verification_uri') != 'https://github.com/login/device'
                or not positive_seconds(body.get('interval'), 86400)
                or not positive_seconds(body.get('expires_in'), 86400)
                or 'error' in body):
            self._stop('failed')
            return
        self._device = device
        self.interval = body['interval']
        # Conservative: issuance cannot precede sending the request.
        self.deadline = self.sent_at + body['expires_in']
        self.next_poll = self.clock() + self.interval
        self.state = 'waiting'
        self.tick()

    def _accept_poll(self, body):
        if 'error' in body:
            error = body['error']
            if 'access_token' in body or 'refresh_token' in body:
                self._stop('failed')
            elif error in ('authorization_pending', 'slow_down'):
                if error == 'slow_down':
                    updated = body.get('interval', self.interval + 5)
                    if not positive_seconds(updated, 86400):
                        self._stop('failed')
                        return
                    self.interval = max(self.interval + 5, updated)
                self.next_poll = self.clock() + self.interval
            else:
                state = 'denied' if error == 'access_denied' else 'failed'
                if error in ('expired_token', 'token_expired'):
                    state = 'expired'
                self._stop(state)
            return
        if (not secret_text(body.get('access_token'))
                or not secret_text(body.get('refresh_token'))
                or body.get('token_type') != 'bearer'
                or not positive_seconds(body.get('expires_in'), 31536000)
                or not positive_seconds(body.get('refresh_token_expires_in'), 31536000)):
            self._stop('failed')
            return
        # Only this explicit expiring-token model, not all OAuth variants.
        self._tokens = {key: body[key] for key in (
            'access_token', 'refresh_token', 'token_type', 'expires_in', 'refresh_token_expires_in')}
        self._device = None
        self._client = None
        self.state = 'authorized'

    def take_tokens(self):
        result = self._tokens
        self._tokens = None
        return result


class SessionDeviceFlow(DeviceFlow):
    """UNWIRED access-only session candidate. Never refreshes, saves or resumes.

    The caller must supply a process-local monotonic clock, drop raw response
    copies, and invalidate on close/unload. Python strings are not securely wiped.
    This is not the native network/UI adapter or a trusted-clock defense.
    """
    def __init__(self, clock):
        super().__init__(clock)
        self._access = None

    def _accept_poll(self, body):
        if 'error' in body:
            super()._accept_poll(body)
            return
        if (not secret_text(body.get('access_token'))
                or body.get('token_type') != 'bearer'
                or not positive_seconds(body.get('expires_in'), 31536000)):
            self._stop('failed')
            return
        # Deliberately do not copy or expose refresh credentials or other fields.
        self._access = body['access_token']
        self.deadline = self.sent_at + body['expires_in']
        self._device = self._client = None
        self.state = 'authorized'
        self.tick()

    def _stop(self, state):
        self._access = None
        super()._stop(state)

    def tick(self):
        super().tick()
        if self.state == 'authorized' and self.clock() >= self.deadline:
            self._stop('expired')

    def access_token(self):
        self.tick()
        return self._access if self.state == 'authorized' else None

    def take_tokens(self):
        # Disable the inherited pair handoff; this candidate has no refresh path.
        return None

    def start(self, client_id):
        # Terminal/start must release its access reference; no refresh path.
        self._access = None
        return super().start(client_id)


class RefreshFlow:
    """UNWIRED synthetic rotation/save handoff, not a protected storage adapter.

    saved() is an adapter acknowledgement, NOT proof of a disk write. An adapter
    must independently read back storage before calling it. No remote rollback.
    """
    @staticmethod
    def _valid_pair(body):
        return (type(body) is dict and 'error' not in body
                and secret_text(body.get('access_token'))
                and secret_text(body.get('refresh_token'))
                and body.get('token_type') == 'bearer'
                and positive_seconds(body.get('expires_in'), 31536000)
                and positive_seconds(body.get('refresh_token_expires_in'), 31536000))

    def __init__(self, clock, tokens):
        self.clock = clock
        self.state = 'idle' if self._valid_pair(tokens) else 'reauth_required'
        self._old = dict(tokens) if self.state == 'idle' else None
        self._candidate = None
        self._tokens = None
        self.active = None
        self.deadline = 0

    def start(self, client_id):
        if self.state != 'idle':
            return None
        if not secret_text(client_id) or len(client_id) > 256:
            self.cancel()
            return None
        self.active = (object(), 1)  # process-local identity; never serialized
        self.sent_at = self.clock()
        self.deadline = self.sent_at + 30
        self.state = 'refreshing'
        request = Request(self.active, 'refresh', {
            'client_id': client_id, 'grant_type': 'refresh_token',
            'refresh_token': self._old['refresh_token']})
        self._old = None
        return request

    def _expire(self):
        if self.state in ('refreshing', 'awaiting_save', 'ready') and self.clock() >= self.deadline:
            self.cancel()

    def receive(self, key, status, body):
        self._expire()
        if self.state != 'refreshing' or key != self.active:
            return False
        if type(status) is not int or status != 200 or not self._valid_pair(body):
            self.cancel()
            return True
        self._candidate = {name: body[name] for name in (
            'access_token', 'refresh_token', 'token_type', 'expires_in', 'refresh_token_expires_in')}
        # Conservative lifetime: never extend from response/save latency.
        self.deadline = min(self.deadline, self.sent_at + body['expires_in'],
                            self.sent_at + body['refresh_token_expires_in'])
        self.state = 'awaiting_save'
        return True

    def cancel(self):
        self._old = self._candidate = self._tokens = self.active = None
        self.state = 'reauth_required'

    def pending_save(self, key):
        self._expire()
        if self.state == 'awaiting_save' and key == self.active:
            return dict(self._candidate)
        return None

    def saved(self, key, success):
        self._expire()
        if self.state != 'awaiting_save' or key != self.active:
            return False
        self._tokens = self._candidate if success is True else None
        self._candidate = None
        self.active = None
        self.state = 'ready' if success is True else 'reauth_required'
        return True

    def take_tokens(self):
        self._expire()
        result = self._tokens
        self._tokens = None
        return result
