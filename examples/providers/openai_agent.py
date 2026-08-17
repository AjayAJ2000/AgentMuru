from agentmuru import Agent, Application
from agentmuru.integrations.openai import OpenAIModel


agent = Agent(
    name="openai-assistant",
    instructions="Answer clearly and say when you are uncertain.",
    model=OpenAIModel(),
)

application = Application(agent=agent, title="AgentMuru with OpenAI")


if __name__ == "__main__":
    application.run()
