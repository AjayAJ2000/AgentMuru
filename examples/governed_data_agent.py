from agentmuru import Agent, Application, FakeModel, tool
from agentmuru.models import ModelCompleted, TextDelta, ToolCall


@tool(permission="database.read", description="Read a customer status")
def read_customer(customer_id: str) -> dict[str, str]:
    return {"customer_id": customer_id, "status": "active"}


@tool(
    permission="database.write",
    approval="required",
    risk="high",
    side_effects=True,
    description="Change a customer status",
)
def update_customer(customer_id: str, status: str) -> dict[str, str]:
    return {"customer_id": customer_id, "status": status}


model = FakeModel.turns(
    [
        ToolCall(
            id="update-1",
            name="update_customer",
            arguments={"customer_id": "C-100", "status": "review"},
        ),
        ModelCompleted(),
    ],
    [TextDelta("The approved customer update completed."), ModelCompleted()],
)

agent = Agent(
    name="customer-ops",
    instructions="Use governed data tools and explain every mutation.",
    model=model,
    tools=(read_customer, update_customer),
    permissions=frozenset({"database.read", "database.write"}),
)

application = Application(agent=agent, title="Governed Data Agent")


if __name__ == "__main__":
    application.run()
