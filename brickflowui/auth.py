"""Authentication and authorization primitives for BrickflowUI."""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional, Protocol, Sequence

from fastapi import Request, WebSocket

AuthMode = str
AccessLevel = str


class AuthenticationRequired(Exception):
    """Raised when a protected resource requires an authenticated principal."""


class AuthorizationError(Exception):
    """Raised when the current principal lacks the required permissions."""


@dataclass(frozen=True)
class Principal:
    """Normalized identity used across HTTP routes, websocket sessions, and render hooks."""

    subject: str
    principal_type: str = "anonymous"
    display_name: Optional[str] = None
    email: Optional[str] = None
    roles: tuple[str, ...] = ()
    authenticated: bool = False
    attributes: Mapping[str, Any] = field(default_factory=dict)
    access_token: Optional[str] = field(default=None, repr=False, compare=False)

    def has_role(self, role: str) -> bool:
        return role in self.roles


class AuthProvider(Protocol):
    """Pluggable provider that can extract a user principal from requests."""

    def authenticate_request(self, request: Request) -> Optional[Principal]:
        ...

    def authenticate_websocket(self, websocket: WebSocket) -> Optional[Principal]:
        ...


def anonymous_principal() -> Principal:
    return Principal(subject="anonymous", principal_type="anonymous", authenticated=False)


def default_app_principal() -> Principal:
    return Principal(
        subject="brickflowui-app",
        principal_type="app",
        display_name="BrickflowUI App",
        authenticated=True,
    )


class StaticAuthProvider:
    """Always returns the provided principal."""

    def __init__(self, principal: Principal):
        self.principal = principal

    def authenticate_request(self, request: Request) -> Optional[Principal]:
        return self.principal

    def authenticate_websocket(self, websocket: WebSocket) -> Optional[Principal]:
        return self.principal


class HeaderAuthProvider:
    """Resolves an authenticated user from HTTP or websocket headers."""

    def __init__(self, header_prefix: str = "x-brickflow-"):
        prefix = header_prefix.lower()
        self.user_id_header = f"{prefix}user-id"
        self.user_name_header = f"{prefix}user-name"
        self.user_email_header = f"{prefix}user-email"
        self.user_roles_header = f"{prefix}user-roles"
        self.forwarded_user_header = "x-forwarded-user"
        self.forwarded_user_name_header = "x-forwarded-preferred-username"
        self.forwarded_user_email_header = "x-forwarded-email"
        self.user_access_token_header = "x-forwarded-access-token"

    def _from_mapping(self, values: Mapping[str, str]) -> Optional[Principal]:
        subject = values.get(self.user_id_header) or values.get(self.forwarded_user_header)
        if not subject:
            return None

        roles_raw = values.get(self.user_roles_header, "")
        roles = tuple(sorted({role.strip() for role in roles_raw.split(",") if role.strip()}))
        return Principal(
            subject=subject,
            principal_type="user",
            display_name=(
                values.get(self.user_name_header)
                or values.get(self.forwarded_user_name_header)
                or subject
            ),
            email=values.get(self.user_email_header) or values.get(self.forwarded_user_email_header),
            roles=roles,
            authenticated=True,
            access_token=values.get(self.user_access_token_header),
        )

    def authenticate_request(self, request: Request) -> Optional[Principal]:
        return self._from_mapping(request.headers)

    def authenticate_websocket(self, websocket: WebSocket) -> Optional[Principal]:
        return self._from_mapping(websocket.headers)


_current_principal: ContextVar[Principal] = ContextVar(
    "_current_principal", default=anonymous_principal()
)


def set_current_principal(principal: Principal) -> Any:
    return _current_principal.set(principal)


def reset_current_principal(token: Any) -> None:
    _current_principal.reset(token)


def current_principal() -> Principal:
    return _current_principal.get()


def current_user() -> Optional[Principal]:
    principal = current_principal()
    if principal.principal_type == "user" and principal.authenticated:
        return principal
    return None


def current_app_identity() -> Optional[Principal]:
    principal = current_principal()
    if principal.principal_type == "app" and principal.authenticated:
        return principal
    return None


def is_authenticated() -> bool:
    return current_principal().authenticated


def require_auth() -> Principal:
    principal = current_principal()
    if not principal.authenticated:
        raise AuthenticationRequired("Authentication is required.")
    return principal


def require_role(role: str) -> Principal:
    principal = require_auth()
    if not principal.has_role(role):
        raise AuthorizationError(f"Role '{role}' is required.")
    return principal


def authorize_principal(
    principal: Principal,
    access: AccessLevel = "public",
    roles: Optional[Sequence[str]] = None,
) -> Principal:
    """Validate that a principal can access the protected resource."""
    normalized_access = access or "public"

    if normalized_access == "public":
        pass
    elif normalized_access == "authenticated":
        if not principal.authenticated:
            raise AuthenticationRequired("Authentication is required.")
    elif normalized_access == "user":
        if not principal.authenticated or principal.principal_type != "user":
            raise AuthenticationRequired("A signed-in user is required.")
    elif normalized_access == "app":
        if not principal.authenticated or principal.principal_type != "app":
            raise AuthorizationError("This resource is reserved for the application identity.")
    else:
        raise ValueError(f"Unsupported access level: {normalized_access}")

    required_roles = tuple(roles or ())
    if required_roles:
        if not principal.authenticated:
            raise AuthenticationRequired("Authentication is required.")
        missing_roles = [role for role in required_roles if not principal.has_role(role)]
        if missing_roles:
            joined = ", ".join(missing_roles)
            raise AuthorizationError(f"Missing required role(s): {joined}")

    return principal


def resolve_principal(
    *,
    auth_mode: AuthMode,
    auth_provider: Optional[AuthProvider],
    app_principal: Optional[Principal],
    allow_anonymous: bool,
    source: Request | WebSocket,
) -> Principal:
    """Resolve the active principal for a request or websocket session."""
    candidate: Optional[Principal] = None
    if auth_provider is not None:
        if isinstance(source, Request):
            candidate = auth_provider.authenticate_request(source)
        else:
            candidate = auth_provider.authenticate_websocket(source)

    service_principal = app_principal or default_app_principal()

    if auth_mode == "app":
        return service_principal

    if auth_mode == "hybrid":
        return candidate if candidate and candidate.authenticated else service_principal

    if auth_mode == "user":
        if candidate and candidate.authenticated:
            return candidate
        if allow_anonymous:
            return anonymous_principal()
        raise AuthenticationRequired("User authentication is required.")

    raise ValueError(f"Unsupported auth mode: {auth_mode}")
