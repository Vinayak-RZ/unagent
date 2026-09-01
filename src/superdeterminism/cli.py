from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from superdeterminism.adapters import AdapterError, resolve
from superdeterminism.ingest import IngestError, load_traces_dir, load_traces_path
from superdeterminism.pipeline import (
    N_MIN_DEFAULT,
    inspect_traces,
    recommend_traces,
    recommendations_to_dict,
    recommendations_to_markdown,
)
from superdeterminism.scaffold import write_scaffold

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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="superdeterminism",
        description="Agnostic determinism advisor. JSON in/out. No prompts. No auto-apply.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    rec = sub.add_parser("recommend", help="ingest traces and emit L0 recommendations")
    rec.add_argument("traces", type=Path, nargs="?", default=None)
    rec.add_argument("--traces-dir", type=Path, default=None)
    rec.add_argument("--json", dest="json_out", type=Path, default=None)
    rec.add_argument("--md", dest="md_out", type=Path, default=None)
    rec.add_argument("--n-min", type=int, default=N_MIN_DEFAULT)
    rec.add_argument("--outcome-attr", default=None)
    rec.add_argument(
        "--stdout",
        choices=("json", "md"),
        default="json",
        help="print this format to stdout (agents: json)",
    )
    rec.add_argument(
        "--adapter",
        default=None,
        help="optional ingest adapter (e.g. langgraph). omitted = P0 generic ingest",
    )
    val = sub.add_parser("validate", help="check payload shape; no recommendations")
    val.add_argument("traces", type=Path)
    ins = sub.add_parser("inspect", help="print node map without recommending")
    ins.add_argument("traces", type=Path)
    ins.add_argument("--adapter", default=None)
    scaf = sub.add_parser("scaffold", help="write illustrative scaffold; never edits user source")
    scaf.add_argument("report", type=Path, help="recommend JSON report")
    scaf.add_argument("--out", type=Path, required=True, help="directory to write (created)")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.cmd == "scaffold":
        return _scaffold(args)
    if args.cmd == "validate":
        return _validate(args)
    if args.cmd == "inspect":
        return _inspect(args)
    if args.cmd != "recommend":
        return 2
    try:
        traces = _load(args)
        recs = recommend_traces(traces, n_min=args.n_min)
    except _BOUNDARY as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    payload = recommendations_to_dict(recs)
    markdown = recommendations_to_markdown(recs)
    try:
        if args.json_out:
            args.json_out.parent.mkdir(parents=True, exist_ok=True)
            args.json_out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        if args.md_out:
            args.md_out.parent.mkdir(parents=True, exist_ok=True)
            args.md_out.write_text(markdown, encoding="utf-8")
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.stdout == "json":
        json.dump(payload, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        sys.stdout.write(markdown)
        if not markdown.endswith("\n"):
            sys.stdout.write("\n")
    return 0


def _load(args: argparse.Namespace):
    outcome = getattr(args, "outcome_attr", None)
    if getattr(args, "traces_dir", None):
        return load_traces_dir(args.traces_dir, outcome_attr=outcome)
    if args.traces is None:
        raise IngestError("traces path or --traces-dir required")
    if args.adapter:
        return resolve(args.adapter)(args.traces)
    return load_traces_path(args.traces, outcome_attr=outcome)


def _validate(args: argparse.Namespace) -> int:
    try:
        traces = load_traces_path(args.traces)
    except _BOUNDARY as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"ok": True, "traces": len(traces), "spans": sum(len(t.spans) for t in traces)}))
    return 0


def _inspect(args: argparse.Namespace) -> int:
    try:
        if args.adapter:
            traces = resolve(args.adapter)(args.traces)
        else:
            traces = load_traces_path(args.traces)
        json.dump(inspect_traces(traces), sys.stdout, indent=2)
        sys.stdout.write("\n")
    except _BOUNDARY as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


def _scaffold(args: argparse.Namespace) -> int:
    try:
        report = json.loads(args.report.read_text(encoding="utf-8"))
        if not isinstance(report, dict):
            raise ValueError("report must be a JSON object")
        write_scaffold(report, args.out)
    except _BOUNDARY as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
