from agentmuru.observability import Tracer, Usage


def test_tracer_records_nested_spans_and_usage() -> None:
    tracer = Tracer()
    trace = tracer.start_trace(session_id="session-1", run_id="run-1", name="agent")
    span = tracer.start_span(trace.id, name="model", kind="model")
    tracer.record_usage(trace.id, Usage(input_tokens=5, output_tokens=3, cost=0.01))
    tracer.finish_span(span.id)
    tracer.finish_trace(trace.id)

    assert trace.status == "completed"
    assert trace.spans[0].duration_ms is not None
    assert trace.usage.total_tokens == 8
    assert trace.usage.cost == 0.01
