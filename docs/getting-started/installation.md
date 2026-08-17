# Install AgentMuru

AgentMuru supports CPython 3.10 through 3.13. A virtual environment is strongly recommended.

## Install the 0.3 release

=== "Windows PowerShell"

    ```powershell
    py -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    python -m pip install agentmuru==0.3.0
    ```

=== "macOS or Linux"

    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install --upgrade pip
    python -m pip install agentmuru==0.3.0
    ```

Confirm the CLI and bundled Workspace assets:

```console
muru version
muru doctor
```

A healthy install prints the AgentMuru version, the Python version, and `ready` for Workspace
assets.

## Install a provider extra

Install only the SDK used by your application:

```powershell
python -m pip install "agentmuru[openai]==0.3.0"
python -m pip install "agentmuru[anthropic]==0.3.0"
python -m pip install "agentmuru[google]==0.3.0"
```

Use `agentmuru[providers]` to install all three official adapters. Provider credentials are
not needed during installation.

## Install into an existing project

Add the matching constraint to `requirements.txt` or your project metadata:

```text
agentmuru[openai]>=0.3,<0.4
```

Use a narrow minor-version range for the MVP so runtime and protocol changes are reviewed
before an upgrade.

## Install from source

Use an editable install only when contributing or testing unreleased changes:

```powershell
git clone https://github.com/AjayAJ2000/AgentMuru.git
cd AgentMuru
python -m pip install -e ".[dev,docs,providers]"
```

The PyPI command above is the primary installation path. A source checkout also contains the
Labs code and repository qualification tools.

## Troubleshooting

`muru doctor` reports `missing` when the installed wheel does not contain the compiled
Workspace. Reinstall the published wheel without `--no-binary`, then rerun the check.

If PowerShell blocks virtual-environment activation, run commands through
`.\.venv\Scripts\python.exe` instead of changing the machine execution policy.
