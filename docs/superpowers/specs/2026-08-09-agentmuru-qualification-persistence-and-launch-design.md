# AgentMuru Qualification, Persistence, and Launch Design

## Decision

AgentMuru 0.2 will combine product qualification with durable local persistence. The
release will prove the framework through clean-wheel installation, runnable scenarios,
contract tests, browser tests, documentation builds, and deployment checks while adding
a standard-library SQLite adapter for sessions, messages, runs, events, artifacts,
approvals, and idempotency records.

The release also replaces the legacy BrickFlowUI landing content with an AgentMuru site,
adopts the approved DataMuru identity as a related product-family system, expands the
MkDocs documentation into an operator-quality reference, and resets the GitHub roadmap
around verified AgentMuru outcomes.

The stable identity remains:

- product: **AgentMuru**;
- framework: **AgentMuru Runtime**;
- Python distribution and package: `agentmuru`;
- CLI: `muru`;
- browser application: **Muru Workspace**.

## Release Outcome

The release succeeds when a new user can install the built AgentMuru wheel into a clean
environment, run every supported public workflow, restart an application without losing
completed history, inspect that history in Muru Workspace, follow complete documentation,
and evaluate the product on a deployed AgentMuru landing page whose claims correspond to
fresh qualification evidence.

The roadmap milestone is **AgentMuru 0.2 — Product Qualification and Durable Local
Persistence**. It is the next in-progress outcome on the GitHub project. Production model
providers and a PostgreSQL adapter remain subsequent milestones rather than being mixed
into this release.

## Scope

The release includes:

- explicit persistent mutation operations in the core store protocols;
- SQLite session, artifact, and approval stores composed through one persistence object;
- durable sessions, messages, runs, ordered events, artifacts, approvals, and idempotency;
- restart recovery for incomplete runs from the previous local runtime process;
- contract suites applied to both in-memory and SQLite adapters;
- a clean-install qualification harness and runnable scenario gallery;
- frontend and browser qualification of all Muru Workspace states;
- accurate Databricks contract verification with optional credential-backed validation;
- a complete AgentMuru documentation structure and qualification report;
- an AgentMuru landing page derived from the existing BrickFlowUI landing repository;
- a Vercel CLI preview, smoke-test, and production-promotion flow;
- GitHub roadmap, issue, release, and documentation updates.

The release does not add a production model-provider implementation, a PostgreSQL
adapter, distributed task resurrection, remote workflow workers, or a multi-tenant
control plane. These remain explicit extension or roadmap items.

## Architecture

Dependency direction remains inward:

```text
CLI / Server / Muru Workspace
            |
Application + Runtime
            |
SessionStore / ArtifactStore / ApprovalStore protocols
            |
In-memory adapters or SQLite adapters
```

Core runtime code depends on protocols and domain objects only. SQLite implementation
details live in an outward persistence adapter package and use Python's standard-library
`sqlite3` module. React, FastAPI, Databricks, and vendor SDKs do not enter persistence
protocols or domain models.

The runtime will stop relying on mutation of object references returned by an in-memory
store. Messages, runs, run-status transitions, events, artifacts, approvals, and
idempotency keys will be written through explicit store operations. Both adapter families
must exhibit the same observable behavior.

## Persistence Composition and Public API

`SQLitePersistence` is the ergonomic public entry point:

```python
from agentmuru import Agent, Application, FakeModel, Runtime, SQLitePersistence

persistence = SQLitePersistence("agentmuru.db")
application = Application(
    agent=Agent(
        name="assistant",
        instructions="Help the user with governed tools.",
        model=FakeModel.responses("Ready."),
    ),
    session_store=persistence.sessions,
    artifact_store=persistence.artifacts,
)
runtime = Runtime(application, approvals=persistence.approval_service())
```

The persistence object owns schema initialization and exposes session, artifact, and
approval adapters sharing the same database path and codec rules. Existing in-memory
defaults remain unchanged, so the smallest AgentMuru application needs no configuration.

The session protocol gains explicit operations for appending messages, creating runs,
updating run status, and recording idempotency keys. The approval layer gains an
`ApprovalStore` protocol used by `ApprovalService`. Compatibility is behavioral rather
than nominal: existing custom session stores receive a documented migration path for the
new protocol methods.

## SQLite Schema and Serialization

The first schema version contains:

- `schema_metadata` for the current migration version;
- `sessions` for identity, ownership, title, metadata, and timestamps;
- `messages` for ordered user, assistant, tool, and system messages;
- `runs` for agent ownership, status, completion, and safe error codes;
- `event_counters` for each session's next sequence;
- `events` for complete typed runtime envelopes;
- `artifacts` for kind, content encoding, MIME type, creator, metadata, and timestamps;
- `approvals` for request, redacted arguments, decision, actor, reason, and expiry;
- `idempotency_keys` for session-scoped submission identity.

Foreign keys are enabled and destructive cascades are limited to records that have no
meaning outside their owning session. Runtime events remain append-only. A unique index
on `(session_id, sequence)` enforces the ordered event contract independently of Python
logic.

Persistent values support Unicode text, bytes, and finite JSON-compatible values. The
same validation is applied to in-memory and SQLite artifacts so adapter selection cannot
silently change accepted public inputs. Serialization failures occur before beginning a
write transaction and expose a stable `storage_serialization` error without leaking raw
content.

## Concurrency, Ordering, and Subscriptions

Each connection enables foreign keys, WAL journal mode, and a 5-second busy timeout.
Event sequence allocation uses this transaction:

```text
BEGIN IMMEDIATE
  -> read and increment the session counter
  -> insert the event with the allocated sequence
  -> update the session timestamp
COMMIT
  -> publish only the committed event
```

Busy or locked transactions receive bounded exponential retries. Retry exhaustion raises
the stable `storage_busy` error. Tests will use separate store instances and separate
processes to prove unique, monotonically increasing per-session sequences and transaction
rollback. The documentation will state that SQLite targets local and modestly concurrent
deployments; sustained multi-tenant write concurrency belongs on a future PostgreSQL
adapter.

SQLite subscriptions combine immediate in-process notification with short polling for
new committed sequence values. This ensures a subscriber observes writes made by another
store instance without claiming that the in-memory event bus crosses process boundaries.

One SQLite database supports one active AgentMuru runtime process. Multiple store clients
may inspect and append data, but running two independent AgentMuru runtimes against one
database is unsupported. At startup, a runtime marks nonterminal runs left by the previous
process as failed with `process_interrupted`; it retains their messages, events, artifacts,
approval audit records, and last known state. Python tasks are never presented as
resurrectable after process death.

## Qualification Strategy

Qualification is performed against built artifacts, not only the source checkout. The
harness will:

1. run the repository's complete Python, frontend, documentation, security, and package
   checks;
2. build the wheel and source distribution;
3. create a clean environment outside the repository;
4. install the wheel and supported optional extras;
5. run `muru version`, `muru doctor`, `muru init`, `muru run`, and `muru dev` checks;
6. execute scenario applications from outside the source tree so imports cannot resolve
   to the checkout accidentally;
7. launch the packaged server and Muru Workspace;
8. exercise HTTP, WebSocket, and browser flows;
9. record exact results in the qualification report.

New behavior and defect fixes follow test-driven development. A test must fail for the
expected missing behavior before implementation and pass after the smallest corrective
change.

## Qualification Matrix

The scenario and test matrix covers:

- model text streaming, structured completion, provider failure, and turn limits;
- synchronous and asynchronous tools;
- generated schemas, invalid arguments, timeouts, retries, and safe failures;
- declared permissions, deny-by-default behavior, redaction, and high-risk policy;
- approval, rejection, timeout, and persisted audit records;
- every artifact kind and each supported persistent content encoding;
- session creation, ownership, messages, runs, ordering, replay, and reconnect cursors;
- idempotent submission and concurrent-session isolation;
- cancellation, terminal failures, safe public errors, usage, spans, and trace projection;
- sequential and conditional workflows, retry behavior, checkpoints, and typed handoffs;
- HTTP validation, authentication, authorization, CSRF behavior, payload limits, and
  WebSocket actions;
- every reducer state and visible Workspace state, including loading, reconnect, denial,
  approval, artifact, trace, empty, cancellation, and failure views;
- SQLite schema creation, reopening, migration rejection, rollback, concurrent writers,
  cross-instance polling, busy exhaustion, and restart recovery;
- CLI, examples, public exports, Python version support, package contents, and bundle size;
- strict MkDocs build, landing lint/build, metadata, accessibility, responsive layout,
  reduced motion, and production smoke checks.

Databricks adapters receive deterministic contract tests for environment resolution,
client boundaries, query execution, Unity Catalog operations, and application service
helpers. Real credential-backed tests run only when the required environment is present.
The qualification report records credential-backed tests as not executed when credentials
are unavailable; it never promotes a contract test into a claim of live-service proof.

## Runnable Scenario Gallery

Examples are small applications rather than disconnected snippets. The gallery includes:

- a minimal streaming agent;
- a governed tool with allowed, denied, approved, rejected, and expired outcomes;
- an artifact-producing analyst;
- a durable SQLite session that is reopened and inspected after restart;
- a deterministic workflow with retry and checkpoint state;
- a typed handoff between two agents;
- a Databricks application that explains its credential requirement before execution.

Every example is import-tested and executed in the clean-wheel qualification environment.
Documentation embeds the same source rather than maintaining divergent copies.

## Landing Page and Product-Family Branding

The existing Next.js landing project in `BrickFlowUI Landing/brickflowui-landing` will be
re-founded as the AgentMuru landing page. It will contain no BrickFlowUI product claims,
legacy component-catalog language, or links to the retired repository identity.

The selected visual direction is **Precision Runtime**. The hero leads with the promise:
"Build agents you can see, steer, and trust." The page then proves that promise through a
Live Workspace event timeline, a concise installation path, governed-tool and durable-state
stories, verified capability evidence, documentation links, and an honest limitations
section.

AgentMuru and DataMuru use the same product-family identity:

- Hybrid Vel Eye geometry as the family mark;
- Peacock Teal `#0A7C7F` as primary;
- Cobalt Wing `#0D5F8A` as secondary;
- Eye Gold `#C48A1F` as a restrained accent;
- Obsidian `#0D0F14`, Mist `#F4F7FB`, and Near Black `#111827` surfaces;
- Inter for interface and body copy, DM Sans for editorial display, and JetBrains Mono for
  code and runtime evidence;
- flat color, exact geometry, quiet confidence, engineer-first copy, and no gradients,
  shadows, hype, or religious illustration.

The AgentMuru wordmark uses `Agent` in Near Black or white and `Muru` in Peacock Teal. The
family mark is redrawn as clean SVG geometry in the landing repository rather than using a
raster screenshot. Favicon, Open Graph, manifest, structured data, sitemap, robots, and
social metadata all use AgentMuru names and current public URLs.

## Documentation System

The MkDocs site becomes the authoritative product manual. It retains concise conceptual
explanations and adds:

- a clean-install quickstart and troubleshooting path;
- a public API reference organized by stable imports;
- a persistence guide with SQLite setup, schema behavior, backup, recovery, concurrency,
  and migration limits;
- a complete cookbook built from the runnable scenarios;
- server and Workspace operation guides;
- security, governance, redaction, and deployment checklists;
- an integration-status page that distinguishes implemented, contract-tested,
  credential-verified, and planned capabilities;
- a qualification report containing commands, environments, results, and limitations;
- an updated architecture decision record and changelog for 0.2;
- a release and migration guide for custom stores affected by explicit mutation methods.

Documentation adopts the DataMuru voice: precise, quietly confident, culturally grounded,
and engineer-first. Claims use evidence and named behavior rather than adjectives. The
MkDocs palette and typography use the same product-family tokens as the landing page while
keeping long-form reading light, accessible, and restrained.

## Roadmap and GitHub Project

The GitHub roadmap will stop presenting legacy BrickFlowUI UI-component epics as active
AgentMuru work. The new outcome-level epic is:

**Qualify AgentMuru with durable local persistence**

Its acceptance signals are:

- built-wheel scenarios pass outside the source checkout;
- SQLite history survives restart and meets the ordering/concurrency contract;
- all supported framework paths have recorded qualification evidence;
- documentation and the production landing page advertise only verified behavior;
- release artifacts pass integrity and installation checks.

Implementation issues will cover persistence, qualification scenarios, documentation,
landing/deployment, and release verification. Relevant legacy issues will be rewritten for
AgentMuru where their outcome still applies; unrelated BrickFlowUI component epics will be
moved out of the active roadmap rather than silently relabeled. The next queued outcomes
after 0.2 are a production model-provider adapter and a PostgreSQL persistence adapter.

GitHub connector operations are preferred for issues and repository metadata. GitHub
Projects will use authenticated project tooling or the user's logged-in browser when the
connector does not expose Projects. The currently invalid local `gh` token is not treated
as evidence that GitHub itself is unavailable.

## Build and Deployment Flow

The landing repository will pin a project-local Vercel CLI version in its lockfile. The
release flow is:

1. run landing unit, lint, type, build, accessibility, and browser checks locally;
2. verify Vercel identity, team scope, and project link;
3. create a preview deployment with the Vercel CLI;
4. smoke-test the preview through Vercel-aware requests and a real browser;
5. promote or deploy the verified build to production;
6. inspect the production deployment, public metadata, responsive behavior, and links.

The core repository will build a wheel, source distribution, bundled Workspace assets, and
strict documentation site. Distribution metadata and contents will be inspected before any
release. GitHub Pages and release artifacts are published only after the full verification
gate. PyPI publishing occurs only when the configured trusted publisher is available and
the release workflow succeeds; otherwise the built artifacts and exact external blocker
are reported without claiming publication.

## Error Handling and Security

Persistence errors use stable public codes: `storage_busy`, `storage_serialization`,
`storage_corrupt`, `storage_migration`, and `process_interrupted`. Raw SQL, filesystem
details, stored content, secrets, and internal exception traces do not cross public API or
browser boundaries.

Approval arguments remain redacted before persistence. Database paths are explicit and
never derived from untrusted session input. SQLite URI features are disabled unless the
application owner opts in through a trusted configuration surface. Filesystem permissions,
backup responsibility, database encryption limits, and the one-runtime-per-file rule are
documented plainly.

## Definition of Done

The milestone is complete only when:

- focused tests demonstrate every new behavior through a recorded red-green cycle;
- the complete Python, frontend, browser, documentation, security, and packaging suites
  pass from a fresh checkout state;
- clean-wheel scenarios pass outside the repository;
- SQLite ordering, rollback, restart, and concurrency tests pass;
- every public example executes successfully in the qualification environment;
- all documentation links, code samples, and capability claims are verified;
- landing preview and production smoke checks pass;
- the AgentMuru roadmap and GitHub project reflect the new milestone and follow-ons;
- built release artifacts pass integrity and installation checks;
- every credential, authentication, service, or publishing limitation is recorded as a
  blocker rather than hidden behind a success claim.
