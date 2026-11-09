# SPDX-License-Identifier: GPL-2.0-or-later
"""Access-only, process-local device session. No storage, refresh or network.

The controller owns monotonic timers and teardown. Real sign-in remains gated by
registration and diagnostic safety. References are dropped, not securely erased.
"""
from dataclasses import dataclass, field
import re


def positive_seconds(value, maximum):
    return type(value) is int and 0 < value <= maximum


def secret_text(value):
    return isinstance(value, str) and 0 < len(value) <= 8192 and all(
        32 < ord(char) < 127 for char in value)


@dataclass(frozen=True)
class Request:
    key: tuple
    endpoint: str
    payload: dict = field(repr=False)


class SessionDeviceFlow:
    """One access-only session; no remembered credentials or pair handoff."""
    def __init__(self, clock):
        self.clock = clock
        self.state = 'idle'
        self.generation = self.sequence = 0
        self.active = None
        self._access = self._tokens = self._client = self._device = None
        self.user_code = self.verification_uri = None
        self.interval = self.deadline = self.next_poll = 0
        self.sent_at = self.request_deadline = 0
        self._events = []

    def _record(self, event, label):
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
        self.request_deadline = self.sent_at + 30
        self._record('request', endpoint)
        return Request(self.active, endpoint, payload)

    def start(self, client_id):
        self._stop('idle')
        if not secret_text(client_id) or len(client_id) > 256:
            self._stop('unconfigured')
            return None
        self._client = client_id
        self.state = 'requesting'
        return self._request('device', {'client_id': client_id, 'scope': 'offline_access'})

    def _stop(self, state):
        self.generation += 1
        self.state = state
        self.active = self._access = self._tokens = self._device = self._client = None
        self.user_code = self.verification_uri = None
        self._record('state', state)

    def cancel(self):
        self._stop('cancelled')

    def tick(self):
        if self.state in ('waiting', 'authorized') and self.clock() >= self.deadline:
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
        device, user = body.get('device_code'), body.get('user_code')
        if (not secret_text(device) or len(device) != 40
                or not isinstance(user, str) or not re.fullmatch(r'[A-Z0-9]{4}-[A-Z0-9]{4}', user)
                or body.get('verification_uri') != 'https://github.com/login/device'
                or not positive_seconds(body.get('interval'), 86400)
                or not positive_seconds(body.get('expires_in'), 86400)
                or 'error' in body or 'access_token' in body or 'refresh_token' in body):
            self._stop('failed')
            return
        self._device = device
        self.user_code, self.verification_uri = user, body['verification_uri']
        self.interval = body['interval']
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
        if (not secret_text(body.get('access_token')) or body.get('token_type') != 'bearer'
                or not positive_seconds(body.get('expires_in'), 31536000)):
            self._stop('failed')
            return
        self._access = body['access_token']
        self.deadline = self.sent_at + body['expires_in']
        self._device = self._client = self.user_code = self.verification_uri = None
        self.state = 'authorized'
        self.tick()

    def access_token(self):
        self.tick()
        return self._access if self.state == 'authorized' else None

    def take_tokens(self):
        return None
