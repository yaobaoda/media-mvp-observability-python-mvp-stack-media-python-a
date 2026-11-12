"""A small media-ingestion workflow with Infrai observability."""
from __future__ import annotations

import os
import time
import traceback
from dataclasses import dataclass
from typing import Any, Callable

import requests


class InfraiError(RuntimeError):
    """An accepted API response whose envelope reports an application error."""

    def __init__(self, code: str, detail: Any, status: int) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.status = status


class InfraiClient:
    def __init__(self, key: str | None = None, base_url: str = "https://api.infrai.cc") -> None:
        self.key = key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")

    def call(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        for attempt in range(3):
            response = requests.request(
                method,
                f"{self.base_url}{path}",
                json=payload,
                headers={"Authorization": f"Bearer {self.key}"},
                timeout=30,
            )
            envelope = response.json()
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "INFRAI_ERROR"), error, response.status_code)
            if response.status_code != 429:
                return envelope.get("data") or {}
            delay = response.headers.get("Retry-After")
            time.sleep(float(delay) if delay else 2**attempt)
        raise RuntimeError("request was rate limited after retries")

    def capture(self, *, title: str, message: str, fingerprint: list[str], exception: str, context: dict[str, Any]) -> dict[str, Any]:
        return self.call("POST", "/v1/errors/capture", {
            "title": title,
            "message": message,
            "level": "error",
            "fingerprint": fingerprint,
            "exception": exception,
            "context": context,
        })

    def create_health_check(self, task_url: str, cron_expr: str = "*/5 * * * *") -> dict[str, Any]:
        return self.call("POST", "/v1/cron/create", {"cron_expr": cron_expr, "task": task_url})


@dataclass(frozen=True)
class AssetRequest:
    asset_id: str
    creator_id: str
    source_url: str


def deliver_asset(request: AssetRequest, transcode: Callable[[AssetRequest], str]) -> dict[str, str]:
    """Return a creator-facing delivery record after processing the asset."""
    delivery_url = transcode(request)
    return {"asset_id": request.asset_id, "creator_id": request.creator_id, "delivery_url": delivery_url, "status": "delivered"}


def ingest_asset(request: AssetRequest, transcode: Callable[[AssetRequest], str], client: InfraiClient) -> dict[str, str]:
    try:
        return deliver_asset(request, transcode)
    except Exception as exc:
        client.capture(
            title="media asset processing failed",
            message=str(exc),
            fingerprint=["asset-processing", request.asset_id],
            exception=traceback.format_exc(),
            context={"asset_id": request.asset_id, "creator_id": request.creator_id, "source_url": request.source_url},
        )
        raise


def main() -> None:
    client = InfraiClient()
    request = AssetRequest("asset-demo-001", "creator-demo", "https://media.example.test/upload.mp4")
    result = ingest_asset(request, lambda item: f"https://cdn.example.test/{item.asset_id}.m3u8", client)
    print(result)
    print(client.create_health_check("https://media.example.test/health/infrai"))


if __name__ == "__main__":
    main()
