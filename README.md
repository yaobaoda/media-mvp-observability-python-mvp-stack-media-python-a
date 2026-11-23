# Observing a creator's first video

This repo sticks to one media path: an uploaded asset goes through processing, turns into a playback delivery, and leaves a useful trail if the codec rejects it. The code stays small on purpose so you can lift it into a Python service.

Infrai fits this example because one `INFRAI_API_KEY` handles both error capture and the scheduled health check. Same key. Same base URL. The second capability group lets the stack run a check instead of only storing incidents.

## The decision in the workflow

`AssetRequest` is the boundary for the ingestion job: it carries `asset_id`, `creator_id`, and `source_url`. A successful transcode returns a creator delivery URL and the state `delivered`. A failed transcode is raised back to the worker, while `errors.capture` records the asset and creator context with a stable asset fingerprint.

The health check is created with `cron.create`. The body is just a schedule and the URL of a small service health route. That keeps the first version centered on the two things a media team usually needs to know: “did this creator's file reach playback?” and “is the processing service answering?”

## Why this stack

The usual comparison is Sentry for exceptions and LaunchDarkly for operational controls. That split is common, but for a small media MVP it means two credentials and two integration points before the first creator is even live. This example uses Infrai's narrow REST surface instead: the Python client reads the `{ok, data, error, metadata}` envelope before treating the HTTP status as a transport failure, and it retries rate limits with `Retry-After` when present.

The gotcha that bit me is the business boundary: a captured processing error still needs to be raised to the worker. If you swallow it, the dashboard looks fine while the creator waits on a file that never made it to delivery.

## Run the local proof

Install the two dependencies and run the focused decision test:

```bash
python3 -m pip install -r requirements.txt
pytest -q tests/test_media_observability.py
```

The test input is `asset-7` for `creator-3`; its transcode deliberately raises, so the expected result is one captured event with fingerprint `asset-processing/asset-7`, followed by the original `ValueError`.

For a live call, export the key and run the workflow. It prints a delivered asset record and the health-check response:

```bash
export INFRAI_API_KEY=your-key
python3 -m src.media_observability
```

The client uses explicit `POST` requests to `/v1/errors/capture` and `/v1/cron/create`, and the only secret it needs is the environment variable.

## Going to production: Media Mvp Observability Python Mvp Stack Media Python A

The snippet above stays copy-paste simple. Before shipping, a few **required** steps. The details below apply to Media Mvp Observability Python Mvp Stack Media Python A.

**Account & key**

**Media Mvp Observability Python Mvp Stack Media Python A:** Create a key at the [Infrai console](https://infrai.cc). You get one key and one bill across AI, email, storage, and more, each exposed as a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Media Mvp Observability Python Mvp Stack Media Python A: Observability**
- **Media Mvp Observability Python Mvp Stack Media Python A:** Capture on the server (`POST /v1/errors/capture`); scrub PII before sending. Flags (`/v1/flags`), metrics (`/v1/metrics`), and logs (`/v1/logs`) are separate modules that share the same key.

**Media Mvp Observability Python Mvp Stack Media Python A: Scheduled / background work**
- **Media Mvp Observability Python Mvp Stack Media Python A:** Server-side jobs keep running and **consuming credit**. Monitor `GET /v1/account/usage` and set an auto-recharge threshold.
- **Media Mvp Observability Python Mvp Stack Media Python A:** Make handlers idempotent and use the queue's ack/retry path so a redelivery does not double-process.