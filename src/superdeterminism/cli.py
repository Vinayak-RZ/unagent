from __future__ import annotations

import argparse
import http.server
import json
import socketserver
import sys
import webbrowser
from pathlib import Path

from superdeterminism.adapters import AdapterError, resolve
from superdeterminism.ingest import IngestError, load_traces_dir, load_traces_path
from superdeterminism.sinks import load_sink
from superdeterminism.pipeline import (
    N_MIN_DEFAULT,
    inspect_traces,
    recommend_traces,
    recommendations_to_dict,
    recommendations_to_markdown,
)
from superdeterminism.simulate import (
    simulate_design,
    simulate_report,
    simulate_what_if,
    what_if_to_dict,
)
from superdeterminism.scaffold import write_scaffold
from superdeterminism.narrative import recommendations_to_narrative

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
        choices=("json", "md", "narrative"),
        default="json",
        help="print this format to stdout (agents: json)",
    )
    rec.add_argument(
        "--adapter",
        default=None,
        help="optional ingest adapter (e.g. langgraph). omitted = P0 generic ingest",
    )
    rec.add_argument(
        "--sink",
        choices=("langfuse", "langsmith", "mlflow"),
        default=None,
        help="load traces via observability sink (file or --live)",
    )
    rec.add_argument(
        "--live",
        action="store_true",
        help="with --sink, pull from live API using env credentials",
    )
    val = sub.add_parser("validate", help="check payload shape; no recommendations")
    val.add_argument("traces", type=Path)
    ins = sub.add_parser("inspect", help="print node map without recommending")
    ins.add_argument("traces", type=Path)
    ins.add_argument("--adapter", default=None)
    sim = sub.add_parser("simulate", help="design/run L0 architecture simulations")
    sim.add_argument("traces", type=Path, nargs="?", default=None)
    sim.add_argument("--traces-dir", type=Path, default=None)
    sim.add_argument("--adapter", default=None)
    sim.add_argument("--sink", choices=("langfuse", "langsmith", "mlflow"), default=None)
    sim.add_argument("--live", action="store_true")
    sim.add_argument("--mode", choices=("what-if", "design", "report"), default="report")
    sim.add_argument("--node", default=None, help="node id for what-if")
    sim.add_argument("--n-min", type=int, default=N_MIN_DEFAULT)
    sim.add_argument("--opt-in-l1", action="store_true", help="acknowledge L1 hybrid path (no live calls in this build)")
    sim.add_argument("--stdout", choices=("json", "md"), default="json")
    sim.add_argument("--json", dest="json_out", type=Path, default=None)
    scaf = sub.add_parser("scaffold", help="write illustrative scaffold; never edits user source")
    scaf.add_argument("report", type=Path, help="recommend JSON report")
    scaf.add_argument("--out", type=Path, required=True, help="directory to write (created)")
    sr = sub.add_parser(
        "studio-report",
        help="emit Studio-ready report JSON (recommend + simulate + graph)",
    )
    sr.add_argument("traces", type=Path)
    sr.add_argument("--out", type=Path, default=Path("examples/studio_report.json"))
    sr.add_argument("--n-min", type=int, default=N_MIN_DEFAULT)
    sr.add_argument("--adapter", default=None)
    ui = sub.add_parser("ui", help="open Unagent Studio (Vite dev or static dist)")
    ui.add_argument("--report", type=Path, default=None, help="report JSON path for ?report= query")
    ui.add_argument("--port", type=int, default=5173)
    ui.add_argument("--no-open", action="store_true", help="print URL only; do not open browser")
    ui.add_argument("--serve-dist", action="store_true", help="serve ui/dist with http.server if present")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.cmd == "ui":
        return _ui(args)
    if args.cmd == "studio-report":
        return _studio_report(args)
    if args.cmd == "scaffold":
        return _scaffold(args)
    if args.cmd == "validate":
        return _validate(args)
    if args.cmd == "inspect":
        return _inspect(args)
    if args.cmd == "simulate":
        return _simulate(args)
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
    elif args.stdout == "narrative":
        sys.stdout.write(recommendations_to_narrative(recs))
        if not recommendations_to_narrative(recs).endswith("\n"):
            sys.stdout.write("\n")
    else:
        sys.stdout.write(markdown)
        if not markdown.endswith("\n"):
            sys.stdout.write("\n")
    return 0


def _load(args: argparse.Namespace):
    outcome = getattr(args, "outcome_attr", None)
    sink = getattr(args, "sink", None)
    live = bool(getattr(args, "live", False))
    if sink:
        return load_sink(sink, path=args.traces, live=live)
    if getattr(args, "traces_dir", None):
        return load_traces_dir(args.traces_dir, outcome_attr=outcome)
    if args.traces is None:
        raise IngestError("traces path, --traces-dir, or --sink required")
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


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _ui_dir() -> Path:
    return _repo_root() / "ui"


def _studio_report(args: argparse.Namespace) -> int:
    try:
        from superdeterminism.graph_hierarchy import nest_for_studio
        from superdeterminism.narrative import build_narrative

        if args.adapter:
            traces = resolve(args.adapter)(args.traces)
        else:
            traces = load_traces_path(args.traces)
        payload = simulate_report(traces, n_min=args.n_min)
        inspected = inspect_traces(traces)
        root_nodes, root_edges = nest_for_studio(
            inspected["nodes"], inspected["edges"], traces
        )
        payload["graph"] = {
            "nodes": root_nodes,
            "edges": root_edges,
            "identity": inspected["graph_identity"],
            "completeness": inspected["completeness"],
            "trust": inspected["trust"],
            "flat_nodes": inspected["nodes"],
            "flat_edges": inspected["edges"],
        }
        payload["narrative"] = build_narrative(payload)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    except _BOUNDARY as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"wrote {args.out}", file=sys.stderr)
    return 0


def _ui(args: argparse.Namespace) -> int:
    ui_dir = _ui_dir()
    dist = ui_dir / "dist"
    report_q = f"?report={args.report.resolve()}" if args.report else ""
    if args.serve_dist and dist.is_dir():
        port = args.port
        suffix = f"index.html{report_q}" if report_q else ""
        url = f"http://127.0.0.1:{port}/{suffix}"
        print(f"Serving {dist} at http://127.0.0.1:{port}/", file=sys.stderr)
        print("Proposal edits export only; never auto-applied.", file=sys.stderr)
        if not args.no_open:
            webbrowser.open(url)

        class _DistHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *a, **kw):
                super().__init__(*a, directory=str(dist), **kw)

        with socketserver.TCPServer(("127.0.0.1", port), _DistHandler) as httpd:
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                pass
        return 0
    dev_cmd = f"cd {ui_dir} && npm install && npm run dev -- --port {args.port}"
    url = f"http://127.0.0.1:{args.port}/{report_q}"
    print("Unagent Studio (dev mode)", file=sys.stderr)
    print(f"  1. {dev_cmd}", file=sys.stderr)
    print(f"  2. Open {url}", file=sys.stderr)
    if args.report:
        print(f"     Or load report via file picker: {args.report.resolve()}", file=sys.stderr)
    print("Build static UI: cd ui && npm run build", file=sys.stderr)
    print("Then: python -m superdeterminism ui --serve-dist --port PORT", file=sys.stderr)
    print("Proposal edits export only; never auto-applied.", file=sys.stderr)
    if not args.no_open and (ui_dir / "node_modules").is_dir():
        webbrowser.open(url)
    return 0


def _simulate(args: argparse.Namespace) -> int:
    try:
        traces = _load(args)
        if args.opt_in_l1:
            print("warning: --opt-in-l1 set; live L1 tail is not executed in this build", file=sys.stderr)
        if args.mode == "what-if":
            if not args.node:
                raise ValueError("--node is required for --mode what-if")
            payload = what_if_to_dict(
                simulate_what_if(traces, args.node, n_min=args.n_min, opt_in_l1=args.opt_in_l1)
            )
        elif args.mode == "design":
            from dataclasses import asdict

            payload = {
                "disclaimer": "simulation != production; canary is confirmatory",
                "design": [asdict(c) for c in simulate_design(traces, n_min=args.n_min)],
            }
        else:
            payload = simulate_report(traces, n_min=args.n_min, opt_in_l1=args.opt_in_l1)
    except _BOUNDARY as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    try:
        if args.json_out:
            args.json_out.parent.mkdir(parents=True, exist_ok=True)
            args.json_out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
