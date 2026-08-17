# Quickstart

This path creates a working AgentMuru application with deterministic output. It does not use
an API key or make a model request over the network.

## Check the installation

```powershell
muru doctor
```

Both Python and Workspace assets should report `ready`.

## Create the starter

```powershell
muru init my-agent --name "My first AgentMuru app"
cd my-agent
```

The directory contains:

- `app.py`, which exports `application`.
- `requirements.txt`, constrained to AgentMuru 0.3.
- `README.md`, with the exact run command.

The default model is `FakeModel`. Open `app.py` and change its fixed response if you want a
different local result.

## Start the runtime

```powershell
python -m pip install -r requirements.txt
muru run app:application
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in a browser.

## Send the first message

Create a session in the left rail, enter a message, and submit it. The fixed assistant reply
appears while the Timeline records the run, model request, streamed content, and completion.

### What you should see

- A session remains available in the session list.
- The conversation contains your message and the deterministic assistant reply.
- Timeline entries have a stable sequence and event type.
- The run ends in `completed`.

Refresh the page. The in-memory starter remains useful for one process lifetime. Add
[SQLite persistence](../operations/sqlite.md) when sessions must survive a restart.

## Stop the server

Return to the terminal and press `Ctrl+C`.

## Next steps

- [Understand the Workspace](workspace-tour.md)
- [Use a real model](real-model.md)
- [Create a governed tool](../cookbook/governed-tools.md)
