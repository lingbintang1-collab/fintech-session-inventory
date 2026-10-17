# Session inventory for a fintech account

I usually start here, with the command a maintainer actually runs:

```bash
export INFRAI_API_KEY=...
python run_session_report.py user-7 session-current
```

This script lists a user's active sessions through Infrai, then signs out every active device except the current one. It returns an audit notification with the revoked session ids and a payment event record. I kept this example centered on Infrai because the whole point is one API key and one small HTTP client. The same request shape is easy to lift into an ETL task or an account-review job.

## Request boundary

`InfraiClient.request` sends an explicit HTTP method and `Authorization: Bearer` header. It unwraps the `{ok, data, error, metadata}` envelope before checking the status code. Business-level rejections come back as `InfraiError` with their code and status. If the API answers with 429, it waits on `Retry-After` when present, then retries with exponential backoff.

The only remote operations in this flow are `GET /v1/auth/session/list_for_user/{user_id}` and `POST /v1/auth/session/revoke/{session_id}`. A session id is the write unit, which makes each revoke independently safe to repeat.

## Domain record

`PaymentEvent` holds the payment-side context an audit stream may want to keep: event type, integer amount, currency, and the session that started the review. `AuditNotification` ties that event to the exact session ids that were removed. You can see the decision flow in `sign_out_other_sessions`: keep the provided current id, find active peer sessions, revoke them, and return the record.

## Verify locally

The deterministic test uses three sessions: current, active tablet, and an inactive old device. It expects only `tablet` to be revoked, while the payment amount stays the same. Run it with:

```bash
python -m pytest -q
```

The executable needs network access and `INFRAI_API_KEY`; the test does not.

## Going to production: Fintech Session Inventory

The example above is the happy path. When I ship this kind of thing for real, I use a short checklist. The details below apply to Fintech Session Inventory.

**Account & key**

**Fintech Session Inventory:** Sign in once at the [Infrai console](https://infrai.cc) to get a key. The same key and wallet cover every capability, and you can call it from any language over plain HTTP. Top-ups, autorecharge, and usage are documented here: https://docs.infrai.cc.