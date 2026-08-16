from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / "packs" / "action-router"
SCHEMAS = ROOT / "schemas" / "agent-pack" / "v1"


def test_action_router_uses_the_public_v1_contract() -> None:
    manifest = json.loads((PACK / "manifest.json").read_text(encoding="utf-8"))
    agents = json.loads((PACK / "agents.json").read_text(encoding="utf-8"))
    actions = json.loads((PACK / "actions.json").read_text(encoding="utf-8"))
    policy = json.loads((PACK / "policy.json").read_text(encoding="utf-8"))

    assert manifest == {
        "schema_version": "agent-pack.agentmuru.dev/v1",
        "id": "action-router",
        "name": "Local action router",
        "version": "1.0.0",
        "entry_agent": "router",
        "max_hops": 4,
        "effects": "simulate",
    }
    assert {agent["id"] for agent in agents} == {"router"}
    assert {action["id"] for action in actions} == {
        "classify_document",
        "search_files",
        "summarize_text",
    }
    assert policy["network_mode"] == "offline"


def test_action_router_has_the_required_eval_distribution() -> None:
    cases = [json.loads(line) for line in (PACK / "evals.jsonl").read_text(encoding="utf-8").splitlines()]
    assert Counter(case["category"] for case in cases) == {
        "accepted": 20,
        "ambiguous": 5,
        "rejected": 5,
        "unsafe": 10,
    }


def test_action_router_checksums_cover_every_runtime_file() -> None:
    declared = {}
    for line in (PACK / "checksums.txt").read_text(encoding="utf-8").splitlines():
        digest, name = line.split()
        declared[name] = digest
    expected = {"manifest.json", "agents.json", "actions.json", "policy.json", "evals.jsonl", "prompts/router.txt"}
    assert set(declared) == expected
    for name, digest in declared.items():
        assert hashlib.sha256((PACK / name).read_bytes()).hexdigest() == digest


def test_all_public_agent_pack_schemas_are_strict_where_applicable() -> None:
    names = {path.name for path in SCHEMAS.glob("*.schema.json")}
    assert names == {
        "manifest.schema.json",
        "agents.schema.json",
        "actions.schema.json",
        "policy.schema.json",
        "eval.schema.json",
    }
    for path in SCHEMAS.glob("*.schema.json"):
        schema = json.loads(path.read_text(encoding="utf-8"))
        assert schema["$schema"].endswith("2020-12/schema")
        if schema["type"] == "object":
            assert schema["additionalProperties"] is False
