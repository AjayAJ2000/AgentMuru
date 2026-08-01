# BrickflowUI App Starter

## Use this skill when

Use this skill when an agent needs to start a new BrickflowUI app, reshape an
existing one, or choose the right example and shell pattern before building.

This skill is not a replacement for the repo-root [SKILL.md](../../SKILL.md).
Read that file first. Then use this skill as the execution overlay for the
"how do I start correctly?" part.

## Mission

Make the agent behave like a senior product engineer who knows that:

- the first version should already have believable structure
- example quality matters as much as component coverage
- data and AI teams need product surfaces, not widget piles
- future auth, deployment, and governance needs should influence the first draft

## Target users

Optimize for:

1. data platform teams
2. AI application teams
3. analytics engineers
4. internal tools teams
5. enterprise evaluators

## Non-negotiable rules

- Review the closest maintained example in `examples/` and reuse only the patterns that fit the requested product.
- Use `import brickflowui as db`.
- Establish the app shell before fine-tuning charts or tables.
- Every control must change visible state.
- Prefer named helper functions over giant inline trees when patterns repeat.
- Build for desktop first, but do not ignore mobile/tablet collapse behavior.

## Required preload

Before building anything, review:

1. repo-root `SKILL.md`
2. the closest example in `examples/`
3. `docs/EXAMPLES.md` if the user is choosing between examples

## Build order

Follow this order unless there is a strong reason not to:

1. Choose the maintained example references that match the product shape.
2. Identify the operator's top three questions.
3. Pick the shell:
   - multipage portal -> `Sidebar`
   - horizontal product shell -> `TopNav`
   - single focused workflow -> `Hero` + `SectionHeader` + `Drawer` / `Modal`
4. Define all `use_state` declarations at the top of the page.
5. Add one control plane that drives visible outcomes.
6. Add loading, empty, and success states.
7. Add drilldown or follow-up action.
8. Only then add extra visual polish.

## Maintained example reference matrix

Choose references by product shape:

- secure internal tool -> `examples/auth_portal/app.py`
- data and AI operations portal -> `examples/data_pipeline_command_center/app.py`
- regulated multipage workflow -> `examples/clinical_trial_command_center/app.py`
- broad interactive component coverage -> `examples/component_studio/app.py`
- assistant or copilot workspace -> `examples/chatbot_workspace/app.py`
- minimal runtime or state check -> `examples/counter/app.py`

If no example fits perfectly, combine supported patterns from the nearest maintained references and explain the tradeoff.

## Shell patterns to prefer

### Multipage operations portal

Use:
- `Sidebar`
- `Hero`
- `StatusStrip`
- `SectionHeader`
- `Table`
- `Drawer`

### Executive or analytics workspace

Use:
- `TopNav` or `Sidebar`
- `Hero`
- KPI grid
- 2 to 4 charts
- one action table

### AI workspace or copilot

Use:
- `Sidebar` or `TopNav`
- `ChatMessage`
- `ChatInput`
- nearby telemetry cards
- drawer/timeline/table as supporting evidence surfaces

### Design-led or editorial surface

Use:
- `Card`
- `Row`
- `Column`
- `Image`
- `Badge`
- rounded CTA buttons
- minimal, honest interactivity

## Structural rules

- The top fold must explain what the app is for.
- The page should have a clear order: identity -> health -> visuals -> operational detail -> action.
- If there is row or node data, provide drilldown.
- If there are three or more related KPIs, use a deliberate KPI grid or `StatusStrip`.
- If the page would feel empty without charts, the shell is probably too weak.

## State and performance rules

- Inputs must bind to `use_state`.
- Use debounced sync for text-heavy inputs unless real-time typing is truly needed.
- Never mutate lists or dicts in place and expect a rerender.
- Keep large derived datasets memoized or computed carefully.
- Split heavy pages into sections or tabs instead of rendering every expensive surface at once.

## Design rules

- Build product hierarchy, not just component coverage.
- Use spacing rhythm deliberately.
- Avoid ad hoc padding changes on every card.
- Let one section lead; do not make every section compete for attention.
- If the app is meant to sell a concept, reserve the fold for one strong idea.

## Documentation rules

- If the new app becomes a meaningful proof point, update `docs/EXAMPLES.md`.
- If a new capability was required, update the relevant docs page.
- Keep versions aligned in examples, docs, and templates when the library version changes.

## Validation checklist

Before considering the work complete:

```bash
python scripts/smoke_examples.py
python -m pytest -q tests/test_examples.py tests/test_app_server.py
```

Then run the touched example directly.

## Anti-patterns

- Do not start from `counter` when a domain example exists.
- Do not build pages that are only `Text` plus `Table`.
- Do not create fake interactions that leave state unchanged.
- Do not add charts before deciding what decisions the user needs to make.
- Do not ship a flagship example that looks worse than the existing promoted examples.

## Prompt shapes

- "Use the BrickflowUI app starter skill and the maintained examples as references for a data and AI operations portal with a real app shell and drilldown drawer."
- "Use the maintained BrickflowUI references for a secure internal AI workspace and implement the first production-grade page."
- "Build a serious BrickflowUI app surface, not a demo, and explain which maintained examples informed the result."

## Done means

- the app boots locally
- the shell is believable
- at least one control visibly changes state
- loading/empty states exist where needed
- the result looks like a product surface that can grow, not a one-off demo
