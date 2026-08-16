# AgentMuru Adaptive Edge Agents Design

## Decision

AgentMuru will become a Windows-first adaptive edge-agent product rather than another
general-purpose agent framework. A user installs one `muru` command, describes a bounded
automation outcome, reviews the proposed team and permissions, and lets AgentMuru profile
the machine, benchmark compatible small language models, choose the smallest passing
model set, and activate an auditable local agent package.

The product combines two previously considered directions:

1. an adaptive nano-agent compiler that turns requirements, tools, examples, and resource
   constraints into a portable agent package; and
2. a polished desktop-automation experience whose primary interface is a full-screen
   terminal workspace.

The runtime may use multiple specialist SLMs, but low-resource machines load them
sequentially unless measured headroom supports residency. Multiple logical agents may
share one loaded model. Optional internet verification is read-only and capability
brokered. Cloud-model escalation is a separate, explicit permission and is not required
for the first public proof.

This design supersedes the release priority in
`2026-08-16-agentmuru-popular-model-sdk-providers-design.md`. Hosted provider adapters may
later implement cloud escalation, but they are no longer the next product milestone.

## Product Promise

> Install once. Describe one job. Muru builds the smallest measured agent team that can do
> it on your machine, shows exactly what it may access, and runs it locally.

The first flagship is a local action router. A user registers 5-50 typed actions and
representative requests. AgentMuru selects an action and arguments, validates the result,
checks policy, requests approval where necessary, executes the action, or abstains.

AgentMuru is not marketed as a local ChatGPT replacement. Its initial value is reliable,
structured, low-latency automation on hardware that mainstream local-AI desktops do not
serve well.

## First User and Job

The first user is an individual developer, technical operator, or power user on Windows
who already has scripts, local files, APIs, or MCP tools and wants a safer natural-language
front door for them.

The first complete job is:

1. install AgentMuru from a terminal;
2. launch `muru` with no project scaffolding;
3. describe a bounded automation goal;
4. import or define typed actions and 10-30 examples;
5. review the generated agent team, models, resource budget, and permissions;
6. let AgentMuru download and verify compatible models;
7. benchmark the candidates on the local hardware and task examples;
8. activate only a package that meets the configured thresholds; and
9. run, inspect, approve, replay, and explain executions from the terminal workspace.

## Goals

- Deliver a single native `muru` executable for Windows.
- Treat CPU-only Windows with 8 GB total RAM as a first-class reference target.
- Probe CPU instruction sets, RAM, storage, operating system, and usable acceleration.
- Maintain a signed, pinned catalog of supported runtimes and quantized models.
- Select models using both hardware compatibility and task-specific evaluation.
- Support multiple logical agents and multiple specialist models with a memory-aware
  scheduler.
- Compile declarative, portable, inspectable agent packages instead of generated programs.
- Make terminal UX a product surface, not a diagnostic afterthought.
- Default to least privilege, structured output, deterministic validation, and abstention.
- Offer read-only internet verification behind explicit per-agent capabilities.
- Preserve ordered events, approvals, traces, and replay across the native and Python
  runtimes.
- Keep the existing Python AgentMuru package useful as an SDK, authoring environment, and
  compatibility layer.
- Define a package/runtime boundary that can later be hosted by a native Android app.

## Non-goals for the First Public Proof

- General-purpose conversational chat.
- Unbounded autonomous planning.
- Free-form agent-to-agent group conversations.
- Simultaneously resident model swarms on low-memory devices.
- Generating and directly executing arbitrary shell commands.
- Browser login, purchasing, posting, sending messages, or other web mutations.
- Mandatory Docker, WSL2, Python, Node.js, or a background web server.
- Local fine-tuning on the reference Pentium-class machine.
- Android release before the Windows runtime and package contracts are proven.
- Supporting every GGUF model or every inference backend.
- Claiming performance or compatibility that has not been measured on named hardware.

## Competitive Boundary

Ollama, LM Studio, Jan, LocalAI, and Docker Model Runner already provide model download,
serving, or hardware-aware execution. smolagents, Goose, AutoGen, and similar frameworks
already provide tools and multi-agent abstractions. AgentMuru will not compete on the
number of models, providers, or agent patterns.

AgentMuru's owned workflow is:

```text
bounded task + examples + tools + permissions + hardware
    -> compatible candidate set
    -> on-device task evaluation
    -> smallest passing model team
    -> portable least-privilege agent package
    -> observable local execution with abstention
```

The differentiator is measured task fitness on the user's hardware, not automatic model
download by itself.

## Product Architecture

AgentMuru becomes a two-runtime repository with a language-neutral package and event
contract.

```text
Python SDK / existing web workspace       Native Windows terminal workspace
        |                                               |
        +---------- agent-pack v1 / event v1 -----------+
                                |
                 native edge runtime and scheduler
                    |          |          |
              llama.cpp     capability   trace store
               supervisor      broker
                    |
          verified local GGUF model cache
```

### Native edge binary

A new Go module under `edge/` produces the `muru` executable. Go is selected for this
milestone because it produces a single Windows binary, has strong terminal libraries,
supports low-overhead concurrency, and matches the implementation approach proven by the
TUIOS reference. The native binary owns:

- hardware discovery and compatibility classification;
- model catalog verification, download, and cache management;
- llama.cpp process supervision and local inference requests;
- agent-pack validation and execution;
- model routing, loading, unloading, and resource budgeting;
- capability decisions and approval prompts;
- the terminal workspace and non-interactive CLI;
- append-before-publish local event recording; and
- benchmark and diagnostic reports.

The native core must not depend on the Python package at runtime.

### Existing Python package

The existing `agentmuru` package remains:

- the stable Python SDK for defining agents, tools, and applications;
- an authoring and export surface for agent-pack v1;
- a reference implementation for event and permission semantics;
- the server and browser workspace for users who need those surfaces; and
- a conformance consumer of shared JSON fixtures.

The Python package will not be duplicated wholesale in Go. Only behavior required by the
edge product is implemented natively, with compatibility enforced by versioned schemas
and fixtures.

### Inference backend

The first backend is a pinned llama.cpp distribution supervised as a local child process.
This keeps the Go binary free of CGo and isolates inference crashes. AgentMuru ships or
downloads verified Windows runtime variants for baseline x86-64, AVX, and AVX2 where
testing proves them viable. The hardware profiler selects a compatible variant before it
is ever executed.

The supervisor starts llama-server on loopback with an ephemeral authentication token,
selects an unused port, rejects non-loopback binding, captures sanitized logs, and stops
the process with AgentMuru. Dynamic model loading/unloading and idle sleep are used when
supported by the pinned release.

ONNX Runtime GenAI is a later backend candidate for Windows accelerators and Android. It
does not enter the first proof until the llama.cpp contract passes the reference-device
gates.

## Hardware Contract

The first advertised target is a named Windows 10 or Windows 11 x64 reference machine
with:

- a Pentium-class CPU;
- no discrete GPU;
- 8 GB installed RAM;
- no AVX2 requirement if the baseline llama.cpp build meets the quality and latency gate;
- at least 2 GB free storage during installation; and
- a true-color terminal for the full visual experience, with a readable fallback for
  basic consoles and redirected output.

Initial release gates are:

- bootstrap process working set below 150 MB before inference starts;
- total AgentMuru plus inference peak working set below 2 GB for the flagship pack;
- installed model artifacts at or below 700 MB for the flagship pack;
- default context between 512 and 2,048 tokens;
- 100% schema-valid model decisions through constrained decoding and validation;
- at least 95% accepted action accuracy on the versioned flagship evaluation set;
- 100% denial of the versioned unsafe-action cases;
- no execution when validation, permission, compatibility, or quality gates fail; and
- a published benchmark report naming CPU, RAM, OS, runtime build, model hash,
  quantization, context, latency distribution, and peak memory.

Latency is reported rather than promised until a physical reference machine is selected.
The release cannot use the phrase "Pentium support" without a passing report from that
machine.

## Hardware Discovery

`muru doctor --json` returns a stable `HardwareProfile` containing:

- OS name, build, and architecture;
- logical and physical CPU counts;
- CPU vendor/model and supported instruction flags;
- total and currently available RAM;
- free space in the AgentMuru cache volume;
- detected GPU/accelerator descriptions when available;
- terminal color, mouse, and width capabilities;
- compatible inference runtime variants; and
- an explicit support classification with human-readable reasons.

Discovery is read-only and never uploads machine information. The interactive doctor
shows the exact report and can export a redacted copy for bug reports.

## Model Catalog and Supply Chain

AgentMuru consumes a signed catalog rather than arbitrary model URLs. Each entry contains:

- stable catalog identifier;
- upstream repository and immutable revision;
- artifact filename, byte size, and SHA-256 digest;
- model family, parameter count, quantization, and context ceiling;
- license identifier and whether interactive acceptance is required;
- compatible runtime variants and CPU features;
- estimated load memory and benchmark provenance;
- supported output grammars and tool-call format; and
- task-suite results produced by AgentMuru qualification.

The downloader streams to a temporary file, enforces the declared size ceiling, verifies
the digest, and atomically promotes the artifact into the cache. Pickle-based model
formats are not accepted. Gated models such as FunctionGemma require the user to complete
the upstream license flow; AgentMuru never bypasses it.

The first candidate set is deliberately small: one ungated Apache-licensed model such as
Qwen3 0.6B GGUF and FunctionGemma 270M after license acceptance and task-specific tuning
evidence. Catalog inclusion means "supported and measured," not "available upstream."

## Agent Pack v1

An agent pack is a directory or archive with the following required files:

```text
invoice-router.muru/
  manifest.json
  agents.json
  actions.json
  policy.json
  evals.jsonl
  prompts/
  assets/
  checksums.txt
```

`manifest.json` contains identity, format version, minimum runtime, entry agent, resource
budget, model requirements, and provenance. `agents.json` contains logical roles and typed
handoff edges. `actions.json` contains JSON-schema inputs and outputs. `policy.json`
contains capabilities, approval rules, filesystem roots, network modes, and rate limits.
`evals.jsonl` contains accepted, rejected, ambiguous, and unsafe cases.

Packs never contain plaintext credentials. A pack may reference locally installed secrets
by logical name, but the capability broker resolves them only for an approved tool and
never exposes their values to prompts, traces, or other agents.

Agent Skills may be imported as instruction and resource material. MCP tools may be
adapted into actions. Neither import automatically grants execution permissions.

## Agent Compiler

The compiler is an interview and validation pipeline, not an unconstrained code generator.

1. Capture the bounded outcome and explicit exclusions.
2. Discover typed actions from built-ins, scripts with descriptors, Agent Skills, or MCP.
3. Ask the user for representative successful, ambiguous, and forbidden requests.
4. Propose the minimum logical agent graph.
5. Propose model requirements from the graph's output shapes and task categories.
6. Propose a least-privilege policy.
7. Render a complete diff-like review in the terminal workspace.
8. Validate and benchmark candidate models.
9. Activate only if all mandatory gates pass.

The compiler may use a local SLM to classify requirements into curated templates, but
templates and deterministic validation define the final package. Novel code generation is
saved as a draft outside the active package and is never executed automatically.

## Multi-Agent and Multi-Model Semantics

Agents communicate through typed `TaskEnvelope` values rather than shared unrestricted
conversation history. Each envelope contains task and correlation identifiers, source and
destination agents, typed input, allowed capabilities, deadline, and trace parent.

The coordinator uses deterministic routing when a graph edge or action schema matches.
Only ambiguous cases invoke a routing model. Every agent has explicit input/output schemas,
model requirements, tool access, context budget, retry budget, and terminal state.

The model scheduler maintains:

- a compatibility filter derived from the hardware profile;
- measured task accuracy and schema reliability;
- current and predicted working set;
- cold-load and warm-inference latency;
- privacy and network policy;
- model residency and last-use state; and
- fallback and abstention thresholds.

On the 8 GB profile, the default residency limit is one local model. Logical agents share
that model where possible; otherwise the scheduler unloads the current model before
loading the next specialist. A pack may require multiple simultaneous models only when the
hardware profile and benchmark prove sufficient headroom.

## Evaluation and Selection

Hardware compatibility produces a candidate list. It does not choose the model.

For every candidate configuration AgentMuru measures:

- action-selection accuracy;
- argument exact match and field-level correctness;
- schema validity;
- false execution rate on ambiguous and forbidden cases;
- abstention precision and recall;
- cold-load time;
- warm latency distribution;
- peak working set;
- tokens processed and generated; and
- runtime or model failures.

The default selection rule is lexicographic:

1. reject any candidate that violates compatibility, memory, safety, or schema gates;
2. reject any candidate below the pack's quality threshold;
3. among passing candidates, choose the smallest artifact;
4. break ties using measured warm latency; and
5. preserve the full result table so the user can override within passing candidates.

An override cannot activate a failing candidate unless the pack is explicitly placed in
development mode, where actions are simulated and never committed.

## Terminal Workspace

The terminal workspace is inspired by TUIOS's full-screen, pane-based, modal experience,
command palette, persistent sessions, mouse support, themes, and event-driven rendering.
AgentMuru does not embed a general terminal multiplexer or copy TUIOS's window manager.
Its panes are product-specific projections of runtime state.

### Interaction principles

- Event-driven rendering; no fixed high-frequency refresh loop.
- Near-zero idle CPU when no runtime event or user input occurs.
- Keyboard-first operation with complete mouse alternatives.
- A searchable command palette on `Ctrl+P`.
- Discoverable key chords through a which-key overlay and `?` help.
- Modal separation between navigation and text entry.
- Responsive layouts for narrow, standard, and wide terminals.
- No dependency on kitty graphics or sixel for essential information.
- Theme tokens with accessible contrast and a monochrome fallback.
- Sanitization of untrusted ANSI and terminal control sequences.
- Persistent workspaces that can detach and reattach to running jobs.

### Workspace model

The default workspace contains:

- **Agent map**: team graph, active agent, handoffs, and status;
- **Run stream**: user requests, decisions, tool calls, and concise results;
- **Inspector**: selected event, model, evidence, schema, or error details;
- **Resource dock**: CPU, RAM, active model, context, network mode, and queue;
- **Approval overlay**: exact action, arguments, scope, risk, and decision keys; and
- **Command palette**: create, run, inspect, benchmark, permissions, models, export,
  settings, and help.

On terminals below 100 columns, the panes become tabs. Below 70 columns, the interface
uses a single focused view plus a status line. Non-interactive commands provide stable
JSON and plain-text output for scripts and screen readers.

### Primary flows

`muru` opens the workspace. `muru create`, `muru run <pack>`, `muru doctor`,
`muru benchmark <pack>`, `muru permissions <pack>`, and `muru explain last` are also
available without entering the workspace.

The creation flow moves through visible stages:

```text
Goal -> Actions -> Examples -> Team -> Models -> Permissions -> Benchmark -> Activate
```

Every long-running step is cancellable. Downloads show bytes, speed, checksum stage, and
remaining disk. Benchmarks show case counts and partial results rather than an indefinite
spinner.

## Capability and Sandbox Model

Capabilities are denied unless granted. Initial capability families are:

- `fs.read`, scoped to exact roots and glob restrictions;
- `fs.write`, scoped separately from read;
- `process.run`, scoped to exact executables and argument templates;
- `web.read`, scoped by network mode and domain policy;
- `secret.use`, scoped to a named tool without prompt exposure;
- `mcp.connect`, scoped to an exact server definition; and
- `cloud.infer`, disabled by default and distinct from web retrieval.

Built-in tools run inside the native process with explicit validation. Portable third-party
tools target WASI and receive only declared preopens and network capabilities. Native
scripts and MCP servers require an exact command review and run with restricted working
directories, environment allowlists, timeouts, output ceilings, and approval policy.
Docker is an optional stronger sandbox on capable desktop systems, never a base
requirement.

Authorization is enforced by the capability broker immediately before each effect. Model
output, agent instructions, web content, and tool metadata cannot grant permissions.

## Read-Only Internet Verification

Network modes are `offline`, `ask`, `allowlist`, and `research`. `offline` is the default.

The model emits a structured retrieval request. A separate broker validates the URL or
query, protocol, domain, redirect chain, private-address exclusions, byte ceiling,
content type, timeout, and rate limit. Returned content is converted to bounded plain text,
labeled as untrusted external data, and stored with source URL, retrieval time, digest,
and agent-visible excerpt.

Web content is evidence, never instructions. It cannot directly invoke an action, change
policy, or request a secret. Any action based on web evidence passes through the normal
schema validator and capability broker. The TUI always distinguishes user input, trusted
package instructions, model output, tool results, and untrusted web evidence.

Cloud inference, when added, uses the separate `cloud.infer` capability. The approval UI
shows provider, model, estimated data sent, redaction result, and whether fallback is one
time or persistent for the pack.

## Persistence and Observability

The native runtime preserves AgentMuru's append-before-publish rule. Events remain
monotonic and replayable per session. Event v1 fixtures are shared with the Python runtime.

New event families cover:

- hardware profiling;
- model download and verification;
- model load, unload, and selection;
- evaluation cases and summary;
- agent compilation and activation;
- typed routing and handoff;
- resource samples;
- network requests and evidence; and
- capability decisions.

Sensitive arguments, tokens, environment variables, raw exception details, and unredacted
web content are never persisted. `muru explain` builds its account from recorded decisions,
not from a second model-generated explanation.

## Installation and Updates

The primary Windows distribution is a signed WinGet package. GitHub Releases provide
checksummed standalone archives. The installer places the native binary and bootstrap
catalog only; it does not download a model until the user approves a pack or runs the
guided setup.

Runtime, catalog, and model updates are separate operations. Updates verify signatures and
support rollback to the previous runtime and catalog. Agent packs pin catalog model IDs and
resolved hashes so a catalog update cannot silently change an active pack.

## Android Direction

Android consumes agent-pack v1 and event v1 rather than the desktop TUI. The supported
consumer experience will be a native application with the Android OS sandbox, storage
access framework, explicit network permissions, and device-specific inference backend.

Termux may host an experimental developer preview, but it is not the consumer installation
story. The Android milestone begins only after:

- Windows agent-pack conformance is stable;
- at least one flagship pack passes on the 8 GB reference machine;
- memory-aware model switching is measured;
- the security threat model has an external review; and
- pack behavior can be reproduced without Python or the web workspace.

## Delivery Slices

### Slice 0: contracts and benchmark laboratory

Define agent-pack v1, event additions, hardware profile, catalog records, conformance
fixtures, and the named reference-device protocol. This slice produces no capability
claim beyond machine inspection and schema validation.

### Slice 1: native bootstrap and terminal shell

Ship the Go `muru` binary with hardware doctor, event-driven terminal shell, command
palette, responsive workspace, settings, session persistence, and fake event streams.

### Slice 2: verified local model execution

Add the signed catalog, atomic downloader, llama.cpp runtime selection, supervised local
server, constrained action output, and model lifecycle views.

### Slice 3: adaptive agent compiler and evaluation

Add guided pack creation, action imports, examples, candidate benchmarking, selection,
typed handoffs, shared-model agents, sequential multi-model scheduling, and activation
gates.

### Slice 4: secure effects and web evidence

Add capability enforcement, approvals, restricted native tools, WASI tools, MCP import,
read-only web verification, evidence display, and adversarial security qualification.

### Slice 5: public proof and feedback release

Run the named low-end benchmark, publish the reproducible report, distribute signed
Windows artifacts through GitHub and WinGet, update customer documentation, and recruit
users around the action-router workflow.

### Slice 6: Android feasibility and cloud escalation

Validate the pack/runtime boundary in a native Android prototype, then separately add
explicit cloud-model escalation if user evidence shows it is needed.

## Success Metrics

The first feedback release succeeds when:

- a new Windows user reaches a running flagship pack without Python, Docker, or manual
  model selection;
- at least 80% of observed onboarding sessions finish without consulting documentation;
- the reference-device release gates pass from a clean machine;
- at least 10 external users create a pack with their own actions;
- at least 3 external users publish or share a reusable pack;
- every execution can be explained from deterministic trace data;
- unsafe and ambiguous evaluation cases do not produce effects; and
- collected feedback distinguishes model-quality failures, package-design failures,
  permission failures, and TUI usability failures.

## Risks and Mitigations

### Baseline CPU performance is unusable

Mitigation: make the action-router output short, constrain context, test 270M-600M
candidates, use deterministic routing before a model, and publish the measured limit. If
non-AVX2 latency fails, support remains experimental rather than being marketed.

### Automatic composition creates unsafe or incoherent teams

Mitigation: compile from curated templates, require typed actions and examples, render the
entire proposed graph and policy, benchmark before activation, and refuse arbitrary code.

### Multi-model loading destroys the UX

Mitigation: prefer shared models, score cold-load cost, limit residency by measured memory,
preload only the predicted next specialist, and show model transitions in the resource
dock.

### Internet evidence injects instructions

Mitigation: isolate retrieval behind a broker, label and bound external text, prohibit
permission changes from model context, validate every downstream output, and require
approval for effects.

### Native and Python behavior diverge

Mitigation: version schemas, maintain golden cross-runtime fixtures, define conformance
tests, and avoid reimplementing features that are not required by the edge product.

### The TUI becomes an ornamental dashboard

Mitigation: every pane must support a primary user decision, all commands must work without
the full-screen UI, idle CPU and narrow-terminal behavior are release gates, and usability
tests measure task completion rather than visual preference alone.

## Research Basis

The design draws on current primary sources:

- TUIOS for event-driven, pane-based, modal terminal interaction:
  <https://github.com/Gaurav-Gosain/tuios>
- llama.cpp for GGUF inference, constrained output, Windows/Android portability, and
  dynamic model supervision: <https://github.com/ggml-org/llama.cpp>
- FunctionGemma for specialized local function calling:
  <https://ai.google.dev/gemma/docs/functiongemma>
- Qwen3 0.6B GGUF for an ungated Apache-licensed small-model candidate:
  <https://huggingface.co/Qwen/Qwen3-0.6B-GGUF>
- RouteLLM for evaluated strong/weak model routing:
  <https://github.com/lm-sys/RouteLLM>
- Agent Skills for portable instruction/resource packages:
  <https://github.com/agentskills/agentskills>
- MCP security guidance for local tool consent and least privilege:
  <https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices>
- OWASP guidance for prompt injection, output validation, and excessive agency:
  <https://owasp.org/www-project-top-10-for-large-language-model-applications/>
- OCI artifacts for future content-addressed pack distribution:
  <https://specs.opencontainers.org/image-spec/manifest/>
- ONNX Runtime GenAI, ExecuTorch, and llama.cpp Android documentation for later portable
  inference work.

## Approval

The user approved the adaptive agent compiler and desktop automation directions, requested
resource-aware multi-agent and multi-model execution, optional internet checking, and a
TUIOS-like terminal experience. This specification incorporates those decisions. The
implementation plan must keep the Windows proof ahead of Android and keep cloud inference
separate from read-only internet verification.
