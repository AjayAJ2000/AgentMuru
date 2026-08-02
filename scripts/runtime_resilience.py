from __future__ import annotations

"""Run a bounded real-WebSocket resilience check against the counter example."""

import argparse
import asyncio
import json
import math
import os
import signal
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import median
from urllib.error import URLError
from urllib.request import urlopen

import websockets


REPO_ROOT = Path(__file__).resolve().parents[1]
COUNTER_APP = REPO_ROOT / "examples" / "counter" / "app.py"


@dataclass(frozen=True)
class ResilienceResult:
    sessions: int
    cycles: int
    successful_events: int
    reconnects: int
    failures: tuple[str, ...]
    median_ms: float
    p95_ms: float
    duration_ms: float


def percentile(values: list[float], percentile_value: float) -> float:
    """Return a nearest-rank percentile for a non-empty sample."""
    if not values:
        raise ValueError("percentile requires at least one value")
    if not 0 < percentile_value <= 100:
        raise ValueError("percentile value must be greater than 0 and at most 100")
    ordered = sorted(values)
    index = max(0, math.ceil((percentile_value / 100) * len(ordered)) - 1)
    return ordered[index]


def find_event_id(tree: dict, label: str) -> str:
    """Find the click event identifier for a named Button VNode."""
    if tree.get("type") == "Button":
        props = tree.get("props", {})
        if props.get("label") == label and props.get("click"):
            return str(props["click"])
    for child in tree.get("children", []):
        if not isinstance(child, dict):
            continue
        try:
            return find_event_id(child, label)
        except ValueError:
            pass
    raise ValueError(f"button {label!r} was not found in the rendered tree")


def _spawn_counter(port: int) -> subprocess.Popen[str]:
    env = os.environ.copy()
    env["DATABRICKS_APP_PORT"] = str(port)
    env.setdefault("PYTHONUNBUFFERED", "1")
    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
    return subprocess.Popen(
        [sys.executable, str(COUNTER_APP)],
        cwd=str(COUNTER_APP.parent),
        env=env,
        # A PIPE can fill under concurrent connect/disconnect logging and block
        # the server itself, producing false handshake timeouts in this check.
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=creationflags,
    )


def _server_output(process: subprocess.Popen[str]) -> str:
    if process.stdout is None or process.poll() is None:
        return ""
    return "\n".join((process.stdout.read() or "").splitlines()[-12:])


def _wait_for_server(process: subprocess.Popen[str], port: int, timeout: float) -> None:
    deadline = time.monotonic() + timeout
    url = f"http://127.0.0.1:{port}/"
    while time.monotonic() < deadline:
        if process.poll() is not None:
            detail = _server_output(process)
            raise RuntimeError(f"counter server exited before startup\n{detail}".rstrip())
        try:
            with urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return
        except URLError:
            pass
        time.sleep(0.2)
    raise TimeoutError(f"counter server did not become ready at {url}")


def _terminate_process(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
        return
    except subprocess.TimeoutExpired:
        pass
    if os.name != "nt":
        os.killpg(process.pid, signal.SIGKILL)
    else:
        process.kill()
    process.wait(timeout=3)


async def _receive_json(websocket, timeout: float) -> dict:
    raw = await asyncio.wait_for(websocket.recv(), timeout=timeout)
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError("WebSocket payload was not an object")
    return payload


async def _run_session(
    session_index: int,
    uri: str,
    cycles: int,
    event_timeout: float,
) -> tuple[list[float], list[str]]:
    latencies: list[float] = []
    failures: list[str] = []
    for cycle in range(cycles):
        try:
            async with websockets.connect(
                uri,
                open_timeout=event_timeout,
                close_timeout=event_timeout,
            ) as websocket:
                full = await _receive_json(websocket, event_timeout)
                if full.get("type") != "full":
                    raise ValueError(f"expected full render, received {full.get('type')!r}")
                event_id = find_event_id(full["tree"], "+")
                started = time.perf_counter()
                await websocket.send(
                    json.dumps({"type": "event", "event_id": event_id, "data": {}})
                )
                saw_patch = False
                saw_complete = False
                while not (saw_patch and saw_complete):
                    message = await _receive_json(websocket, event_timeout)
                    saw_patch = saw_patch or message.get("type") == "patch"
                    saw_complete = saw_complete or message.get("type") == "event_complete"
                    if message.get("type") == "error":
                        raise RuntimeError("server returned a redacted runtime error")
                latencies.append((time.perf_counter() - started) * 1000)
        except Exception as exc:
            failures.append(
                f"session={session_index} cycle={cycle} error={type(exc).__name__}: {exc}"
            )
    return latencies, failures


async def _run_clients(
    sessions: int,
    cycles: int,
    port: int,
    deadline: float,
    event_timeout: float,
) -> tuple[list[float], list[str]]:
    uri = f"ws://127.0.0.1:{port}/events?path=%2F"
    tasks = [
        _run_session(index, uri, cycles, event_timeout)
        for index in range(sessions)
    ]
    results = await asyncio.wait_for(asyncio.gather(*tasks), timeout=deadline)
    latencies = [latency for result, _ in results for latency in result]
    failures = [failure for _, errors in results for failure in errors]
    return latencies, failures


def run_resilience(
    sessions: int,
    cycles: int,
    port: int,
    deadline: float,
    max_p95_ms: float,
) -> ResilienceResult:
    if sessions < 1 or cycles < 1:
        raise ValueError("sessions and cycles must be at least 1")
    if deadline <= 0 or max_p95_ms <= 0:
        raise ValueError("deadline and max-p95-ms must be greater than 0")

    started = time.perf_counter()
    process = _spawn_counter(port)
    try:
        _wait_for_server(process, port, timeout=min(15.0, deadline))
        event_timeout = min(5.0, max(1.0, deadline / max(1, cycles)))
        latencies, failures = asyncio.run(
            _run_clients(sessions, cycles, port, deadline, event_timeout)
        )
    finally:
        _terminate_process(process)

    measured_median = median(latencies) if latencies else 0.0
    measured_p95 = percentile(latencies, 95) if latencies else 0.0
    if measured_p95 > max_p95_ms:
        failures.append(
            f"p95 latency {measured_p95:.2f} ms exceeded {max_p95_ms:.2f} ms"
        )
    expected_events = sessions * cycles
    if len(latencies) != expected_events:
        failures.append(
            f"received {len(latencies)} successful events; expected {expected_events}"
        )

    return ResilienceResult(
        sessions=sessions,
        cycles=cycles,
        successful_events=len(latencies),
        reconnects=sessions * max(0, cycles - 1),
        failures=tuple(failures),
        median_ms=round(measured_median, 2),
        p95_ms=round(measured_p95, 2),
        duration_ms=round((time.perf_counter() - started) * 1000, 2),
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sessions", type=int, default=20)
    parser.add_argument("--cycles", type=int, default=3)
    parser.add_argument("--port", type=int, default=9180)
    parser.add_argument("--deadline", type=float, default=30.0)
    parser.add_argument("--max-p95-ms", type=float, default=1000.0)
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        result = run_resilience(
            sessions=args.sessions,
            cycles=args.cycles,
            port=args.port,
            deadline=args.deadline,
            max_p95_ms=args.max_p95_ms,
        )
    except Exception as exc:
        print(json.dumps({"failures": [f"{type(exc).__name__}: {exc}"]}, sort_keys=True))
        return 1
    print(json.dumps(asdict(result), sort_keys=True))
    return 1 if result.failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
