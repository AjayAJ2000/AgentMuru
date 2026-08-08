from __future__ import annotations

import secrets
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Mapping, Protocol


@dataclass(frozen=True, slots=True)
class Principal:
    subject: str
    authenticated: bool = False
    principal_type: str = "user"
    display_name: str | None = None
    roles: tuple[str, ...] = ()
    attributes: Mapping[str, str] = field(default_factory=dict)
    access_token: str | None = field(default=None, repr=False, compare=False)

    def has_role(self, role: str) -> bool:
        return role in self.roles


ANONYMOUS = Principal(subject="anonymous")
_principal: ContextVar[Principal] = ContextVar("agentmuru_principal", default=ANONYMOUS)


def current_principal() -> Principal:
    return _principal.get()


def set_current_principal(principal: Principal):
    return _principal.set(principal)


def reset_current_principal(token: object) -> None:
    _principal.reset(token)  # type: ignore[arg-type]


class AuthProvider(Protocol):
    def authenticate(self, headers: Mapping[str, str]) -> Principal | None: ...


class StaticAuthProvider:
    def __init__(self, principal: Principal) -> None:
        self.principal = principal

    def authenticate(self, headers: Mapping[str, str]) -> Principal | None:
        return self.principal


class BearerTokenAuth:
    """Small deterministic bearer provider for local/private deployments and tests."""

    def __init__(self, tokens: Mapping[str, Principal]) -> None:
        self._tokens = dict(tokens)

    def authenticate(self, headers: Mapping[str, str]) -> Principal | None:
        authorization = headers.get("authorization", "")
        scheme, _, candidate = authorization.partition(" ")
        if scheme.lower() != "bearer" or not candidate:
            return None
        for token, principal in self._tokens.items():
            if secrets.compare_digest(token, candidate):
                return principal
        return None
