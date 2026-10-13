"""
Command Line Interface for Robvis Cli.
"""
import argparse
import csv
import math
import sys

from agents.models import SystemTaskPayload
from agents.supervisor import SystemSupervisor
from agents.base import AuditLogger

supervisor = SystemSupervisor(model_provider="mock")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="robvis-cli", description="Robvis Cli")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Audit
    p_audit = subparsers.add_parser("audit", help="Run single task evaluation")
    p_audit.add_argument("--task-id", default="TASK-2026-001")
    p_audit.add_argument("--target", default="KEY-TARGET-01")
    p_audit.add_argument("--primary", type=float, default=28.5)
    p_audit.add_argument("--secondary", type=float, default=14.2)
    p_audit.add_argument("--critical", action="store_true")
    p_audit.add_argument("--status", default="DISCORDANT")

    # Chat
    p_chat = subparsers.add_parser("chat", help="System configuration query")
    p_chat.add_argument("query", nargs="+")

    # Batch
    p_batch = subparsers.add_parser("batch", help="Batch process CSV records")
    p_batch.add_argument("-i", "--input", required=True)
    p_batch.add_argument("-o", "--output", default="results.csv")

    # Verify Audit
    subparsers.add_parser("verify-audit", help="Verify HMAC audit trail integrity")

    # Serve
    p_serve = subparsers.add_parser("serve", help="Launch FastAPI REST server")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8000)

    args = parser.parse_args(argv)

    if args.command == "audit":
        payload = SystemTaskPayload(
            task_id=args.task_id,
            target_identifier=args.target,
            primary_metric=args.primary,
            secondary_metric=args.secondary,
            status_descriptor=args.status,
            is_critical_flag=args.critical,
        )
        dossier = supervisor.process_task(payload)
        print("=" * 80)
        print("  ROBVIS CLI")
        print("  Domain: Clinical & Biomedical AI | Standard: CAP / CLSI / ISO Standards")
        print(f"  Dossier ID: {dossier.dossier_id} | Urgency: [{dossier.overall_urgency.value}]")
        print("=" * 80)
        for a in dossier.alerts:
            print(f"\n  [{a.urgency.value}] from {a.origin_worker}:")
            print(f"  Summary: {a.summary}")
            print(f"  Details: {a.technical_details}")
            print(f"  Action:  {a.actionable_remediation}")
        print(f"\n  HMAC-SHA256 Audit Hash: {dossier.audit_hash}")
        print("=" * 80)
        return 0

    if args.command == "chat":
        ans = supervisor.query_supervisory_chat(" ".join(args.query))
        print(f"\n[Robvis Cli Supervisor]:\n{ans}\n")
        return 0

    if args.command == "verify-audit":
        trail = AuditLogger.get_trail()
        valid = AuditLogger.verify_integrity()
        print(f"Audit Trail Blocks: {len(trail)} | Cryptographic Integrity Verified: {valid}")
        return 0

    if args.command == "serve":
        import uvicorn
        from agents.api import app
        print(f"Starting Robvis Cli API server on http://{args.host}:{args.port}")
        uvicorn.run(app, host=args.host, port=args.port)
        return 0

    return 0

    if args.command == "batch":
        try:
            return _run_batch(args.input, args.output)
        except (OSError, ValueError) as exc:
            print(f"Batch ERROR: {exc}", file=sys.stderr)
            return 1

    return 0


def _run_batch(input_path: str, output_path: str):
    with open(input_path, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    out_fields = list(dict.fromkeys(fieldnames + ["overall_urgency", "integrity_status", "total_alerts", "audit_hash"]))
    out_rows = []
    for index, r in enumerate(rows, start=2):
        flag = str(r.get("is_critical_flag") or "false").strip().lower()
        if flag not in ("true", "false", "1", "0", "yes", "no"):
            raise ValueError(f"Line {index}: invalid is_critical_flag value")
        primary = float(r.get("primary_metric") or 15.0)
        secondary = float(r.get("secondary_metric") or 5.0)
        if not math.isfinite(primary) or not math.isfinite(secondary):
            raise ValueError(f"Line {index}: metrics must be finite")
        payload = SystemTaskPayload(
            task_id=r.get("task_id", "TASK-01"),
            target_identifier=r.get("target_identifier", "TARGET-01"),
            primary_metric=primary,
            secondary_metric=secondary,
            status_descriptor=r.get("status_descriptor", "NOMINAL"),
            is_critical_flag=flag in ("true", "1", "yes"),
        )
        dossier = supervisor.process_task(payload)
        row_dict = dict(r)
        row_dict["overall_urgency"] = dossier.overall_urgency.value
        row_dict["integrity_status"] = dossier.integrity_status.value
        row_dict["total_alerts"] = dossier.total_alerts
        row_dict["audit_hash"] = dossier.audit_hash
        out_rows.append(row_dict)

    with open(output_path, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields)
        writer.writeheader()
        writer.writerows(out_rows)
    print(f"Processed {len(out_rows)} records -> {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
