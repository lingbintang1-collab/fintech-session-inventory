from src.session_inventory import PaymentEvent, sign_out_other_sessions


class FakeClient:
    def __init__(self):
        self.revoked = []

    def list_sessions(self, user_id):
        return [{"id": "current", "active": True}, {"id": "tablet", "active": True}, {"id": "old", "active": False}]

    def revoke_session(self, session_id):
        self.revoked.append(session_id)


def test_only_active_other_device_is_revoked():
    client = FakeClient()
    result = sign_out_other_sessions(client, "user-7", "current", PaymentEvent("payment_review", 1250, "USD", "current"))
    assert client.revoked == ["tablet"]
    assert result.revoked_session_ids == ("tablet",)
    assert result.payment_event.amount == 1250
