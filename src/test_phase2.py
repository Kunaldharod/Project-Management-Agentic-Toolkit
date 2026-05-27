"""
test_phase2.py
--------------
Validates Phase 2 deliverables:
  - All JSON schemas are valid JSON Schema Draft-07
  - Seed artifacts validate against their own schemas
  - Agent output parsing logic handles all output types and edge cases
  - Workflow JSON is valid and contains required node types

Run:
    pytest src/test_phase2.py -v
"""

import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

import pytest
import jsonschema
from jsonschema import Draft7Validator, validate, ValidationError

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMAS_DIR  = os.path.join(BASE, "schemas")
ARTIFACTS_DIR= os.path.join(BASE, "artifacts")
N8N_DIR      = os.path.join(BASE, "n8n")
PROMPTS_DIR  = os.path.join(BASE, "prompts")


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ── 1. Schema files are valid JSON Schema Draft-07 ────────────────────────────

class TestSchemasAreValid:

    @pytest.mark.parametrize("schema_file", [
        "risk_register.schema.json",
        "charter.schema.json",
        "stakeholder_map.schema.json",
        "velocity_log.schema.json",
    ])
    def test_schema_is_valid_draft7(self, schema_file):
        schema = load_json(os.path.join(SCHEMAS_DIR, schema_file))
        # This raises if the schema itself is malformed
        Draft7Validator.check_schema(schema)

    @pytest.mark.parametrize("schema_file", [
        "risk_register.schema.json",
        "charter.schema.json",
        "stakeholder_map.schema.json",
        "velocity_log.schema.json",
    ])
    def test_schema_has_required_meta(self, schema_file):
        schema = load_json(os.path.join(SCHEMAS_DIR, schema_file))
        assert "$schema" in schema,      "Schema must declare $schema"
        assert "title" in schema,        "Schema must have a title"
        assert "description" in schema,  "Schema must have a description"
        assert schema.get("type") == "object", "Top-level type must be 'object'"


# ── 2. Seed artifacts validate against their schemas ──────────────────────────

class TestArtifactsValidate:

    def test_risk_register_seed_validates(self):
        schema   = load_json(os.path.join(SCHEMAS_DIR, "risk_register.schema.json"))
        artifact = load_json(os.path.join(ARTIFACTS_DIR, "risk_register.json"))
        # Validate each risk entry individually (the artifact wraps entries in a list)
        for risk in artifact.get("risks", []):
            errors = list(Draft7Validator(schema).iter_errors(risk))
            assert errors == [], f"Risk {risk.get('risk_id')} failed: {[e.message for e in errors]}"

    def test_velocity_log_seed_validates(self):
        schema   = load_json(os.path.join(SCHEMAS_DIR, "velocity_log.schema.json"))
        artifact = load_json(os.path.join(ARTIFACTS_DIR, "velocity_log.json"))
        validator = Draft7Validator(schema)
        errors = list(validator.iter_errors(artifact))
        assert errors == [], f"velocity_log.json failed: {[e.message for e in errors]}"

    def test_risk_register_has_at_least_one_risk(self):
        artifact = load_json(os.path.join(ARTIFACTS_DIR, "risk_register.json"))
        assert len(artifact.get("risks", [])) >= 1

    def test_velocity_log_has_sprints(self):
        artifact = load_json(os.path.join(ARTIFACTS_DIR, "velocity_log.json"))
        assert len(artifact.get("sprints", [])) >= 1

    def test_risk_ids_are_unique(self):
        artifact = load_json(os.path.join(ARTIFACTS_DIR, "risk_register.json"))
        ids = [r["risk_id"] for r in artifact.get("risks", [])]
        assert len(ids) == len(set(ids)), "Duplicate risk IDs found in seed data"

    def test_sprint_ids_are_unique(self):
        artifact = load_json(os.path.join(ARTIFACTS_DIR, "velocity_log.json"))
        ids = [s["sprint_id"] for s in artifact.get("sprints", [])]
        assert len(ids) == len(set(ids)), "Duplicate sprint IDs found in seed data"

    def test_risk_dates_are_iso_format(self):
        artifact = load_json(os.path.join(ARTIFACTS_DIR, "risk_register.json"))
        import re
        pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
        for risk in artifact.get("risks", []):
            assert pattern.match(risk["date"]), f"Bad date format in {risk['risk_id']}: {risk['date']}"


# ── 3. Agent output parsing logic (replicates the n8n Code node) ─────────────

def parse_agent_output(raw: str) -> dict:
    """Mirrors the JS logic in the n8n Parse Agent Output node."""
    cleaned = raw.replace("```json", "").replace("```", "").strip()
    parsed = json.loads(cleaned)

    output_type = "UNKNOWN"
    if parsed.get("action") == "NO_ACTION":
        output_type = "NO_ACTION"
    elif parsed.get("risk_id"):
        output_type = "RISK"
    elif parsed.get("sprint_id"):
        output_type = "VELOCITY"
    elif parsed.get("id", "").startswith("SH-"):
        output_type = "STAKEHOLDER"

    parsed["_output_type"] = output_type
    return parsed


class TestAgentOutputParsing:

    def test_parses_clean_risk_json(self):
        raw = json.dumps({
            "risk_id": "RSK-004", "title": "Test risk", "category": "Technical",
            "probability": "Medium", "impact_score": 5,
            "mitigation": "Add more tests", "status": "Open", "date": "2026-05-22"
        })
        result = parse_agent_output(raw)
        assert result["_output_type"] == "RISK"
        assert result["risk_id"] == "RSK-004"

    def test_strips_markdown_fences(self):
        raw = "```json\n{\"action\": \"NO_ACTION\", \"reason\": \"Nothing notable\", \"snapshot_digest\": \"routine commits only\"}\n```"
        result = parse_agent_output(raw)
        assert result["_output_type"] == "NO_ACTION"
        assert result["reason"] == "Nothing notable"

    def test_parses_velocity_output(self):
        raw = json.dumps({
            "sprint_id": "SP-03",
            "start_date": "2026-05-12",
            "end_date": "2026-05-25",
            "status": "Active",
            "metrics": {
                "commits_total": 29, "prs_merged": 4,
                "prs_opened": 6, "issues_closed": 6, "issues_opened": 9
            },
            "blockers": [],
            "achievements": [],
            "summary": "Sprint is tracking below target due to two blockers.",
            "ai_confidence": 0.83
        })
        result = parse_agent_output(raw)
        assert result["_output_type"] == "VELOCITY"

    def test_parses_stakeholder_output(self):
        raw = json.dumps({
            "id": "SH-004", "name": "New Dev", "role": "Backend Engineer",
            "influence": "Low", "interest": "High",
            "current_engagement": "Neutral", "desired_engagement": "Supportive"
        })
        result = parse_agent_output(raw)
        assert result["_output_type"] == "STAKEHOLDER"

    def test_unknown_output_type_labelled_correctly(self):
        raw = json.dumps({"something_unexpected": True})
        result = parse_agent_output(raw)
        assert result["_output_type"] == "UNKNOWN"

    def test_raises_on_invalid_json(self):
        with pytest.raises(json.JSONDecodeError):
            parse_agent_output("this is not json at all")

    def test_no_action_output_has_reason(self):
        raw = json.dumps({
            "action": "NO_ACTION",
            "reason": "All commits are routine feature work with no risk signals",
            "snapshot_digest": "5 commits, 0 reverts"
        })
        result = parse_agent_output(raw)
        assert result["_output_type"] == "NO_ACTION"
        assert "reason" in result

    def test_risk_upsert_logic_creates_new(self):
        """Simulate the n8n Code node upsert logic for risk register."""
        existing = {"risks": [
            {"risk_id": "RSK-001", "title": "Old risk", "status": "Open"}
        ]}
        new_risk = {"risk_id": "RSK-002", "title": "New risk", "status": "Open"}

        idx = next((i for i, r in enumerate(existing["risks"]) if r["risk_id"] == new_risk["risk_id"]), -1)
        if idx >= 0:
            existing["risks"][idx] = {**existing["risks"][idx], **new_risk}
        else:
            existing["risks"].append(new_risk)

        assert len(existing["risks"]) == 2
        assert existing["risks"][1]["risk_id"] == "RSK-002"

    def test_risk_upsert_logic_updates_existing(self):
        """Simulate upsert when risk already exists."""
        existing = {"risks": [
            {"risk_id": "RSK-001", "title": "Old risk", "status": "Open", "probability": "Medium"}
        ]}
        updated_risk = {"risk_id": "RSK-001", "probability": "High", "impact_score": 9}

        idx = next((i for i, r in enumerate(existing["risks"]) if r["risk_id"] == updated_risk["risk_id"]), -1)
        if idx >= 0:
            existing["risks"][idx] = {**existing["risks"][idx], **updated_risk}
        else:
            existing["risks"].append(updated_risk)

        assert len(existing["risks"]) == 1
        assert existing["risks"][0]["probability"] == "High"
        assert existing["risks"][0]["impact_score"] == 9
        assert existing["risks"][0]["title"] == "Old risk"  # preserved from original


# ── 4. n8n workflow structure ─────────────────────────────────────────────────

class TestWorkflowStructure:

    def setup_method(self):
        self.workflow = load_json(os.path.join(N8N_DIR, "workflow.json"))

    def test_workflow_is_valid_json(self):
        assert isinstance(self.workflow, dict)

    def test_workflow_has_required_keys(self):
        for key in ["name", "nodes", "connections", "settings"]:
            assert key in self.workflow, f"Workflow missing key: {key}"

    def test_workflow_has_trigger_nodes(self):
        node_types = [n["type"] for n in self.workflow["nodes"]]
        assert any("scheduleTrigger" in t or "webhook" in t for t in node_types), \
            "Workflow must have at least one trigger node"

    def test_workflow_has_ai_agent_node(self):
        node_types = [n["type"] for n in self.workflow["nodes"]]
        assert any("agent" in t.lower() for t in node_types), \
            "Workflow must contain an AI Agent node"

    def test_workflow_has_execute_command_nodes(self):
        node_types = [n["type"] for n in self.workflow["nodes"]]
        exec_nodes = [t for t in node_types if "executeCommand" in t]
        assert len(exec_nodes) >= 2, \
            "Workflow needs at least 2 Execute Command nodes (git_extractor + kanban_connector)"

    def test_workflow_node_ids_are_unique(self):
        ids = [n["id"] for n in self.workflow["nodes"]]
        assert len(ids) == len(set(ids)), "Duplicate node IDs in workflow"

    def test_workflow_has_error_handler(self):
        node_names = [n["name"] for n in self.workflow["nodes"]]
        assert any("Error" in name or "error" in name for name in node_names), \
            "Workflow should have an error handler node"


# ── 5. System prompt completeness ─────────────────────────────────────────────

class TestSystemPrompt:

    def setup_method(self):
        with open(os.path.join(PROMPTS_DIR, "agent_system_prompt.md"), encoding="utf-8") as f:
            self.prompt = f.read()

    def test_prompt_defines_output_types(self):
        for output_type in ["OUTPUT A", "OUTPUT B", "OUTPUT C", "OUTPUT D"]:
            assert output_type in self.prompt, f"Prompt missing {output_type} definition"

    def test_prompt_includes_detection_rules(self):
        assert "Rule 1" in self.prompt
        assert "Rule 2" in self.prompt
        assert "Revert" in self.prompt

    def test_prompt_includes_strict_output_rules(self):
        assert "STRICT OUTPUT RULES" in self.prompt
        assert "NO_ACTION" in self.prompt

    def test_prompt_includes_confidence_scoring(self):
        assert "confidence" in self.prompt.lower()

    def test_prompt_specifies_json_only_output(self):
        assert "JSON only" in self.prompt or "strict JSON" in self.prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
