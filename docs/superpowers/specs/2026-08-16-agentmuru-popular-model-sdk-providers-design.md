# AgentMuru Popular Model SDK Providers Design

## Decision

AgentMuru 0.3 will be a public feedback release that adds production model providers
backed by the official OpenAI, Anthropic, and Google Gen AI Python SDKs. These adapters
will preserve AgentMuru's provider-neutral runtime, governed tool execution, approvals,
ordered events, durable sessions, and replay behavior.

The release will not embed another agent runtime. OpenAI Agents SDK, LangGraph, CrewAI,
LlamaIndex, and similar orchestration frameworks remain outside this milestone because
they own agent loops, tools, state, or persistence that AgentMuru already owns. Future
bridges may treat an external agent as a remote capability, but they will not replace the
AgentMuru runtime inside this release.

## Release Outcome

The release succeeds when a new user can install one provider extra, configure an API key
through the provider's normal environment variable, replace `FakeModel` with a production
provider in an otherwise unchanged AgentMuru application, and exercise streamed text and
governed tool calls in Muru Workspace.

The user-facing promise is:

> Bring an OpenAI, Anthropic, or Google model. Keep AgentMuru's approvals, audit trail,
> persistence, and operator workspace.

AgentMuru remains usable without any provider dependency or credentials. `FakeModel`
stays the default for the generated starter, deterministic examples, and offline tests.

## Goals

- Support the official OpenAI Python SDK through an `OpenAIModel` adapter.
- Support the official Anthropic Python SDK through an `AnthropicModel` adapter.
- Support the official Google Gen AI Python SDK through a `GoogleGenAIModel` adapter.
- Normalize streaming text, function calls, usage, cancellation, and safe failures.
- Preserve complete tool-call conversations across SQLite restart and replay.
- Keep provider dependencies optional and outside the core runtime dependency direction.
- Give prospective users copy-and-run examples and a specific provider-feedback channel.
- Describe capability evidence honestly as contract-tested or credential-verified.

## Non-goals

- OpenAI Agents SDK integration or delegation to its agent loop.
- LangGraph, LangChain agent, CrewAI, LlamaIndex, or Google ADK bridges.
- A LiteLLM or other compatibility-proxy dependency.
- Hosted provider tools such as web search, code execution, or provider-managed MCP.
- Vision, audio, embeddings, image generation, or multimodal session messages.
- Structured-output schemas beyond ordinary tool calling.
- Automatic model selection, pricing tables, or calculated currency cost.
- Automatic retry of a model turn after any streamed output has been observed.
- Claims that every OpenAI-compatible endpoint behaves like the official OpenAI service.

## Alternatives Considered

### Native official-SDK adapters (selected)

Each provider adapter translates between its official SDK and AgentMuru's normalized model
contract. This produces the clearest failure behavior, lets AgentMuru test every mapping,
and leaves control of tools and approvals in the AgentMuru runtime. It requires three
small adapters, but that maintenance cost is justified for the initial supported set.

### One compatibility layer

A dependency such as LiteLLM could expose many providers quickly. This reduces the number
of direct integrations, but introduces another normalization layer between AgentMuru and
the vendor, makes streaming and error provenance harder to reason about, and weakens the
claim that each supported provider path has been verified. It may be offered later as a
community adapter rather than the primary production path.

### Agent-framework bridges

Wrapping LangGraph or CrewAI would give access to existing applications, but those
frameworks already perform orchestration, state management, persistence, tool execution,
and human-in-the-loop control. Running them inside AgentMuru would create two competing
runtimes and make ownership of cancellation, approvals, and replay ambiguous. This is not
the right first adoption surface.

## Architecture

Dependency direction remains inward:

```text
Official provider SDKs
        |
agentmuru.integrations.{openai,anthropic,google}
        |
ModelProvider / ModelRequest / normalized ModelEvent
        |
AgentMuru Runtime -> governed tools -> approvals -> session stores
        |
HTTP/WebSocket protocol -> Muru Workspace projection
```

Vendor SDKs may be imported only from outward integration modules. `agentmuru/core`,
`sessions`, `models`, `tools`, `artifacts`, `approvals`, and `observability` must not import
OpenAI, Anthropic, or Google packages. Vendor response objects, request identifiers,
exceptions, and credentials must not enter persisted messages or public runtime events.

## Installation and Public Imports

Provider packages are optional extras:

```powershell
python -m pip install "agentmuru[openai]"
python -m pip install "agentmuru[anthropic]"
python -m pip install "agentmuru[google]"
python -m pip install "agentmuru[providers]"
```

The `providers` extra composes all three provider extras. The existing `all` extra also
includes them. Minimum SDK versions will be set to the first versions verified by the
implementation and clean-wheel qualification; they will not be guessed in documentation.

Stable imports live in the provider modules so importing `agentmuru` does not require any
vendor package:

```python
from agentmuru.integrations.openai import OpenAIModel
from agentmuru.integrations.anthropic import AnthropicModel
from agentmuru.integrations.google import GoogleGenAIModel
```

Importing a provider module without its extra installed raises a concise error naming the
exact install command. Provider classes are documented and contract-tested before they
are treated as stable imports. They are not re-exported from `agentmuru.__init__` in 0.3.

## Provider Construction

The smallest configurations are:

```python
OpenAIModel(model="gpt-5.6")
AnthropicModel(model="claude-opus-5")
GoogleGenAIModel(model="gemini-2.5-flash")
```

Model identifiers in examples are verified when implementation begins and again before
release. Documentation will not describe an unavailable or unverified model as current.

Each constructor accepts an optional already-configured async client. Client injection is
the supported route for custom timeouts, proxies, enterprise endpoints, and deterministic
tests. Without an injected client, the official SDK resolves credentials from its normal
environment variables. API keys are never constructor fields on AgentMuru domain objects,
never copied into `Agent.model_settings`, and never serialized.

Each provider exposes:

- `name`, containing the stable provider identifier;
- `model_id`, containing the configured model identifier; and
- `capabilities`, accurately limited to behavior implemented by the adapter.

`FakeModel` gains `model_id = "fake"`. Custom providers receive a migration note for the
new provider-neutral model identifier. Runtime model-request events include `model_id`
when present so operators can distinguish models without exposing configuration secrets.

## Normalized Request Settings

`Agent.model_settings` continues to flow into `ModelRequest.settings`. The first provider
release defines common normalized keys for:

- `max_output_tokens`;
- `temperature`;
- `top_p`;
- `stop`; and
- `tool_choice`.

Adapters translate those keys to the official SDK's request shape. A nested
`provider_options` mapping may expose documented vendor options that have no normalized
equivalent. Adapters reject attempts to override reserved fields such as the model,
messages or input, instructions, tools, streaming mode, clients, credentials, and base
URLs through `provider_options`.

Unknown normalized keys fail before making a network request. This catches configuration
mistakes and prevents accidental leakage of application values into a vendor request.

## Durable Tool-call Conversation Contract

The current session transcript stores tool results but does not persist the assistant's
structured tool call. Real provider APIs need both the assistant tool request and its tool
result when the conversation continues. AgentMuru 0.3 therefore adds a normalized,
provider-neutral tool-call record to assistant messages.

The session domain gains an immutable record with:

- `id`: the provider call identifier, or an AgentMuru-generated identifier when absent;
- `name`: the requested AgentMuru tool name; and
- `arguments`: the parsed JSON object after applying the matched Tool's sensitive-field
  redaction policy.

`Message` gains a tuple of these records. Ordinary text messages use an empty tuple.
Assistant messages may contain text, tool calls, or both. Existing tool-result messages
continue to use `role=tool`, `tool_call_id`, `name`, and JSON text content.

SQLite serialization, HTTP session payloads, clean-wheel scenarios, and frontend protocol
types are extended to preserve the normalized tool-call records. The Workspace does not
need to render raw arguments as chat text; tool activity remains represented through the
existing governed runtime events, where sensitive fields are redacted.

The design deliberately avoids storing raw vendor response objects or hiding continuation
state inside a provider instance. A reconstructed `ModelRequest` must contain everything
needed to continue a tool conversation after process restart. Raw tool arguments exist
only in memory long enough to evaluate policy and execute the tool. When a requested tool
does not exist, the runtime fails safely without serializing its untrusted arguments.

## Runtime Turn Lifecycle

The runtime currently handles each `ToolCall` while the provider stream is still open.
The production-provider lifecycle changes to:

1. Start the provider span and emit the model-request event.
2. Consume the provider stream, publishing text deltas while collecting text and complete
   normalized tool calls in memory.
3. Record usage and close the provider stream.
4. Resolve each requested AgentMuru Tool and persist one assistant message containing its
   complete text and redacted tool-call records. Unknown tools fail without argument
   serialization.
5. Emit the assistant-message completion event when text exists.
6. Execute collected tool calls in provider order through the existing permission,
   approval, redaction, timeout, retry, trace, and persistence path.
7. Start the next model turn with the complete normalized transcript when a tool was used.
8. Complete when the provider returns a turn without tool calls.

Multiple tool calls from one assistant turn are preserved together before any tool result.
They are executed sequentially in 0.3 so approval order and runtime event order remain
deterministic. Parallel tool execution is a separate future design.

If a provider emits malformed or incomplete tool arguments, the adapter emits a safe
failure and no tool executes. Tool calls are yielded only after their complete JSON object
has been received and parsed.

## Adapter Behavior

### OpenAI

`OpenAIModel` uses the official asynchronous OpenAI client and Responses API. It converts
AgentMuru messages, instructions, and tool schemas into Responses input and function
definitions. It accumulates streamed function-call arguments, emits completed tool calls,
and records response token usage without persisting provider response IDs.

The adapter targets the official OpenAI service. An injected client may point to a custom
endpoint, but the documentation will describe that path as user-configured and unverified
unless a separate compatibility test exists.

### Anthropic

`AnthropicModel` uses the official asynchronous Anthropic Messages client. It translates
AgentMuru instructions to the system field, assistant tool calls to `tool_use` blocks,
tool results to `tool_result` blocks, and AgentMuru tool schemas to Anthropic tool
definitions. Streamed content blocks are normalized without exposing SDK objects.

### Google

`GoogleGenAIModel` uses the official asynchronous Google Gen AI client. It translates the
normalized transcript into Google content and parts, AgentMuru instructions into system
instructions, and tools into function declarations. Both Gemini Developer API and Google
enterprise configuration are available through official client injection; credential
verification is recorded separately for each service actually tested.

If a Google function-call response has no stable call identifier, AgentMuru creates one
for that normalized conversation and persists it with the assistant message and result.

## Capabilities

The initial adapters claim only:

- text input and output;
- streaming text;
- function or tool calling; and
- input and output token usage when the provider reports it.

Vision, audio, embeddings, structured output, provider-hosted tools, and reasoning traces
remain false or unsupported even if a configured vendor model offers them. Capability
flags describe what the AgentMuru adapter has implemented and tested, not the full vendor
model catalog.

Currency cost remains `None` because pricing is time-dependent and provider usage objects
do not establish the application's actual billed amount. Users still receive token usage
for their own cost analysis.

## Failures, Cancellation, and Retries

Adapters map vendor exceptions into stable safe codes:

- `model_authentication`;
- `model_permission`;
- `model_rate_limit`;
- `model_timeout`;
- `model_invalid_request`;
- `model_unavailable`;
- `model_invalid_tool_arguments`; and
- `model_provider_error`.

`ModelFailed.message` contains a safe explanation and never the raw vendor exception,
request body, response body, endpoint URL, or credential. The `retryable` flag is true
only for rate limits, timeouts, and temporary unavailability.

Adapters do not introduce hidden AgentMuru retries. Official clients may be configured by
the application owner, but the provider adapter never repeats a streamed turn after text
or a tool call has been observed. Cancellation closes or exits the SDK stream and
propagates `asyncio.CancelledError` so the runtime records a cancelled run instead of a
provider failure.

## Security and Privacy

- Provider credentials remain in environment variables or injected SDK clients.
- Secrets and raw exceptions never enter session messages, runtime events, traces, or logs.
- Assistant transcript arguments, public tool events, and approval records all use the
  matched Tool's sensitive-field redaction policy. Raw arguments remain in memory only
  for the active policy evaluation and invocation.
- Documentation warns application owners that session databases may contain model text,
  tool arguments, and tool results and must be protected accordingly.
- Provider request logging is not enabled by AgentMuru.
- Test fixtures are synthetic and contain no copied customer prompts, responses, or keys.
- Provider-hosted tools are excluded because they would bypass AgentMuru's permission and
  approval boundary.

## Test Strategy

Implementation follows test-driven development. Each behavior begins with a focused test
that fails for the intended reason before production code is written.

Shared provider contract tests cover:

- text-only streaming order;
- text followed by one tool call;
- multiple tool calls in one assistant turn;
- streamed and fragmented JSON tool arguments;
- mixed assistant text and tool calls;
- transcript reconstruction for a second turn;
- assistant tool-call persistence across SQLite reopen;
- sensitive assistant tool-call argument redaction before persistence;
- input and output usage mapping;
- empty and omitted usage;
- cancellation and stream cleanup;
- each normalized safe error code;
- malformed tool arguments;
- missing optional dependency diagnostics;
- settings translation and reserved-field rejection; and
- absence of vendor objects or raw exceptions in persisted/public values.

Each adapter has deterministic fake-client fixtures that model its current official SDK
event shapes. No network call is required for the default suite. Tests import the real SDK
types when the provider extra is installed so fake shapes cannot silently drift away from
the supported SDK surface.

The runtime suite adds ordering assertions proving that the assistant tool-call message is
persisted before tool results and that replayed requests reconstruct the same normalized
conversation. SQLite, HTTP serialization, frontend protocol, examples, public imports,
package metadata, and clean-wheel qualification receive corresponding coverage.

## Credential-backed Verification

Live checks are opt-in and require explicit provider credentials. Each provider check uses
a bounded model, prompt, output limit, and tool schema. It verifies one streamed text turn
and one non-destructive tool-call turn. It records the SDK version, model identifier,
service variant, timestamp, and result without recording prompts, model output, keys, or
raw headers.

The integration-status page uses these states precisely:

- **Implemented** after the adapter ships and local runtime behavior is exercised;
- **Contract tested** after deterministic official-SDK mapping tests pass;
- **Credential verified** only for the provider, service variant, and model used by a live
  authorized check; and
- **Planned** for everything else.

Missing credentials produce a recorded skip, not a credential-verified claim. Release can
proceed with contract-tested providers if the release notes state which live checks were
not run; at least one credential-backed provider path is required before describing 0.3
as production-provider verified.

## Customer-facing Documentation

Public navigation stays task-oriented. It does not expose internal adapter packages or a
maintainer-centric provider architecture tree. The documentation journey is:

- **Getting started -> Connect a real model**: choose OpenAI, Anthropic, or Google, install
  one extra, configure credentials, and run the same starter application;
- **Guides -> Use OpenAI**, **Use Anthropic**, and **Use Google**: provider configuration,
  supported settings, tool behavior, errors, and service-specific limits;
- **Reference -> Model providers**: stable class signatures, normalized settings, and
  capability matrix;
- **Operations -> Provider security and cost visibility**: credentials, data handling,
  token usage, timeouts, and safe logging; and
- **Current capabilities and limits**: exact evidence state for every provider path.

The credential-free `FakeModel` quickstart remains first. README and installation pages
add a short second path titled "Use a real model" rather than replacing the reliable local
onboarding path.

Examples are executable applications under `examples/providers/`, not isolated snippets.
Documentation includes the example source or imports it so examples and docs cannot drift.

## Feedback Loop

The repository adds a provider-feedback GitHub issue form that asks for:

- provider and model identifier;
- AgentMuru and provider SDK versions;
- Python version and operating system;
- text, streaming, tool-call, approval, persistence, or error scenario;
- expected and observed behavior;
- a minimal reproduction with secrets removed; and
- permission to use a sanitized reproduction as a contract fixture.

Provider guides and release notes link directly to that issue form with the request:
"Try one real workflow and tell us where the provider experience breaks." The form warns
users not to include keys, full prompts, customer data, or raw provider response bodies.

Feedback is evaluated against reproducible behavior and used to prioritize patch releases.
Requests for additional providers or framework bridges are tracked separately from defects
in the supported three-provider contract.

## Release and Compatibility

The target version is 0.3.0. It is a pre-1.0 minor release because normalized assistant
tool-call history extends the session serialization contract and custom model providers
gain a documented `model_id` expectation.

Existing text-only `FakeModel` applications remain source-compatible. Existing SQLite
databases receive an additive schema migration for assistant tool-call records; reopening
an older database preserves all prior messages. Custom session stores and model providers
receive migration notes and contract tests.

The release gate includes:

1. focused provider and runtime tests;
2. the complete Python, Ruff, MyPy, frontend, browser, strict MkDocs, and bundle checks;
3. wheel and source distribution builds;
4. one clean environment for the base package;
5. separate clean-wheel imports for each provider extra;
6. a combined `providers` extra scenario;
7. all provider examples with deterministic clients;
8. recorded opt-in live-check results or explicit skips;
9. package metadata and contents inspection; and
10. documentation and release-claim review against the integration-status evidence.

Publishing, tagging, and release promotion occur only after these gates pass. The release
notes identify the providers as beta integrations and link directly to the feedback form.

## Definition of Done

AgentMuru 0.3 is complete only when:

- all three official SDK adapters satisfy the shared provider contract;
- a user can switch from `FakeModel` to any supported provider without runtime changes;
- streamed text and governed tool calls work through Muru Workspace;
- assistant tool calls and tool results survive SQLite restart and replay;
- multiple tool calls preserve deterministic message and event ordering;
- cancellation closes streams and records cancelled runs correctly;
- public errors and persistent state contain no credentials, unredacted sensitive tool
  arguments, or raw vendor exceptions;
- optional extras install independently from a built wheel;
- every provider example runs through the clean-wheel qualification path;
- documentation navigation remains customer-facing and every code sample is verified;
- capability states distinguish contract tests from credential-backed checks;
- the provider-feedback issue form is live and linked from docs and release notes;
- migration notes cover custom providers, stores, and existing SQLite databases; and
- the complete repository and release qualification gates pass from fresh artifacts.
