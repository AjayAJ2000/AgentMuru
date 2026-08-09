from __future__ import annotations

import importlib.util
import json
import os

from agentmuru import Agent, Application, FakeModel


application = Application(
    agent=Agent(
        name="databricks-inspector",
        instructions="Check configuration before using optional Databricks adapters.",
        model=FakeModel.responses("Databricks configuration inspected without network access."),
    ),
    title="Databricks Agent",
)


def main() -> dict[str, bool]:
    try:
        sdk_installed = importlib.util.find_spec("databricks.sdk") is not None
    except ModuleNotFoundError:
        sdk_installed = False
    return {
        "host_configured": bool(os.getenv("DATABRICKS_HOST")),
        "sdk_installed": sdk_installed,
        "network_attempted": False,
    }


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, sort_keys=True))

