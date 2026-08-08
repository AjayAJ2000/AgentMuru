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


def test_runtime_streams_trace_span_events_to_workspace() -> None:
    import asyncio

    from agentmuru import Agent, Application, FakeModel, Runtime
    from agentmuru.core.events import EventType

    async def run_agent():
        runtime = Runtime(
            Application(agent=Agent(name="traced", instructions="", model=FakeModel.responses("ok")))
        )
        session = runtime.create_session()
        run = await runtime.submit(session.id, "trace this")
        await runtime.wait(run.id)
        return session.events

    events = asyncio.run(run_agent())
    types = [event.type for event in events]
    assert EventType.TRACE_SPAN_STARTED in types
    assert EventType.TRACE_SPAN_COMPLETED in types
