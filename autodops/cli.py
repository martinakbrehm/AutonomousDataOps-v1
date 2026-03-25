import argparse
import os
import sys


def serve(args):
    import uvicorn
    host = args.host or "0.0.0.0"
    port = int(args.port or 8000)
    uvicorn.run("api.main:app", host=host, port=port, reload=args.reload)


def run_pipeline(args):
    from pipelines.etl_pipeline import run_pipeline_from_file
    path = args.file
    if not os.path.exists(path):
        print(f"File not found: {path}")
        sys.exit(2)
    req = {"clean": args.clean, "analyze": args.analyze, "transform": args.transform}
    df, summary = run_pipeline_from_file(path, req)
    print("Summary:", summary)


def main():
    parser = argparse.ArgumentParser(prog="autodops", description="Autonomous DataOps CLI")
    sub = parser.add_subparsers(dest="cmd")

    p_serve = sub.add_parser("serve", help="Run the FastAPI server")
    p_serve.add_argument("--host", default=None)
    p_serve.add_argument("--port", default=8000)
    p_serve.add_argument("--reload", action="store_true")
    p_serve.set_defaults(func=serve)

    p_run = sub.add_parser("run-pipeline", help="Run pipeline on a local file")
    p_run.add_argument("file", help="Path to CSV/Excel file")
    p_run.add_argument("--clean", action="store_true", default=True)
    p_run.add_argument("--analyze", action="store_true", default=True)
    p_run.add_argument("--transform", action="store_true", default=False)
    p_run.set_defaults(func=run_pipeline)

    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)
    args.func(args)
