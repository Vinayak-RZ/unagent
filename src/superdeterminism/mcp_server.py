"""Stdio MCP server — thin wrappers over the Unagent library. No recommend logic here."""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, Callable

from superdeterminism.adapters import AdapterError, resolve
from superdeterminism.ingest import IngestError, load_traces_dir, load_traces_path
from superdeterminism.pipeline import (
    N_MIN_DEFAULT,
    inspect_traces,
    recommend_traces,
    recommendations_to_dict,
)
from superdeterminism.scaffold import write_scaffold
from superdeterminism.simulate import (
    simulate_design,
    simulate_report,
    simulate_what_if,
    what_if_to_dict,
)

_PROTOCOL = "2024-11-05"
_SERVER_NAME = "unagent"

_BOUNDARY = (
    AdapterError,
    IngestError,
    OSError,
    ValueError,
    TypeError,
    json.JSONDecodeError,
    UnicodeDecodeError,
    KeyError,
    AttributeError,
    RecursionError,
)


class ToolError(Exception):
    """Tool invocation failed (bad input or library boundary error)."""


def _require_str(arguments: dict[str, Any], key: str) -> str:
    value = arguments.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ToolError(f"{key} must be a non-empty string")
    return value.strip()


def _resolve_path(raw: str, *, must_exist: bool) -> Path:
    path = Path(raw).expanduser()
    if must_exist and not path.exists():
        raise ToolError(f"path does not exist: {raw!r}")
    try:
        return path.resolve()
    except OSError as exc:
        raise ToolError(f"invalid path: {raw!r}") from exc


def _load_traces(path: Path, adapter: str | None) -> list[Any]:
    if adapter:
        return resolve(adapter)(path)
    return load_traces_path(path)


def _load_traces_from_args(arguments: dict[str, Any]) -> list[Any]:
    traces_dir = arguments.get("traces_dir")
    path_raw = arguments.get("path")
    adapter = arguments.get("adapter")
    if isinstance(adapter, str):
        adapter = adapter.strip() or None
    else:
        adapter = None
    if traces_dir is not None:
        if not isinstance(traces_dir, str) or not traces_dir.strip():
            raise ToolError("traces_dir must be a non-empty string")
        return load_traces_dir(_resolve_path(traces_dir.strip(), must_exist=True))
    if path_raw is not None:
        if not isinstance(path_raw, str) or not path_raw.strip():
            raise ToolError("path must be a non-empty string")
        return _load_traces(_resolve_path(path_raw.strip(), must_exist=True), adapter)
    raise ToolError("path or traces_dir required")


def unagent_validate(arguments: dict[str, Any]) -> dict[str, Any]:
    path = _resolve_path(_require_str(arguments, "path"), must_exist=True)
    traces = load_traces_path(path)
    return {"ok": True, "traces": len(traces), "spans": sum(len(t.spans) for t in traces)}


def unagent_inspect(arguments: dict[str, Any]) -> dict[str, Any]:
    path = _resolve_path(_require_str(arguments, "path"), must_exist=True)
    adapter = arguments.get("adapter")
    if isinstance(adapter, str):
        adapter = adapter.strip() or None
    else:
        adapter = None
    traces = _load_traces(path, adapter)
    return inspect_traces(traces)


def unagent_recommend(arguments: dict[str, Any]) -> dict[str, Any]:
    traces = _load_traces_from_args(arguments)
    n_min = arguments.get("n_min", N_MIN_DEFAULT)
    if not isinstance(n_min, int) or isinstance(n_min, bool):
        raise ToolError("n_min must be an integer")
    recs = recommend_traces(traces, n_min=n_min)
    return recommendations_to_dict(recs)


def unagent_simulate(arguments: dict[str, Any]) -> dict[str, Any]:
    traces = _load_traces_from_args(arguments)
    mode = arguments.get("mode", "report")
    if not isinstance(mode, str):
        raise ToolError("mode must be a string")
    mode = mode.strip()
    if mode not in {"what-if", "design", "report"}:
        raise ToolError("mode must be what-if, design, or report")
    n_min = arguments.get("n_min", N_MIN_DEFAULT)
    if not isinstance(n_min, int) or isinstance(n_min, bool):
        raise ToolError("n_min must be an integer")
    opt_in_l1 = bool(arguments.get("opt_in_l1", False))
    if mode == "what-if":
        node = arguments.get("node")
        if not isinstance(node, str) or not node.strip():
            raise ToolError("node is required for mode what-if")
        return what_if_to_dict(
            simulate_what_if(traces, node.strip(), n_min=n_min, opt_in_l1=opt_in_l1)
        )
    if mode == "design":
        return {
            "disclaimer": "simulation != production; canary is confirmatory",
            "design": [asdict(c) for c in simulate_design(traces, n_min=n_min)],
        }
    return simulate_report(traces, n_min=n_min, opt_in_l1=opt_in_l1)


def unagent_scaffold(arguments: dict[str, Any]) -> dict[str, Any]:
    report_path = _resolve_path(_require_str(arguments, "report_path"), must_exist=True)
    out_dir = _resolve_path(_require_str(arguments, "out_dir"), must_exist=False)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if not isinstance(report, dict):
        raise ToolError("report must be a JSON object")
    write_scaffold(report, out_dir)
    files = sorted(str(p.relative_to(out_dir)) for p in out_dir.rglob("*") if p.is_file())
    return {"files": files}


_TOOL_HANDLERS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "unagent_validate": unagent_validate,
    "unagent_inspect": unagent_inspect,
    "unagent_recommend": unagent_recommend,
    "unagent_simulate": unagent_simulate,
    "unagent_scaffold": unagent_scaffold,
}

_TOOLS: list[dict[str, Any]] = [
    {
        "name": "unagent_validate",
        "description": "Validate trace payload shape; return trace and span counts.",
        "inputSchema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Path to trace JSON file"}},
            "required": ["path"],
        },
    },
    {
        "name": "unagent_inspect",
        "description": "Inspect reconstructed node map without recommending.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to trace JSON file"},
                "adapter": {"type": "string", "description": "Optional ingest adapter (e.g. langgraph)"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "unagent_recommend",
        "description": "Ingest traces and emit L0 recommendation report.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to trace JSON file"},
                "traces_dir": {"type": "string", "description": "Directory of trace JSON files"},
                "n_min": {"type": "integer", "description": "Minimum sample size per node"},
                "adapter": {"type": "string", "description": "Optional ingest adapter"},
            },
        },
    },
    {
        "name": "unagent_simulate",
        "description": "Run L0 architecture simulation (what-if, design ranking, or full report).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "traces_dir": {"type": "string"},
                "mode": {"type": "string", "enum": ["what-if", "design", "report"]},
                "node": {"type": "string", "description": "Node id (required for what-if)"},
                "n_min": {"type": "integer"},
                "opt_in_l1": {"type": "boolean"},
                "adapter": {"type": "string"},
            },
        },
    },
    {
        "name": "unagent_scaffold",
        "description": "Write illustrative scaffold under out_dir only; never edits user source.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "report_path": {"type": "string", "description": "Path to recommend JSON report"},
                "out_dir": {"type": "string", "description": "Output directory (created if needed)"},
            },
            "required": ["report_path", "out_dir"],
        },
    },
]


def list_tools() -> list[dict[str, Any]]:
    return list(_TOOLS)


def call_tool(name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    handler = _TOOL_HANDLERS.get(name)
    if handler is None:
        raise ToolError(f"unknown tool: {name}")
    try:
        return handler(arguments or {})
    except ToolError:
        raise
    except _BOUNDARY as exc:
        raise ToolError(str(exc)) from exc


def _tool_result(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "content": [{"type": "text", "text": json.dumps(payload, indent=2)}],
        "isError": False,
    }


def _tool_error(message: str) -> dict[str, Any]:
    return {
        "content": [{"type": "text", "text": message}],
        "isError": True,
    }


def _rpc_result(req_id: Any, result: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": req_id, "result": result}) + "\n")
    sys.stdout.flush()


def _rpc_error(req_id: Any, code: int, message: str) -> None:
    sys.stdout.write(
        json.dumps(
            {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}
        )
        + "\n"
    )
    sys.stdout.flush()


def _handle_request(method: str, params: dict[str, Any]) -> dict[str, Any]:
    if method == "initialize":
        return {
            "protocolVersion": _PROTOCOL,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": _SERVER_NAME, "version": "0.2.0"},
        }
    if method == "tools/list":
        return {"tools": list_tools()}
    if method == "tools/call":
        name = params.get("name")
        if not isinstance(name, str):
            raise ValueError("tools/call requires string name")
        try:
            payload = call_tool(name, params.get("arguments") or {})
        except ToolError as exc:
            return _tool_error(str(exc))
        return _tool_result(payload)
    raise ValueError(f"method not found: {method}")


def run_stdio() -> None:
    """JSON-RPC stdio loop for MCP clients."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(msg, dict):
            continue
        method = msg.get("method")
        if not isinstance(method, str):
            continue
        if method.startswith("notifications/"):
            continue
        req_id = msg.get("id")
        if req_id is None:
            continue
        params = msg.get("params")
        if not isinstance(params, dict):
            params = {}
        try:
            result = _handle_request(method, params)
            _rpc_result(req_id, result)
        except ValueError as exc:
            _rpc_error(req_id, -32601, str(exc))
        except Exception as exc:  # ponytail: fail closed; stdio must not crash the loop
            _rpc_error(req_id, -32603, str(exc))


def main() -> None:
    run_stdio()


if __name__ == "__main__":
    main()
