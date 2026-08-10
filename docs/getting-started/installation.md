# Install AgentMuru

Install the verified AgentMuru 0.2 distribution, then confirm that the CLI and bundled
Workspace are available.

## Prerequisites

- Python 3.10 or later;
- a terminal with permission to create a virtual environment;
- network access to PyPI.

## Install the verified release

Create and activate a virtual environment if your project does not already use one:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Install the pinned release and run the local diagnostic:

```powershell
python -m pip install agentmuru==0.2.0
muru doctor
```

`muru doctor` verifies the Python runtime and bundled Workspace assets. Resolve any failed
check before starting the server.

## Continue with a local agent

Follow the [five-minute local quickstart](quickstart.md) to scaffold and run an agent that
does not require provider credentials.

## Contribute from source

Editable installation is for contributors, not the primary product path:

```powershell
git clone https://github.com/AjayAJ2000/AgentMuru.git
cd AgentMuru
python -m pip install -e ".[dev,docs]"
python -m pytest -q
```

Use the pinned PyPI release when evaluating the product or validating deployment behavior.
