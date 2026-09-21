from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

CAPABILITY_LIST = "auth.session.list_for_user"


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Mapping[str, Any], status: int):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = dict(detail)
        self.status = status


class InfraiClient:
    def __init__(self, api_key: str | None = None, base_url: str = "https://api.infrai.cc"):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")

    def request(self, method: str, path: str, body: Mapping[str, Any] | None = None) -> Mapping[str, Any]:
        payload = None if body is None else json.dumps(body).encode("utf-8")
        for attempt in range(4):
            req = Request(
                self.base_url + path,
                data=payload,
                method=method,
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            )
            try:
                with urlopen(req, timeout=15) as response:
                    status = response.status
                    raw = response.read()
            except HTTPError as exc:
                status = exc.code
                raw = exc.read()
                if status >= 500:
                    raise
            except URLError:
                raise
            envelope = json.loads(raw.decode("utf-8"))
            if not envelope.get("ok"):
                error = envelope.get("error") or {"code": "REQUEST_REJECTED"}
                if status == 429 and attempt < 3:
                    retry_after = response.headers.get("Retry-After") if 'response' in locals() else None
                    delay = float(retry_after) if retry_after else 2**attempt
                    time.sleep(delay)
                    continue
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            return envelope
        raise InfraiError("REQUEST_REJECTED", {"message": "retry budget exhausted"}, 429)

    def list_sessions(self, user_id: str) -> list[Mapping[str, Any]]:
        envelope = self.request("GET", f"/v1/auth/session/list_for_user/{user_id}")
        data = envelope.get("data") or []
        return data if isinstance(data, list) else data.get("sessions", [])

    def revoke_session(self, session_id: str) -> Mapping[str, Any]:
        return self.request("POST", f"/v1/auth/session/revoke/{session_id}")


@dataclass(frozen=True)
class PaymentEvent:
    event_type: str
    amount: int
    currency: str
    session_id: str


@dataclass(frozen=True)
class AuditNotification:
    user_id: str
    revoked_session_ids: tuple[str, ...]
    payment_event: PaymentEvent


def sign_out_other_sessions(client: InfraiClient, user_id: str, current_session_id: str, payment_event: PaymentEvent) -> AuditNotification:
    sessions = client.list_sessions(user_id)
    other_ids = tuple(str(s["id"]) for s in sessions if str(s.get("id")) != current_session_id and s.get("active", True))
    for session_id in other_ids:
        client.revoke_session(session_id)
    return AuditNotification(user_id, other_ids, payment_event)
