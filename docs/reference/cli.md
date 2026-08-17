# CLI reference

The `muru` command is installed with the core package.

## `muru version`

Print the installed package identity and version.

```console
muru version
```

## `muru doctor`

Check the current Python version and bundled Workspace assets. The command exits nonzero when a
required check is missing.

```console
muru doctor
```

## `muru init`

Create a minimal project in an empty or missing directory.

```console
muru init PATH [--name TEXT] [--provider fake|openai|anthropic|google]
```

`--name` defaults to `My AgentMuru App`. `--provider` defaults to `fake`. The provider choice
changes the import, model constructor, requirement extra, and credential note. It never writes a
credential.

The command refuses to overwrite a nonempty directory.

## `muru dev`

Run an application with source reload:

```console
muru dev [TARGET] [--host TEXT] [--port INTEGER]
```

`TARGET` defaults to `app:application`, host to `127.0.0.1`, and port to `8000`.

Reload mode stores the target in `AGENTMURU_APP` so Uvicorn can import the factory after a source
change. Use it only for local development.

## `muru run`

Run an application without source reload:

```console
muru run [TARGET] [--host TEXT] [--port INTEGER]
```

`TARGET` defaults to `app:application`, host to `0.0.0.0`, and port to `8000`.

## Application targets

A target uses `module:attribute` syntax. The module must be importable from the current Python
environment, and the attribute must be an `agentmuru.Application`.

```python
# app.py
application = Application(agent=agent, title="Support")
```

```console
muru run app:application
```

Invalid syntax, a missing module or attribute, and a value that is not an `Application` fail
before the server starts.
