# BrickflowUI Geometric UI

## Use this skill when

Use this skill when the goal is a geometry-led, glassmorphism-heavy, image-led,
editorial, or product-showcase surface rather than a traditional operator
dashboard.

Read the repo-root [SKILL.md](D:\Projects\brickflowUI\brickflowUI\SKILL.md)
first. This file is the design-led overlay.

## Mission

Make the agent think like a design-system engineer and product designer working
inside a Python-first framework.

The result should feel like:

- a premium product surface
- a concept-grade launch or showcase page
- a deliberate internal portal with strong visual authorship

It should not feel like:

- a dashboard wearing a gradient
- rounded cards pasted onto a generic grid
- a poster that stops behaving like an application

## Primary users

Optimize for:

1. data and AI teams needing a premium front door
2. design-conscious internal tools teams
3. product evaluators testing whether BrickflowUI can move beyond admin UI
4. engineers proving that Python-first authoring can still deliver deliberate UI

## Baseline example

Start from:

- `examples/geometric_signal_lab/app.py`

That example is the current proof point for:

- rounded shell
- pill navigation
- hero-led composition
- image-driven right rail
- geometric recent-work cards
- branded loading assets

## Composition model

Always build in layers:

1. shell layer
2. hero layer
3. support layer
4. showcase layer

### Shell layer

- rounded outer frame
- pill nav or top rail
- clear brand anchor
- action icons or secondary controls

### Hero layer

- one dominant phrase
- one emphasized phrase or capsule
- one main visual
- a left/right desktop balance that feels intentional

### Support layer

- short supporting copy
- CTA row
- minimal metadata pills

### Showcase layer

- recent-work cards
- feature cases
- concept cards
- carousel or rotation controls only if they change something real

## BrickflowUI primitives to prefer

- `Card` for glass and shell surfaces
- `Row` and `Column` for major composition
- `Grid` or `Row` for case cards
- `Image` for hero art and case art
- `Button` for pills, actions, and arrows
- `Badge` for compact metadata
- `Popup` or `Drawer` for explainer overlays

## Desktop-first rules

- The reference composition should be solved as desktop-first first.
- Do not let the page collapse into a portrait poster before the desktop layout is credible.
- Right-side hero visuals should feel integrated, not boxed-in unless the reference genuinely uses a device frame.
- Recent-work cards should match the intended aspect ratio of the source reference. If the reference uses short wide cards, do not accept tall cards as "close enough."

## Styling rules

- Use large radius values deliberately.
- Keep the gradient calm and the glow zones limited.
- Pair translucent fills with visible borders.
- Shadows should lift the surface without muddying it.
- Typography must remain readable in light mode.
- Use real local SVG or PNG art when the design language depends on bespoke visuals.

## Typography rules

- Usually one large phrase plus one emphasized phrase.
- Emphasis should come from hierarchy and containment, not random font changes.
- Supporting copy should stay short enough that the art can still lead.
- If the layout becomes dense, cut copy before cutting spacing.

## Interaction rules

- Navigation pills should either change the visible surface or clearly read as state.
- Arrow controls should rotate or switch real showcased content.
- CTAs should open a popup, drawer, route, or meaningful state change.
- Do not imitate filters from a reference if the page has no real filtering logic.

## Quality rules

- The page must read in five seconds.
- The hero visual must be large enough to matter.
- The app must still boot cleanly and survive theme changes.
- If exact fidelity depends on a framework primitive that does not exist, document that gap honestly.
- "Looks expensive" is not enough if spacing, proportions, and hierarchy are wrong.

## Known framework friction points

These are the main friction points for inch-by-inch geometric fidelity today:

- `IconButton`
- `SegmentedControl`
- `Stack` / absolute overlay helper
- `AspectFrame`
- first-class glass surface tokens
- stronger display typography control
- breakpoint-aware shell helpers
- stronger hero-media/image placement controls

## Validation

After changes, run:

```bash
python scripts/smoke_examples.py
python -m pytest -q tests/test_examples.py tests/test_app_server.py
```

Then compare the result against the reference on a desktop viewport first.

## Anti-patterns

- do not fake premium art with empty boxes
- do not accept portrait composition when the reference is landscape-first
- do not let glowing backgrounds replace clear information hierarchy
- do not overfit to one screenshot if the page stops behaving like a usable app
- do not hide missing primitives in brittle style hacks

## Prompt shapes

- "Use the BrickflowUI geometric UI skill and rebuild this reference as close as possible in a desktop-first composition."
- "Turn this reference into a premium BrickflowUI showcase and explicitly document which missing primitives prevent inch-perfect fidelity."
- "Adapt geometric_signal_lab into a closer product-grade match for this reference without breaking the runtime or faking the interactions."

## Done means

- the page feels like a composed product surface
- the hero visual leads
- cards and pills repeat on a clear rhythm
- interactions are real
- remaining pixel-fidelity gaps are documented as framework roadmap items
