from agentmuru import Agent, Application
from agentmuru.integrations.google import GoogleGenAIModel


agent = Agent(
    name="google-assistant",
    instructions="Answer clearly and say when you are uncertain.",
    model=GoogleGenAIModel(),
)

application = Application(agent=agent, title="AgentMuru with Google")


if __name__ == "__main__":
    application.run()
