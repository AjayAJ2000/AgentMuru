# BrickflowUI Polish + QA

## Use this skill when

Use this skill when an app works functionally but still feels rough, laggy,
inconsistent, visually unfinished, or unconvincing for evaluation.

Read the repo-root [SKILL.md](../../SKILL.md)
first. This file is the release-quality overlay.

## Mission

Make the agent behave like a staff engineer and senior product designer doing a
ship/no-ship review.

The goal is not "make it prettier." The goal is to make it:

- smoother
- clearer
- more honest
- more resilient
- more believable to a buyer or evaluator

## Audit order

Always review in this order:

1. interaction smoothness
2. loading / disabled / empty / error states
3. layout rhythm and hierarchy
4. theme parity
5. responsive behavior
6. example honesty
7. code readability
8. docs alignment

## Interaction checks

- text inputs should not feel blocked by backend round-trips
- checkboxes, toggles, sliders, and multiselects must update reliably
- overlapping events should not leave controls stuck in loading
- drawers, modals, popups, and toasts must open and close safely
- chart/table drilldowns must be repeatable and understandable
- controls that look clickable must actually do something

## Loading and empty-state checks

- loading should appear where the user is waiting, not only globally
- tables and charts should have explicit `loading` and `empty_message`
- loaders should not leave the page in a fake or frozen state
- branded loading should not break dark/light mode
- success and error feedback should be visible and dismissible

## Layout and hierarchy checks

- the fold must have a clear anchor
- section gaps must feel intentional and repeatable
- cards should align on a rhythm
- the page should not feel like multiple demos stitched together
- text density should match the page purpose
- reduce clutter before shrinking typography

## Theme checks

- dark and light modes both need readable text
- shadows, borders, and glows must make sense in both modes
- images should not disappear into their backgrounds
- product previews and mini demos need their own contrast-safe local styling if necessary

## Responsive checks

Check at least:

- desktop wide
- laptop
- tablet
- narrow/mobile

Look for:

- nav collapse
- overflow
- broken card aspect ratios
- clipped charts or images
- unreadable tables
- awkward gap scaling

## Design-led surface checks

For editorial, geometric, or showcase-heavy surfaces:

- hero art must be large enough to matter
- short desktop cards should not collapse into accidental poster layouts
- pills, badges, and actions should look related
- gradients and blur should support hierarchy, not hide it
- if a reference cannot be matched exactly, document the missing primitive

## Code and docs checks

- repeated view patterns should be helper functions
- comments should explain intent, not basic syntax
- weak examples should be fixed or de-promoted
- docs should mention any newly proven capability
- skill files, docs, and examples should not contradict each other

## Required validation

Before closing the pass, run:

```bash
python scripts/smoke_examples.py
python -m pytest -q tests/test_examples.py tests/test_app_server.py
python -m mkdocs build --strict -d .site_validation_local
cd frontend
npx tsc --noEmit
```

If the environment blocks build steps, report that clearly and use bounded
validation instead of pretending the release path passed.

## Anti-patterns

- do not add animation to hide structural weaknesses
- do not add more cards when the issue is hierarchy
- do not claim dark-mode support if one mode is visibly broken
- do not leave fake live states in flagship examples
- do not treat docs as optional cleanup after the fact

## Prompt shapes

- "Use the BrickflowUI polish and QA skill to do a release-quality pass on this app: loading, spacing, responsiveness, theme parity, and drilldown quality all matter."
- "Audit this BrickflowUI example like an enterprise evaluator and remove anything that feels fake, laggy, or fragile."
- "Make this BrickflowUI surface feel premium and trustworthy without introducing frontend-only hacks."

## Done means

- controls feel smooth
- loading and empty states are explicit
- spacing and hierarchy are deliberate
- desktop and narrow layouts both work
- docs and examples support the code honestly
