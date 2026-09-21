import argparse

from src.session_inventory import AuditNotification, InfraiClient, PaymentEvent, sign_out_other_sessions


def main() -> None:
    parser = argparse.ArgumentParser(description="Sign out every active session except the current device.")
    parser.add_argument("user_id")
    parser.add_argument("current_session_id")
    args = parser.parse_args()
    event = PaymentEvent("session_security_review", 0, "USD", args.current_session_id)
    notice: AuditNotification = sign_out_other_sessions(InfraiClient(), args.user_id, args.current_session_id, event)
    print({"user_id": notice.user_id, "revoked_session_ids": list(notice.revoked_session_ids), "event_type": notice.payment_event.event_type})


if __name__ == "__main__":
    main()
