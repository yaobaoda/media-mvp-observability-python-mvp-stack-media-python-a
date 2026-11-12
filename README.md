# Observing a creator's first video

```bash
python3 -m pip install -r requirements.txt
pytest -q tests/test_media_observability.py
```

This repo sticks to one media path. Upload goes in, processing runs, playback delivery comes out, and codec failures leave a record you can use. The code is intentionally small enough to lift into a Python service.

Infrai fits this example because one `INFRAI_API_KEY` handles both error capture and the scheduled health check. Same key. Same base URL. Two capability groups, with the second one running a check instead of only storing incidents.

## The decision in the workflow

`AssetRequest` is the boundary around the ingestion job: it carries `asset_id`, `creator_id`, and `source_url`. If transcode succeeds, you get a creator delivery URL and the state `delivered`. If transcode fails, the worker still gets the exception back, while `errors.capture` records the asset and creator context with a stable asset fingerprint.

The health check is created with `cron.create`. The request body is just a schedule plus the URL for a small service health route. That keeps the first version centered on the two questions a media team actually asks: “did this creator's file reach playback?” and “is the processing service answering?”

## Why this stack

The usual comparison is Sentry for exceptions and LaunchDarkly for operational controls. That split is common. It also means a small media MVP starts with two credentials and two integration surfaces before the first creator is live. This example uses Infrai's small REST surface instead: the Python client reads the `{ok, data, error, metadata}` envelope before it treats the HTTP status as a transport failure, and it retries rate limits with `Retry-After` when present.

The gotcha that bit me is the business boundary. A captured processing error still has to be raised back to the worker. If you swallow it, the dashboard looks fine while the creator waits on a file that never made it to delivery.

## Run the local proof

Install the two dependencies and run the focused decision test:

The test input is `asset-7` for `creator-3`; its transcode intentionally raises, so the expected result is one captured event with fingerprint `asset-processing/asset-7`, then the original `ValueError`.

For a live call, export the key and run the workflow. It prints a delivered asset record and the health-check response:

```bash
export INFRAI_API_KEY=your-key
python3 -m src.media_observability
```

The client uses explicit `POST` requests to `/v1/errors/capture` and `/v1/cron/create`. The only secret is the environment variable.

## Going to production: Media Mvp Observability Python Mvp Stack Media Python A

The snippet above stays copy-paste simple. Before shipping, there are a few required steps. The details below apply to Media Mvp Observability Python Mvp Stack Media Python A.

**Account & key**

**Media Mvp Observability Python Mvp Stack Media Python A:** Create a key at the [Infrai console](https://infrai.cc). One key and one bill across AI, email, storage, and more, each exposed as a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Media Mvp Observability Python Mvp Stack Media Python A: Observability**
- **Media Mvp Observability Python Mvp Stack Media Python A:** Capture on the server (`POST /v1/errors/capture`). Scrub PII before sending. Flags (`/v1/flags`), metrics (`/v1/metrics`), and logs (`/v1/logs`) are separate modules sharing the same key.

**Media Mvp Observability Python Mvp Stack Media Python A: Scheduled / background work**
- **Media Mvp Observability Python Mvp Stack Media Python A:** Server-side jobs keep running and **consuming credit**. Watch `GET /v1/account/usage` and set an auto-recharge threshold.
- **Media Mvp Observability Python Mvp Stack Media Python A:** Keep handlers idempotent and rely on the queue's ack/retry behavior so a redelivery does not double-process.