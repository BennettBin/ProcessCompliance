from backend.process_compliance.online.result_schema import (
    AnalysisResult,
    AgentReview,
    ComplianceResult,
    PredictionResult,
)


def test_result_schema_json_serializable():
    obj = AnalysisResult(
        run_id="test_run",
        status="success",
        dataset_name="BPIC20_D",
        event_log_path="dataset/new_data/BPIC20_D.csv",
        running_trace_path="dataset/running_trace/BPIC20_D_trace.csv",
        current_trace=[],
        prediction=PredictionResult(remaining_time_unit="hours"),
        compliance=ComplianceResult(current_status="unknown", future_risk="unknown"),
        agent_review=AgentReview(),
    )
    payload = obj.model_dump_json()
    assert '"run_id":"test_run"' in payload


