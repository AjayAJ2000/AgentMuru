# Current capabilities and limits

Use this page to confirm what AgentMuru 0.2 supports before you choose an integration or
deployment shape. Capability claims use four precise states:

- **Implemented**: shipped in the runtime and exercised directly.
- **Contract tested**: adapter behavior is verified with deterministic fakes.
- **Credential verified**: exercised against an authorized live service.
- **Planned**: roadmap work, not a current capability.

| Capability | State | Evidence | Boundary |
| --- | --- | --- | --- |
| FakeModel | Implemented | Runtime and scenario suites | Deterministic; not a production provider |
| In-memory stores | Implemented | Shared store contracts | Process-local only |
| SQLite persistence | Implemented | Reopen, concurrency, browser restart, clean wheel | One Runtime process per file |
| Databricks SDK/SQL imports | Contract tested | Optional-extra clean install and adapter tests | No live workspace call in offline gate |
| Databricks live workspace | Contract tested | Identity/config behavior | Credential verification is not recorded yet |
| Production model provider | Planned | Roadmap | FakeModel is the current concrete provider |
| PostgreSQL store | Planned | Store protocols and roadmap | SQLite is the current durable implementation |

## Native local-model qualification

Native edge evidence uses three levels that must not be collapsed into one “supported” label:

- **Fixture-qualified**: deterministic signed-catalog, tamper, download, child-process,
  constrained-decision, residency, and terminal tests pass with local fixtures.
- **Clean-machine-qualified**: a packaged archive installs on a fresh Windows image, downloads
  a declared test artifact, starts the pinned runtime, returns a constrained decision, and
  records redacted resource evidence.
- **Reference-device-qualified**: the exact published model/runtime pair passes the same flow
  on a named low-end device profile, including latency and working-set thresholds.

The source preview is Fixture-qualified. Clean-machine qualification and the Windows native
archive are not yet published. **No catalog model is reference-device-qualified**, including
the Pentium 8 GB target; therefore the signed bootstrap catalog currently contains no public
model artifacts.

| Native capability | State | Evidence | Boundary |
| --- | --- | --- | --- |
| Signed catalog verification | Fixture-qualified | Ed25519 mutation and semantic tests | Empty production bootstrap |
| Atomic GGUF download | Fixture-qualified | Size, digest, cancellation, promotion tests | No public artifact entry |
| llama.cpp variant selection | Fixture-qualified | Feature-subset tests | Build outputs require qualification |
| Authenticated local supervisor | Fixture-qualified | Loopback child, token, Job Object, event order | Fixture child process |
| Constrained action decision | Fixture-qualified | Grammar, JSON, allowlist, redaction tests | Fixture HTTP backend |
| Pentium 8 GB model/runtime pair | Planned | Hardware contract fixture only | No reference-device report |
| Native terminal workspace | Fixture-qualified | Responsive golden tests and 60-second idle probe | Source/prerelease preview |
| Portable agent-pack compiler | Fixture-qualified | Strict loader, compiler, checksum, and contract tests | Directory packs; simulation only |
| Action-router sample | Fixture-qualified | 40 measured cases, at least 95% routing gate | Deterministic router; not model quality |
| Trusted-host capability broker | Fixture-qualified | Path, process, web-target, and default-deny tests | Effect execution remains disabled |
| Optional internet retrieval | Planned | HTTPS/host/IP authorization primitives only | No fetcher is shipped |
| Android runtime | Planned | Product target only | No Android build or device report |

The latest machine-readable and rendered evidence is in
[AgentMuru qualification evidence](qualification.md).
