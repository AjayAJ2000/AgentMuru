# Text

## What It Does

Renders headings, body copy, captions, labels, and lightweight code text.

## Signature

```python
db.Text(value: 'str', variant: 'TextVariant' = 'body', color: 'Optional[str]' = None, bold: 'bool' = False, italic: 'bool' = False, muted: 'bool' = False, style: 'Optional[Dict[str, Any]]' = None, class_name: 'Optional[str]' = None) -> 'VNode'
```

## Parameters

| Name | Type | Default | Notes |
| --- | --- | --- | --- |
| `value` | `str` | `required` | |
| `variant` | `TextVariant` | `'body'` | |
| `color` | `Optional[str]` | `None` | |
| `bold` | `bool` | `False` | |
| `italic` | `bool` | `False` | |
| `muted` | `bool` | `False` | |
| `style` | `Optional[Dict[str, Any]]` | `None` | |
| `class_name` | `Optional[str]` | `None` | |

## Example

```python
import brickflowui as db

node = db.Text("Warehouse latency is stable.", variant="body", muted=False)
```

## Integration Notes

- This component composes cleanly with layout primitives such as `Card`, `Grid`, `Row`, and `Column`.
- Prefer controlled state from Python when the value matters to your business logic or backend query layer.

## Responsive Notes

Check the component inside a realistic layout, not only in isolation, so spacing, overflow, and action density stay comfortable on smaller screens.

## Accessibility Notes

Pair this component with clear visible copy and predictable state changes so keyboard and assistive-technology users are not surprised.
