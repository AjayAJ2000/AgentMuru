from dataclasses import dataclass

import pytest

from agentmuru.tools import (
    ApprovalMode,
    PermissionDecision,
    PermissionPolicy,
    ToolExecutionError,
    tool,
)


@dataclass
class Query:
    customer_id: str
    include_history: bool = False


@tool(permission="database.read", description="Look up a customer")
def lookup(query: Query, limit: int = 10) -> dict[str, object]:
    return {"customer_id": query.customer_id, "limit": limit}


def test_tool_derives_json_schema_from_typed_signature() -> None:
    assert lookup.name == "lookup"
    assert lookup.description == "Look up a customer"
    assert lookup.input_schema["required"] == ["query"]
    assert lookup.input_schema["properties"]["limit"]["default"] == 10
    assert lookup.input_schema["properties"]["query"]["properties"]["customer_id"] == {
        "type": "string"
    }


@pytest.mark.asyncio
async def test_tool_validates_and_executes_dataclass_arguments() -> None:
    result = await lookup.invoke({"query": {"customer_id": "c-1"}})

    assert result == {"customer_id": "c-1", "limit": 10}


@pytest.mark.asyncio
async def test_tool_reports_validation_failures_without_calling_handler() -> None:
    with pytest.raises(ToolExecutionError, match="query"):
        await lookup.invoke({"limit": 5})


def test_permission_policy_denies_missing_grant_and_gates_dangerous_tools() -> None:
    @tool(permission="database.write", approval="required", risk="high")
    def update(value: str) -> str:
        return value

    policy = PermissionPolicy()
    assert policy.evaluate(update, granted_permissions=set()) is PermissionDecision.DENY
    assert (
        policy.evaluate(update, granted_permissions={"database.write"})
        is PermissionDecision.REQUIRE_APPROVAL
    )
    assert update.approval is ApprovalMode.REQUIRED


def test_tool_redacts_declared_sensitive_arguments() -> None:
    @tool(sensitive_fields={"token"})
    def publish(token: str, value: str) -> str:
        return value

    assert publish.redact_arguments({"token": "secret", "value": "safe"}) == {
        "token": "[REDACTED]",
        "value": "safe",
    }
