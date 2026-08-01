# CatalogBrowser

## What It Does

Browses Unity Catalog catalogs, schemas, and tables.

## Signature

```python
db.CatalogBrowser(on_select: 'Optional[Callable[[Dict[str, str]], None]]' = None, selected: 'Optional[Dict[str, str]]' = None, catalogs: 'Optional[List[Dict[str, Any]]]' = None, loading: 'bool' = False, error: 'Optional[str]' = None, empty_message: 'str' = 'No catalogs available', disabled: 'bool' = False) -> 'VNode'
```

## Parameters

| Name | Type | Default | Notes |
| --- | --- | --- | --- |
| `on_select` | `Optional[Callable[[Dict[str, str]], None]]` | `None` | |
| `selected` | `Optional[Dict[str, str]]` | `None` | |
| `catalogs` | `Optional[List[Dict[str, Any]]]` | `None` | |
| `loading` | `bool` | `False` | |
| `error` | `Optional[str]` | `None` | |
| `empty_message` | `str` | `'No catalogs available'` | |
| `disabled` | `bool` | `False` | |

## Example

```python
import brickflowui as db

node = db.CatalogBrowser()
```

## Integration Notes

- This component composes cleanly with layout primitives such as `Card`, `Grid`, `Row`, and `Column`.
- Prefer controlled state from Python when the value matters to your business logic or backend query layer.

## Responsive Notes

Check the component inside a realistic layout, not only in isolation, so spacing, overflow, and action density stay comfortable on smaller screens.

## Accessibility Notes

Pair this component with clear visible copy and predictable state changes so keyboard and assistive-technology users are not surprised.
