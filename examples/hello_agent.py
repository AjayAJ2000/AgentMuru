from agentmuru import Agent, Application, FakeModel


agent = Agent(
    name="hello",
    instructions="Welcome the user and explain that this is a deterministic local example.",
    model=FakeModel.responses("Hello. AgentMuru is running locally."),
)

application = Application(agent=agent, title="Hello AgentMuru")


if __name__ == "__main__":
    application.run()
