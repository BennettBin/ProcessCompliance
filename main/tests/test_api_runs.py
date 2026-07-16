from fastapi.testclient import TestClient

from backend.main import app


def test_api_runs_create_and_stream():
    client = TestClient(app)

    create_resp = client.post(
        "/api/runs",
        json={
            "event_log_path": "dataset/new_data/not_exists.csv",
            "running_trace_path": "dataset/running_trace/not_exists.csv",
            "dataset_name": "BPIC20_D",
        },
    )
    # create run should be successful even if data is missing; the run will fail in controlled way later.
    assert create_resp.status_code == 200
    payload = create_resp.json()
    assert "run_id" in payload
    run_id = payload["run_id"]

    stream_resp = client.get(f"/api/runs/{run_id}/stream")
    assert stream_resp.status_code == 200
    assert stream_resp.headers.get("content-type", "").startswith("text/event-stream")

