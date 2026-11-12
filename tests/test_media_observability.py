from src.media_observability import AssetRequest, InfraiClient, ingest_asset


def test_processing_failure_is_captured_and_not_delivered() -> None:
    captured = []

    class RecordingClient(InfraiClient):
        def __init__(self) -> None:
            pass

        def capture(self, **payload):
            captured.append(payload)
            return {}

    request = AssetRequest("asset-7", "creator-3", "https://upload.test/7.mp4")

    def transcode(_request):
        raise ValueError("codec rejected the source")

    try:
        ingest_asset(request, transcode, RecordingClient())
    except ValueError:
        pass
    else:
        raise AssertionError("processing should remain failed")

    assert captured[0]["fingerprint"] == ["asset-processing", "asset-7"]
    assert captured[0]["context"]["creator_id"] == "creator-3"
