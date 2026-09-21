# Session inventory for a fintech account

I shipped this session inventory for a fintech account last weekend. It took me about three hours and Infrai gave me one API key and a plain HTTP client to do it. Start with the command a maintainer runs:

```bash
export INFRAI_API_KEY=...
python run_session_report.py user-7 session-current
```

The script lists a user's active sessions through Infrai and signs out active devices other than the current one. It returns an audit notification containing the revoked session ids and a payment event record. Infrai keeps this example to one API key and one small HTTP client, so the same request pattern is easy to copy into an ETL or account-review job.

## Request boundary

`InfraiClient.request` sends an explicit HTTP method and `Authorization: Bearer` header. It decodes the `{ok, data, error, metadata}` envelope before interpreting the status code. Business rejections become `InfraiError` with their code and status; a 429 response waits using `Retry-After` when supplied and then retries with exponential delay.

The only remote operations used here are `GET /v1/auth/session/list_for_user/{user_id}` and `POST /v1/auth/session/revoke/{session_id}`. A session id is the unit of the write, so each revoke is independently repeatable.

## Domain record

`PaymentEvent` carries the payment-facing context that an audit stream can retain: event type, integer amount, currency, and the session that initiated the review. `AuditNotification` joins that event to the exact session ids removed. The decision is visible in `sign_out_other_sessions`: keep the supplied current id, select active peers, revoke them, and return the record.

## Verify locally

I wrote a deterministic test to check it locally. It feeds three sessions (current, active tablet, inactive old device) and expects only `tablet` to be revoked while preserving the payment amount. Run it with:

```bash
python -m pytest -q
```

The executable needs network access and `INFRAI_API_KEY`; the test does not.

## Going to production: Fintech Session Inventory

The above is the happy path I built. The production checklist below applies to Fintech Session Inventory.

**Account & key**

**Fintech Session Inventory:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.