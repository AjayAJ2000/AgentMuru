from __future__ import annotations

"""Collect read-only, sanitized release evidence from a Databricks workspace."""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


RESOURCE_KEYS = ("catalog", "warehouse", "job")


def redact_origin(url: str) -> str:
    """Keep only a URL's scheme and hostname/port, dropping credentials and paths."""
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("app URL must be an absolute http or https URL")
    host = parsed.hostname
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    if parsed.port:
        host = f"{host}:{parsed.port}"
    return urlunsplit((parsed.scheme, host, "", "", ""))


def validate_results(results: list[dict[str, Any]]) -> list[str]:
    """Validate two-user identity and permission evidence."""
    errors: list[str] = []
    if len(results) != 2:
        return ["validation requires exactly two profiles"]

    subjects = [str(result.get("subject") or "") for result in results]
    if not all(subjects) or subjects[0] == subjects[1]:
        errors.append("profiles must resolve to two different subjects")

    owner = results[0]
    for resource in RESOURCE_KEYS:
        if owner.get(resource) is not True:
            errors.append(f"profile A must be able to read the {resource} resource")

    if not any(
        bool(results[0].get(resource)) != bool(results[1].get(resource))
        for resource in RESOURCE_KEYS
    ):
        errors.append("profiles must demonstrate at least one permission difference")
    return errors


def _probe(call: Callable[[], Any]) -> tuple[bool, str | None]:
    try:
        call()
    except Exception as exc:  # SDK exception text may contain request details; keep type only.
        return False, type(exc).__name__
    return True, None


def _subject(me: Any) -> str:
    for attribute in ("user_name", "display_name", "id"):
        value = getattr(me, attribute, None)
        if value:
            return str(value)
    return ""


def _collect_profile(client: Any, profile: str, args: argparse.Namespace) -> dict[str, Any]:
    result: dict[str, Any] = {"profile": profile}
    try:
        result["subject"] = _subject(client.current_user.me())
    except Exception as exc:
        result["subject"] = ""
        result["identity_error"] = type(exc).__name__

    probes = {
        "catalog": lambda: client.catalogs.get(name=args.catalog),
        "warehouse": lambda: client.warehouses.get(id=args.warehouse_id),
        "job": lambda: client.jobs.get(job_id=int(args.job_id)),
    }
    for resource, call in probes.items():
        allowed, error_type = _probe(call)
        result[resource] = allowed
        if error_type:
            result[f"{resource}_error"] = error_type
    return result


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: N802
        return None


def _probe_app_root(client: Any, app_url: str) -> dict[str, Any]:
    result: dict[str, Any] = {"origin": redact_origin(app_url), "reachable": False}
    try:
        headers = dict(client.config.authenticate())
        request = Request(app_url, headers=headers, method="GET")
        with build_opener(_NoRedirect).open(request, timeout=10) as response:
            result["status"] = int(response.status)
            result["reachable"] = 200 <= response.status < 300
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        result["error"] = type(exc).__name__
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app-url", required=True, help="Authenticated Databricks App root URL")
    parser.add_argument("--profile-a", required=True, help="Databricks CLI profile with full read access")
    parser.add_argument("--profile-b", required=True, help="A different Databricks CLI profile")
    parser.add_argument("--catalog", required=True, help="Catalog name to read")
    parser.add_argument("--warehouse-id", required=True, help="SQL warehouse ID to read")
    parser.add_argument("--job-id", required=True, help="Job ID to read without running it")
    parser.add_argument("--output", required=True, type=Path, help="Path for sanitized JSON evidence")
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        from databricks.sdk import WorkspaceClient
    except ImportError:
        print(
            "Prerequisite missing: install the Databricks SDK and configure two CLI profiles.",
            file=sys.stderr,
        )
        return 2

    try:
        clients = [WorkspaceClient(profile=args.profile_a), WorkspaceClient(profile=args.profile_b)]
        results = [
            _collect_profile(clients[0], args.profile_a, args),
            _collect_profile(clients[1], args.profile_b, args),
        ]
        validation_errors = validate_results(results)
        app_root = _probe_app_root(clients[0], args.app_url)
        if not app_root["reachable"]:
            validation_errors.append("profile A could not read the authenticated app root")

        evidence = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "app_root": app_root,
            "resources": {
                "catalog": args.catalog,
                "warehouse_id": args.warehouse_id,
                "job_id": str(args.job_id),
            },
            "profiles": results,
            "validation_errors": validation_errors,
        }
        encoded = json.dumps(evidence, indent=2, sort_keys=True)
        lowered = encoded.lower()
        if any(forbidden in lowered for forbidden in ('"token"', '"authorization"', '"password"')):
            raise RuntimeError("evidence contained a forbidden credential field")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(f"{encoded}\n", encoding="utf-8")
        print(f"Wrote sanitized evidence to {args.output}")
        if validation_errors:
            print("Workspace validation failed; inspect validation_errors in the evidence file.", file=sys.stderr)
            return 1
        print("Workspace validation passed.")
        return 0
    except Exception as exc:
        print(f"Workspace validation failed safely: {type(exc).__name__}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
