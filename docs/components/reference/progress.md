# Progress

## What It Does

Displays completion, readiness, or processing percentages.

## Signature

```python
db.Progress(value: 'float', max: 'float' = 100, label: 'Optional[str]' = None, color: 'str' = 'blue') -> 'VNode'
```

## Parameters

| Name | Type | Default | Notes |
| --- | --- | --- | --- |
| `value` | `float` | `required` | |
| `max` | `float` | `100` | |
| `label` | `Optional[str]` | `None` | |
| `color` | `str` | `'blue'` | |

## Example

```python
import brickflowui as db

node = db.Progress(value=85, label="Pipeline health")
```

## Integration Notes

- The fill width is calculated as `value / max`, capped at 100 percent.
- Friendly colors map to theme tokens: `blue` uses primary, `green` uses success, `orange` or `yellow` uses warning, and `red` uses error.
- You can also pass an explicit CSS color such as `#2563eb` or `var(--custom-progress)`.

## Responsive Notes

Check the component inside a realistic layout, not only in isolation, so spacing, overflow, and action density stay comfortable on smaller screens.

## Accessibility Notes

Pair this component with clear visible copy and predictable state changes so keyboard and assistive-technology users are not surprised.
