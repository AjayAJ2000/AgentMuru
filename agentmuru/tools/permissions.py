from __future__ import annotations

from enum import Enum

from .base import ApprovalMode, RiskLevel, Tool


class PermissionDecision(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"


class PermissionPolicy:
    def evaluate(self, tool: Tool, *, granted_permissions: set[str] | frozenset[str]) -> PermissionDecision:
        if tool.permission and tool.permission not in granted_permissions:
            return PermissionDecision.DENY
        if tool.approval is ApprovalMode.REQUIRED:
            return PermissionDecision.REQUIRE_APPROVAL
        if tool.approval is ApprovalMode.AUTO and tool.risk in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            return PermissionDecision.REQUIRE_APPROVAL
        return PermissionDecision.ALLOW
