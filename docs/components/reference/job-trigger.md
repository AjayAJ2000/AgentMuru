# JobTrigger

## What It Does

Starts a Databricks job run from the UI.

## Signature

```python
db.JobTrigger(job_id: 'str', label: 'str' = 'Run Job', on_complete: 'Optional[Callable[[Dict[str, Any]], None]]' = None, on_trigger: 'Optional[Callable[[Dict[str, Any]], None]]' = None, status: 'Optional[str]' = None, run_id: 'Optional[str]' = None, loading: 'bool' = False, error: 'Optional[str]' = None, disabled: 'bool' = False) -> 'VNode'
```

## Parameters

| Name | Type | Default | Notes |
| --- | --- | --- | --- |
| `job_id` | `str` | `required` | |
| `label` | `str` | `'Run Job'` | |
| `on_complete` | `Optional[Callable[[Dict[str, Any]], None]]` | `None` | |
| `on_trigger` | `Optional[Callable[[Dict[str, Any]], None]]` | `None` | |
| `status` | `Optional[str]` | `None` | |
| `run_id` | `Optional[str]` | `None` | |
| `loading` | `bool` | `False` | |
| `error` | `Optional[str]` | `None` | |
| `disabled` | `bool` | `False` | |

## Example

```python
import brickflowui as db

node = db.JobTrigger(job_id="job_id", label="Pipeline health")
```

## Integration Notes

- This component composes cleanly with layout primitives such as `Card`, `Grid`, `Row`, and `Column`.
- Prefer controlled state from Python when the value matters to your business logic or backend query layer.

## Responsive Notes

Check the component inside a realistic layout, not only in isolation, so spacing, overflow, and action density stay comfortable on smaller screens.

## Accessibility Notes

Pair this component with clear visible copy and predictable state changes so keyboard and assistive-technology users are not surprised.
