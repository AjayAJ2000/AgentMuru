# WarehouseSelector

## What It Does

Selects a Databricks SQL warehouse from the current environment.

## Signature

```python
db.WarehouseSelector(on_select: 'Optional[Callable[[str], None]]' = None, selected_id: 'Optional[str]' = None, label: 'str' = 'SQL Warehouse', warehouses: 'Optional[List[Dict[str, Any]]]' = None, loading: 'bool' = False, error: 'Optional[str]' = None, empty_message: 'str' = 'No warehouses available', disabled: 'bool' = False) -> 'VNode'
```

## Parameters

| Name | Type | Default | Notes |
| --- | --- | --- | --- |
| `on_select` | `Optional[Callable[[str], None]]` | `None` | |
| `selected_id` | `Optional[str]` | `None` | |
| `label` | `str` | `'SQL Warehouse'` | |
| `warehouses` | `Optional[List[Dict[str, Any]]]` | `None` | |
| `loading` | `bool` | `False` | |
| `error` | `Optional[str]` | `None` | |
| `empty_message` | `str` | `'No warehouses available'` | |
| `disabled` | `bool` | `False` | |

## Example

```python
import brickflowui as db

node = db.WarehouseSelector(label="Pipeline health")
```

## Integration Notes

- This component composes cleanly with layout primitives such as `Card`, `Grid`, `Row`, and `Column`.
- Prefer controlled state from Python when the value matters to your business logic or backend query layer.

## Responsive Notes

Check the component inside a realistic layout, not only in isolation, so spacing, overflow, and action density stay comfortable on smaller screens.

## Accessibility Notes

Pair this component with clear visible copy and predictable state changes so keyboard and assistive-technology users are not surprised.
