# Run verified local models

The native AgentMuru source preview contains the trust, installation, supervision, and
decision layers for small GGUF models. The current signed catalog is an empty bootstrap:
no public model is offered until its clean-machine and named reference-device reports are
published.

## Check the machine first

```powershell
muru doctor --json
```

AgentMuru classifies the operating system, architecture, CPU flags, memory, and free cache
storage without downloading or executing anything. Catalog compatibility is filtered from
this profile before a runtime binary can start.

## Inspect installed models

```powershell
muru models list
muru models list --json
```

Models come only from a signed catalog. Each entry pins an immutable upstream revision,
HTTPS URL, declared byte size, SHA-256 digest, GGUF format, runtime variants, memory floor,
and license metadata.

## Install a catalog artifact

When a qualified artifact appears in the signed catalog, install it by ID:

```powershell
muru models install <artifact-id>
```

The download is streamed into a partial file, capped at the declared size, hashed, flushed,
and atomically promoted only after the digest matches. Cancellation, an oversized response,
or a digest mismatch leaves no promoted model.

For a gated artifact, review the displayed URL and record acceptance of that exact license:

```powershell
muru models install <artifact-id> --accept-license <license-id>
```

JSON mode never prompts. It returns the stable `license_required` code until the exact
`--accept-license` value is supplied.

## Understand runtime isolation

AgentMuru selects the highest-ranked llama.cpp binary whose required CPU flags are a subset
of the hardware profile. It verifies the binary manifest before execution, binds the child
to `127.0.0.1`, supplies a random bearer token through `LLAMA_API_KEY`, waits for authenticated
health, and owns the Windows process through a Job Object.

On an 8 GB profile, the default residency budget is one model. AgentMuru can unload an idle
specialist before loading another, but never evicts a model with an active lease.

## Understand decision constraints

Local inference is used for bounded action decisions, not unrestricted shell text. Requests
use temperature zero, a generated grammar, and a small output ceiling. Responses must be one
JSON object and are validated again against the declared action and argument types. AgentMuru
does not repair Markdown fences or accept undeclared actions.

Events retain model ID, digest, latency, token counts, and decision status. They exclude the
bearer token, complete prompt, raw server error, and unredacted arguments.

## Check qualification status

See [Current capabilities and limits](../integration-status.md) before treating a model and
runtime pair as supported. Deterministic fixture coverage is not a substitute for a report
from the machine tier you plan to use.
