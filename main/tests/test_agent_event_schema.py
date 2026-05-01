from backend.process_compliance.agents.event_stream import create_agent_event


def test_agent_event_json_serializable():
    event = create_agent_event(
        run_id="run_test",
        type="agent_message_completed",
        agent_name="check_agent",
        content="CONSENSUS: YES\nCONFIDENCE: 0.82",
        payload={"confidence": 0.82},
    )
    raw = event.model_dump_json()
    assert '"run_id":"run_test"' in raw
    assert event.event_id.startswith("evt_")
    assert event.timestamp


