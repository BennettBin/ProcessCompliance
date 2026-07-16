from backend.process_compliance.data.validation import validate_running_trace


def test_data_validation_missing_file():
    result = validate_running_trace("dataset/running_trace/not_found.csv")
    assert result.valid is False
    assert any("does not exist" in e for e in result.errors)


