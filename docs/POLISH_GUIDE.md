# Polish Guide

BrickflowUI `0.1.13` focuses on making the framework more dependable, more polished, and more capable without forcing API churn.

## What changed

The release adds a safer visual polish layer on top of the current component model:

- motion-ready cards and buttons
- animated KPI values
- progress fill animation
- drawer, accordion, toast, breadcrumbs, timeline, and sparkline primitives
- better empty and loading states
- theme tokens for surfaces, shadows, and motion
- table CSV export

## Safe additive props

These are additive and optional.

### Visual polish

- `animated=True`
- `animation="fade-up"`
- `animation_delay=0.1`
- `elevated=True`

### State-aware rendering

- `loading=True`
- `empty_message="No rows yet"`
- `exportable=True`

## Example

```python
db.Card(
    [
        db.Stat(
            "Freshness",
            "17 min",
            delta="-4 min",
            delta_type="decrease",
            animated=True,
        ),
    ],
    elevated=True,
    animated=True,
    animation="fade-up",
    animation_delay=0.1,
)
```

## Design patterns that now work well

- premium executive dashboards
- pipeline command centers
- chatbot-style workspaces
- landing pages and internal microsites
- launch or product announcement pages

## Reliability notes

The polish layer was shipped with reliability in mind:

- existing examples still render without code changes
- multi-value inputs now round-trip safely through forms
- object-style input payloads such as date ranges are preserved
- charts support loading and empty states directly
- table exports do not change existing table behavior unless enabled

