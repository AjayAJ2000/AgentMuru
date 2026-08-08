from agentmuru import Agent, Application, FakeModel, tool


@tool(permission="knowledge.read")
def search_notes(query: str) -> dict[str, str]:
    """Search the application's local notes."""
    return {"query": query, "result": "Add your data integration here."}


agent = Agent(
    name="assistant",
    description="A governed local assistant",
    instructions="Answer clearly and use tools when they improve the result.",
    model=FakeModel.responses("AgentMuru is ready. Configure a provider to begin."),
    tools=(search_notes,),
    permissions=frozenset({"knowledge.read"}),
)

application = Application(agent=agent, title="{{APP_NAME}}")
