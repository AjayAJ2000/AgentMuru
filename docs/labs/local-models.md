# Local models

The native preview contains trust, installation, supervision, and decision layers for small
GGUF models. The signed catalog is an empty bootstrap, so no public artifact is currently
offered.

No catalog model is reference-device-qualified.

## Profile before selection

```powershell
muru doctor --json
```

The native command profiles operating system, architecture, CPU flags, memory, and free cache
storage without downloading or executing a model. Catalog compatibility is filtered against
this profile.

## Inspect the catalog and cache

```powershell
muru models list
muru models list --json
```

Catalog entries pin upstream revision, HTTPS URL, byte size, SHA-256 digest, GGUF format, runtime
variants, memory floor, and license metadata.

## Install a future qualified artifact

```powershell
muru models install <artifact-id>
```

Downloads stream into a partial file, enforce declared size, verify digest, flush, and promote
atomically. Cancellation, oversize response, or digest mismatch leaves no promoted model.

A gated artifact requires exact license acceptance:

```powershell
muru models install <artifact-id> --accept-license <license-id>
```

JSON mode never prompts and returns `license_required` until the expected value is supplied.

## Runtime isolation design

The preview selects a llama.cpp binary compatible with the machine CPU flags, verifies its
manifest, binds it to `127.0.0.1`, gives it a random bearer token, checks authenticated health,
and owns the child process. An 8 GB profile defaults to one resident model and does not evict an
active lease.

Local inference is constrained to one JSON action decision with temperature zero, generated
grammar, small output ceiling, and post-response schema validation. Undeclared actions and
Markdown-wrapped results are rejected.

Fixture-qualified behavior is not clean-machine or reference-device evidence. Check the
[project qualification page](../qualification.md) before treating any future artifact as
supported.
