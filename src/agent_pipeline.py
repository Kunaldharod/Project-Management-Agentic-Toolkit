"""
agent_pipeline.py
-----------------
The core end-to-end agent pipeline. This is what n8n's AI Agent node
orchestrates visually — here it runs as pure Python for local testing,
CI integration, and Phase 3 validation.

Flow:
  1. Load system prompt + current PMBOK artifacts (context)
  2. Receive git snapshot text (from git_extractor.py)
  3. Call LLM with full context
  4. Parse + classify output (Risk / Velocity / Stakeholder / NoAction)
  5. Validate JSON output against PMBOK schema
  6. Upsert the correct artifact file
  7. Optionally push to Kanban board (kanban_connector.py)
  8. Return a structured PipelineResult

Usage (CLI):
    python src/agent_pipeline.py --snapshot <path-to-snapshot.txt>
    python src/agent_pipeline.py --repo owner/repo --live   # full live run

Usage (imported):
    from agent_pipeline import AgentPipeline
    result = AgentPipeline().run(snapshot_text)
"""

import argparse
import json
import logging
import os
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from jsonschema import Draft7Validator

load_dotenv()

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[
        logging.FileHandler("logs/pipeline.log"),
        logging.StreamHandler(sys.stderr),
    ],
)
log = logging.getLogger("pipeline")


# ── Paths ─────────────────────────────────────────────────────────────────────
BASE          = Path(__file__).resolve().parent.parent
SCHEMAS_DIR   = BASE / "schemas"
ARTIFACTS_DIR = BASE / "artifacts"
PROMPTS_DIR   = BASE / "prompts"
LOGS_DIR      = BASE / "logs"


# ── Output types ──────────────────────────────────────────────────────────────
OUTPUT_RISK        = "RISK"
OUTPUT_VELOCITY    = "VELOCITY"
OUTPUT_STAKEHOLDER = "STAKEHOLDER"
OUTPUT_NO_ACTION   = "NO_ACTION"
OUTPUT_UNKNOWN     = "UNKNOWN"


# ── Pipeline result ───────────────────────────────────────────────────────────
@dataclass
class PipelineResult:
    output_type:   str
    payload:       dict
    artifact_path: Optional[str]   = None
    kanban_result: Optional[dict]  = None
    validation_errors: list        = field(default_factory=list)
    llm_provider:  str             = ""
    llm_model:     str             = ""
    input_tokens:  int             = 0
    output_tokens: int             = 0
    attempts:      int             = 1
    duration_sec:  float           = 0.0
    run_id:        str             = ""

    @property
    def success(self) -> bool:
        return len(self.validation_errors) == 0

    def summary(self) -> str:
        status = "✅ SUCCESS" if self.success else "❌ FAILED"
        return (
            f"{status} | type={self.output_type} | "
            f"provider={self.llm_provider}/{self.llm_model} | "
            f"tokens={self.input_tokens + self.output_tokens} | "
            f"duration={self.duration_sec:.1f}s"
        )


# ── Context loader ────────────────────────────────────────────────────────────
class ContextLoader:
    """Loads all static context files the agent needs before each run."""

    def load_system_prompt(self) -> str:
        path = PROMPTS_DIR / "agent_system_prompt.md"
        return path.read_text(encoding="utf-8")

    def load_risk_register(self) -> str:
        path = ARTIFACTS_DIR / "risk_register.json"
        return path.read_text(encoding="utf-8") if path.exists() else "{}"

    def load_velocity_log(self) -> str:
        path = ARTIFACTS_DIR / "velocity_log.json"
        return path.read_text(encoding="utf-8") if path.exists() else "{}"

    def build_user_message(
        self,
        snapshot_text: str,
        sprint_id: str,
        sprint_start: str,
        sprint_end: str,
    ) -> str:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        risk_register = self.load_risk_register()
        velocity_log  = self.load_velocity_log()

        return f"""You are now processing a new repository snapshot.
Today's date: {today}
Current Sprint: {sprint_id}
Sprint Window: {sprint_start} to {sprint_end}

--- CURRENT RISK REGISTER (check before creating new risks) ---
{risk_register}

--- CURRENT VELOCITY LOG (last 3 sprints) ---
{velocity_log}

--- GIT REPOSITORY SNAPSHOT ---
{snapshot_text}

Analyse the snapshot. Apply your detection rules. Produce the correct JSON output type (A/B/C/D).
Output JSON only — zero prose, zero markdown fences."""


# ── Output classifier ─────────────────────────────────────────────────────────
def classify_output(parsed: dict) -> str:
    if parsed.get("action") == "NO_ACTION":
        return OUTPUT_NO_ACTION
    if parsed.get("risk_id"):
        return OUTPUT_RISK
    if parsed.get("sprint_id"):
        return OUTPUT_VELOCITY
    if str(parsed.get("id", "")).startswith("SH-"):
        return OUTPUT_STAKEHOLDER
    return OUTPUT_UNKNOWN


# ── Schema validator ──────────────────────────────────────────────────────────
def validate_against_schema(output_type: str, payload: dict) -> list[str]:
    """
    Returns list of error strings (empty = valid).

    The AI agent outputs single objects (one risk, one sprint, one stakeholder).
    The schemas describe the full collection wrapper. We normalise here:
      - VELOCITY:    { sprint_id, ... }  → { project_id, sprints: [payload] }
      - STAKEHOLDER: { id, ... }         → { project_id, version, stakeholders: [payload] }
      - RISK:        validated as-is (schema describes a single entry)
    """
    schema_map = {
        OUTPUT_RISK:        SCHEMAS_DIR / "risk_register.schema.json",
        OUTPUT_VELOCITY:    SCHEMAS_DIR / "velocity_log.schema.json",
        OUTPUT_STAKEHOLDER: SCHEMAS_DIR / "stakeholder_map.schema.json",
    }
    schema_path = schema_map.get(output_type)
    if not schema_path:
        return []   # NO_ACTION and UNKNOWN don't have schemas

    with open(schema_path, encoding="utf-8") as f:
        schema = json.load(f)

    # Wrap single-object agent outputs into the collection envelope the schema expects
    if output_type == OUTPUT_VELOCITY and "sprint_id" in payload:
        payload = {"project_id": "PROJ-001", "sprints": [payload]}
    elif output_type == OUTPUT_STAKEHOLDER and "id" in payload:
        payload = {"project_id": "PROJ-001", "version": "1.0", "stakeholders": [payload]}

    validator = Draft7Validator(schema)
    errors = []
    for err in sorted(validator.iter_errors(payload), key=lambda e: e.path):
        path = " > ".join(str(p) for p in err.path) or "root"
        errors.append(f"[{path}] {err.message}")
    return errors


# ── Artifact upsert ───────────────────────────────────────────────────────────
class ArtifactWriter:

    def upsert_risk(self, risk: dict) -> str:
        path = ARTIFACTS_DIR / "risk_register.json"
        data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"risks": []}

        # Remove internal pipeline fields before writing
        clean = {k: v for k, v in risk.items() if not k.startswith("_")}

        idx = next((i for i, r in enumerate(data["risks"]) if r["risk_id"] == clean["risk_id"]), -1)
        if idx >= 0:
            data["risks"][idx] = {**data["risks"][idx], **clean}
            action = "updated"
        else:
            data["risks"].append(clean)
            action = "created"

        data["last_updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        log.info("Risk register %s: %s", action, clean["risk_id"])
        return str(path)

    def upsert_velocity(self, sprint: dict) -> str:
        path = ARTIFACTS_DIR / "velocity_log.json"
        data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"sprints": []}

        clean = {k: v for k, v in sprint.items() if not k.startswith("_")}

        idx = next((i for i, s in enumerate(data["sprints"]) if s["sprint_id"] == clean["sprint_id"]), -1)
        if idx >= 0:
            data["sprints"][idx] = {**data["sprints"][idx], **clean}
            action = "updated"
        else:
            data["sprints"].append(clean)
            action = "created"

        data["last_updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        log.info("Velocity log %s: %s", action, clean["sprint_id"])
        return str(path)

    def upsert_stakeholder(self, stakeholder: dict) -> str:
        path = ARTIFACTS_DIR / "stakeholder_map.json"
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
        else:
            data = {"project_id": "PROJ-001", "version": "1.0", "stakeholders": []}

        clean = {k: v for k, v in stakeholder.items() if not k.startswith("_")}

        idx = next((i for i, s in enumerate(data["stakeholders"]) if s["id"] == clean["id"]), -1)
        if idx >= 0:
            data["stakeholders"][idx] = {**data["stakeholders"][idx], **clean}
            action = "updated"
        else:
            data["stakeholders"].append(clean)
            action = "created"

        data["last_updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        log.info("Stakeholder map %s: %s", action, clean.get("id"))
        return str(path)


# ── Audit logger ──────────────────────────────────────────────────────────────
def append_pipeline_audit(result: PipelineResult) -> None:
    entry = {
        "run_id":       result.run_id,
        "timestamp":    datetime.now(timezone.utc).isoformat(),
        "output_type":  result.output_type,
        "success":      result.success,
        "provider":     result.llm_provider,
        "model":        result.llm_model,
        "input_tokens": result.input_tokens,
        "output_tokens":result.output_tokens,
        "duration_sec": result.duration_sec,
        "artifact":     result.artifact_path,
        "errors":       result.validation_errors,
    }
    audit_path = LOGS_DIR / "pipeline_audit.jsonl"
    with open(audit_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


# ── Main pipeline ─────────────────────────────────────────────────────────────
class AgentPipeline:
    """
    Orchestrates the full agent loop end-to-end.
    Can be used standalone or imported by test_phase3.py.
    """

    def __init__(
        self,
        llm_provider: Optional[str]  = None,
        llm_model:    Optional[str]  = None,
        push_kanban:  bool           = False,
        kanban_provider: str         = "trello",
        dry_run:      bool           = False,
    ) -> None:
        from llm_client import build_llm_client, TokenBudget
        self.llm       = build_llm_client(llm_provider, llm_model)
        self.budget    = TokenBudget()
        self.loader    = ContextLoader()
        self.writer    = ArtifactWriter()
        self.push_kanban    = push_kanban
        self.kanban_provider = kanban_provider
        self.dry_run   = dry_run

    def run(
        self,
        snapshot_text: str,
        sprint_id:    str = "SP-03",
        sprint_start: str = "2026-05-12",
        sprint_end:   str = "2026-05-25",
        run_id:       str = "",
    ) -> PipelineResult:
        import time, uuid
        run_id = run_id or uuid.uuid4().hex[:8]
        t_start = time.monotonic()
        log.info("Pipeline run %s started", run_id)

        # ── Step 1: Build context ─────────────────────────────────────────────
        system_prompt = self.loader.load_system_prompt()
        user_message  = self.loader.build_user_message(
            snapshot_text, sprint_id, sprint_start, sprint_end
        )

        # ── Step 2: Call LLM ─────────────────────────────────────────────────
        log.info("Calling LLM (%s)...", self.llm.__class__.__name__)
        response = self.llm.call(
            system_prompt=system_prompt,
            user_message=user_message,
            max_tokens=1500,
        )
        self.budget.record(response)
        log.info("LLM response received. %s", self.budget.summary())

        # ── Step 3: Parse output ──────────────────────────────────────────────
        try:
            parsed = response.extract_json()
        except Exception as e:
            log.error("JSON parse failed: %s\nRaw output:\n%s", e, response.content)
            return PipelineResult(
                run_id=run_id,
                output_type=OUTPUT_UNKNOWN,
                payload={"raw": response.content},
                validation_errors=[f"JSON parse error: {e}"],
                llm_provider=response.provider,
                llm_model=response.model,
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
                duration_sec=time.monotonic() - t_start,
            )

        output_type = classify_output(parsed)
        log.info("Output classified as: %s", output_type)

        # ── Step 4: Validate schema ───────────────────────────────────────────
        errors = validate_against_schema(output_type, parsed)
        if errors:
            log.warning("Schema validation failed (%d errors):\n%s", len(errors), "\n".join(errors))

        # ── Step 5: Upsert artifact ───────────────────────────────────────────
        artifact_path = None
        if not errors and not self.dry_run:
            if output_type == OUTPUT_RISK:
                artifact_path = self.writer.upsert_risk(parsed)
            elif output_type == OUTPUT_VELOCITY:
                artifact_path = self.writer.upsert_velocity(parsed)
            elif output_type == OUTPUT_STAKEHOLDER:
                artifact_path = self.writer.upsert_stakeholder(parsed)
            elif output_type == OUTPUT_NO_ACTION:
                log.info("No action required: %s", parsed.get("reason", ""))

        # ── Step 6: Push to Kanban ────────────────────────────────────────────
        kanban_result = None
        if self.push_kanban and output_type == OUTPUT_RISK and not errors and not self.dry_run:
            kanban_result = self._push_to_kanban(parsed)

        # ── Step 7: Build result ──────────────────────────────────────────────
        result = PipelineResult(
            run_id=run_id,
            output_type=output_type,
            payload=parsed,
            artifact_path=artifact_path,
            kanban_result=kanban_result,
            validation_errors=errors,
            llm_provider=response.provider,
            llm_model=response.model,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            attempts=response.attempts,
            duration_sec=time.monotonic() - t_start,
        )
        log.info(result.summary())
        append_pipeline_audit(result)
        return result

    def _push_to_kanban(self, payload: dict) -> dict:
        connector = str(BASE / "src" / "kanban_connector.py")
        cmd = [
            sys.executable, connector,
            "--provider", self.kanban_provider,
            "--payload", json.dumps(payload),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if proc.returncode != 0:
            log.error("kanban_connector.py failed: %s", proc.stderr)
            return {"success": False, "error": proc.stderr}
        try:
            return json.loads(proc.stdout)
        except Exception:
            return {"success": False, "raw": proc.stdout}


# ── CLI entry point ───────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(description="Run the PMBOK AI agent pipeline")
    parser.add_argument("--snapshot", help="Path to a pre-generated snapshot .txt file")
    parser.add_argument("--repo",     help="GitHub repo (owner/name) — fetches live snapshot")
    parser.add_argument("--provider", choices=["anthropic", "openai"], help="LLM provider override")
    parser.add_argument("--model",    help="Model override e.g. claude-sonnet-4-20250514")
    parser.add_argument("--sprint",   default="SP-03",       help="Current sprint ID")
    parser.add_argument("--start",    default="2026-05-12",  help="Sprint start date YYYY-MM-DD")
    parser.add_argument("--end",      default="2026-05-25",  help="Sprint end date YYYY-MM-DD")
    parser.add_argument("--kanban",   action="store_true",   help="Push result to Kanban board")
    parser.add_argument("--dry-run",  action="store_true",   help="Run LLM but skip all writes")
    parser.add_argument("--output",   choices=["text", "json"], default="text")
    args = parser.parse_args()

    # Get snapshot text
    if args.snapshot:
        snapshot_text = Path(args.snapshot).read_text(encoding="utf-8")
    elif args.repo:
        log.info("Fetching live snapshot for %s...", args.repo)
        extractor = str(BASE / "src" / "git_extractor.py")
        proc = subprocess.run(
            [sys.executable, extractor, "--repo", args.repo],
            capture_output=True, text=True, timeout=60,
        )
        if proc.returncode != 0:
            log.error("git_extractor.py failed: %s", proc.stderr)
            sys.exit(1)
        snapshot_text = proc.stdout
    else:
        log.error("Provide --snapshot <file> or --repo <owner/name>")
        sys.exit(1)

    pipeline = AgentPipeline(
        llm_provider=args.provider,
        llm_model=args.model,
        push_kanban=args.kanban,
        dry_run=args.dry_run,
    )
    result = pipeline.run(
        snapshot_text=snapshot_text,
        sprint_id=args.sprint,
        sprint_start=args.start,
        sprint_end=args.end,
    )

    if args.output == "json":
        print(json.dumps({
            "run_id":       result.run_id,
            "output_type":  result.output_type,
            "success":      result.success,
            "payload":      result.payload,
            "errors":       result.validation_errors,
            "artifact":     result.artifact_path,
            "tokens":       result.input_tokens + result.output_tokens,
            "duration_sec": result.duration_sec,
        }, indent=2))
    else:
        print(f"\n{'='*60}")
        print(result.summary())
        print(f"Output type : {result.output_type}")
        print(f"Artifact    : {result.artifact_path or 'N/A'}")
        if result.validation_errors:
            print(f"Errors      :\n  " + "\n  ".join(result.validation_errors))
        print(f"Payload     :\n{json.dumps(result.payload, indent=2)}")
        print(f"{'='*60}\n")

    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()
