from agentmuru import Agent, Application
from agentmuru.integrations.anthropic import AnthropicModel


agent = Agent(
    name="anthropic-assistant",
    instructions="Answer clearly and say when you are uncertain.",
    model=AnthropicModel(),
)

application = Application(agent=agent, title="AgentMuru with Anthropic")


if __name__ == "__main__":
    application.run()
