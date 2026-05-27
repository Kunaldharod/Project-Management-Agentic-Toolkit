"""
test_phase3.py
--------------
Phase 3 test suite — end-to-end pipeline validation.

Test groups:
  1. LLMResponse — JSON extraction, token tracking
  2. ContextLoader — prompt + artifact loading, user message assembly
  3. OutputClassifier — all 4 output types + edge cases
  4. SchemaValidator — valid and invalid payloads per output type
  5. ArtifactWriter — upsert create/update logic for all 3 artifact types
  6. AgentPipeline (mocked LLM) — full loop for each output type
  7. AgentPipeline (mocked LLM) — error recovery paths
  8. Retry logic — backoff behaviour on transient errors
  9. TokenBudget — tracking and over-budget detection
 10. PipelineResult — summary formatting and success flag

No real API keys needed — all LLM calls are mocked.

Run:
    pytest src/test_phase3.py -v
    pytest src/test_phase3.py -v -k "Pipeline"    # just pipeline tests
"""

import json
import os
import sys
import tempfile
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from llm_client import LLMResponse, TokenBudget, AnthropicAdapter, OpenAIAdapter, build_llm_client
from agent_pipeline import (
    AgentPipeline, PipelineResult, ContextLoader, ArtifactWriter,
    classify_output, validate_against_schema,
    OUTPUT_RISK, OUTPUT_VELOCITY, OUTPUT_STAKEHOLDER, OUTPUT_NO_ACTION, OUTPUT_UNKNOWN,
    ARTIFACTS_DIR, SCHEMAS_DIR, PROMPTS_DIR,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

SAMPLE_SNAPSHOT = """=== GIT REPOSITORY SNAPSHOT ===
Repo        : org/drone-platform
Branch      : main
Language    : Python
Extracted   : 2026-05-22 10:00 UTC
Window      : last 50 commits / issues updated in past 7 days

--- COMMITS (last 12) ---
  [a1b2c3d4] 2026-05-21 09:00 | Priya Sharma: revert: drone altitude calculation — diverges above 200m
  [e5f6g7h8] 2026-05-21 11:00 | Arjun Mehta: fix: revert trajectory algorithm to v1.2
  [i9j0k1l2] 2026-05-20 14:00 | Priya Sharma: hotfix: memory leak in QGIS processing module
  [m3n4o5p6] 2026-05-20 16:00 | Kavya Nair: fix: increase heap threshold in QGIS plugin
  [q7r8s9t0] 2026-05-19 10:00 | Rohit Desai: feat: add altitude validation to pre-flight checks

--- OPEN PULL REQUESTS (2) ---
  PR#42 []: Revert drone trajectory calculation
    author=arjun-mehta | reviews=3 labels=['bug', 'high-priority']
    updated=2026-05-21 11:00 | https://github.com/org/drone-platform/pull/42
    desc: Reverting because trajectory diverges at altitude > 200m

--- OPEN ISSUES updated in past 7d (2) ---
  Issue#99: QGIS plugin crashes on startup with large datasets
    author=qa-kavya | comments=5 labels=['bug', 'blocker']
    updated=2026-05-22 14:00 | https://github.com/org/drone-platform/issues/99

=== END SNAPSHOT ==="""

VALID_RISK_RESPONSE = json.dumps({
    "risk_id": "RSK-004",
    "title": "Drone altitude calculation diverges above 200m — revert required",
    "category": "Technical",
    "probability": "High",
    "impact_score": 9,
    "risk_score": 7.2,
    "mitigation": "Revert PR#42 to stable v1.2 algorithm. Engage aerospace consultant. Add boundary validation at 150m.",
    "contingency": "Cap operational altitude at 150m until algorithm passes external safety review.",
    "status": "Open",
    "owner": "Arjun Mehta",
    "raised_from": "pr:42",
    "date": "2026-05-22",
    "tags": ["sprint-3", "drone-module", "safety-critical"]
})

VALID_VELOCITY_RESPONSE = json.dumps({
    "sprint_id": "SP-03",
    "start_date": "2026-05-12",
    "end_date": "2026-05-25",
    "status": "Active",
    "metrics": {
        "commits_total": 29,
        "prs_merged": 4,
        "prs_opened": 6,
        "issues_closed": 6,
        "issues_opened": 9,
        "velocity_trend": "Decelerating"
    },
    "blockers": [
        {
            "description": "Memory leak blocking CI merges",
            "linked_risk": "RSK-001",
            "impact": "High",
            "status": "Mitigating"
        }
    ],
    "achievements": ["QGIS alpha released to internal testers"],
    "summary": "Sprint 3 is tracking at 41% of target at midpoint. Two critical blockers — memory leak and altitude revert — are compounding. Immediate escalation recommended.",
    "ai_confidence": 0.85
})

VALID_STAKEHOLDER_RESPONSE = json.dumps({
    "id": "SH-005",
    "name": "Rohit Desai",
    "role": "Junior Backend Engineer",
    "influence": "Low",
    "interest": "High",
    "current_engagement": "Neutral",
    "desired_engagement": "Supportive",
    "activity_signal": {
        "commits_last_sprint": 4,
        "prs_opened": 1,
        "issues_reported": 0,
        "last_active": "2026-05-19"
    }
})

NO_ACTION_RESPONSE = json.dumps({
    "action": "NO_ACTION",
    "reason": "All commits are routine feature work. No risk signals, reverts, or blockers detected.",
    "snapshot_digest": "5 feature commits, 0 reverts"
})


def make_mock_llm_response(content: str, provider: str = "anthropic") -> MagicMock:
    mock = MagicMock(spec=LLMResponse)
    mock.content = content
    mock.provider = provider
    mock.model = "claude-sonnet-4-20250514" if provider == "anthropic" else "gpt-4o"
    mock.input_tokens = 1200
    mock.output_tokens = 280
    mock.total_tokens = 1480
    mock.attempts = 1
    mock.extract_json.return_value = json.loads(content)
    return mock


# ── 1. LLMResponse ────────────────────────────────────────────────────────────

class TestLLMResponse:

    def test_extract_json_clean(self):
        r = LLMResponse(content='{"risk_id": "RSK-001"}', provider="anthropic", model="claude")
        assert r.extract_json() == {"risk_id": "RSK-001"}

    def test_extract_json_strips_fences(self):
        r = LLMResponse(content='```json\n{"risk_id": "RSK-001"}\n```', provider="anthropic", model="claude")
        assert r.extract_json() == {"risk_id": "RSK-001"}

    def test_extract_json_raises_on_bad_content(self):
        r = LLMResponse(content="This is not JSON at all.", provider="anthropic", model="claude")
        with pytest.raises(json.JSONDecodeError):
            r.extract_json()

    def test_total_tokens_property(self):
        r = LLMResponse(content="{}", provider="anthropic", model="claude",
                        input_tokens=800, output_tokens=200)
        assert r.total_tokens == 1000


# ── 2. TokenBudget ────────────────────────────────────────────────────────────

class TestTokenBudget:

    def test_records_usage(self):
        budget = TokenBudget(max_tokens=10_000)
        mock_resp = MagicMock()
        mock_resp.input_tokens = 500
        mock_resp.output_tokens = 100
        budget.record(mock_resp)
        assert budget.total_used == 600

    def test_not_over_budget_initially(self):
        budget = TokenBudget(max_tokens=50_000)
        assert not budget.is_over_budget()

    def test_over_budget_detection(self):
        budget = TokenBudget(max_tokens=100)
        mock_resp = MagicMock()
        mock_resp.input_tokens = 90
        mock_resp.output_tokens = 30
        budget.record(mock_resp)
        assert budget.is_over_budget()

    def test_summary_string(self):
        budget = TokenBudget(max_tokens=50_000)
        summary = budget.summary()
        assert "Tokens used" in summary
        assert "budget" in summary


# ── 3. ContextLoader ─────────────────────────────────────────────────────────

class TestContextLoader:

    def test_load_system_prompt_returns_string(self):
        loader = ContextLoader()
        prompt = loader.load_system_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 100
        assert "PMBOK" in prompt

    def test_load_risk_register_returns_json_string(self):
        loader = ContextLoader()
        result = loader.load_risk_register()
        parsed = json.loads(result)
        assert "risks" in parsed

    def test_load_velocity_log_returns_json_string(self):
        loader = ContextLoader()
        result = loader.load_velocity_log()
        parsed = json.loads(result)
        assert "sprints" in parsed

    def test_build_user_message_contains_all_sections(self):
        loader = ContextLoader()
        msg = loader.build_user_message(
            snapshot_text=SAMPLE_SNAPSHOT,
            sprint_id="SP-03",
            sprint_start="2026-05-12",
            sprint_end="2026-05-25",
        )
        assert "GIT REPOSITORY SNAPSHOT" in msg
        assert "CURRENT RISK REGISTER" in msg
        assert "CURRENT VELOCITY LOG" in msg
        assert "SP-03" in msg
        assert "2026-05-12" in msg

    def test_build_user_message_contains_todays_date(self):
        from datetime import datetime, timezone
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        loader = ContextLoader()
        msg = loader.build_user_message(SAMPLE_SNAPSHOT, "SP-03", "2026-05-12", "2026-05-25")
        assert today in msg


# ── 4. OutputClassifier ───────────────────────────────────────────────────────

class TestOutputClassifier:

    def test_classifies_risk(self):
        assert classify_output({"risk_id": "RSK-001"}) == OUTPUT_RISK

    def test_classifies_velocity(self):
        assert classify_output({"sprint_id": "SP-03"}) == OUTPUT_VELOCITY

    def test_classifies_stakeholder(self):
        assert classify_output({"id": "SH-005"}) == OUTPUT_STAKEHOLDER

    def test_classifies_no_action(self):
        assert classify_output({"action": "NO_ACTION", "reason": "ok"}) == OUTPUT_NO_ACTION

    def test_classifies_unknown(self):
        assert classify_output({"something": "unexpected"}) == OUTPUT_UNKNOWN

    def test_no_action_takes_priority_over_risk_id(self):
        # Malformed response that has both — NO_ACTION should win
        assert classify_output({"action": "NO_ACTION", "risk_id": "RSK-001"}) == OUTPUT_NO_ACTION


# ── 5. SchemaValidator ────────────────────────────────────────────────────────

class TestSchemaValidator:

    def test_valid_risk_passes(self):
        payload = json.loads(VALID_RISK_RESPONSE)
        errors = validate_against_schema(OUTPUT_RISK, payload)
        assert errors == [], f"Unexpected errors: {errors}"

    def test_risk_missing_required_field_fails(self):
        payload = {"risk_id": "RSK-004", "title": "Something"}
        errors = validate_against_schema(OUTPUT_RISK, payload)
        assert len(errors) > 0

    def test_risk_bad_category_fails(self):
        payload = json.loads(VALID_RISK_RESPONSE)
        payload["category"] = "Political"
        errors = validate_against_schema(OUTPUT_RISK, payload)
        assert any("category" in e for e in errors)

    def test_risk_impact_score_out_of_range_fails(self):
        payload = json.loads(VALID_RISK_RESPONSE)
        payload["impact_score"] = 15
        errors = validate_against_schema(OUTPUT_RISK, payload)
        assert len(errors) > 0

    def test_valid_velocity_passes(self):
        # Agent outputs a single sprint object — the validator wraps it internally
        payload = json.loads(VALID_VELOCITY_RESPONSE)
        errors = validate_against_schema(OUTPUT_VELOCITY, payload)
        assert errors == [], f"Unexpected errors: {errors}"

    def test_no_action_has_no_schema(self):
        errors = validate_against_schema(OUTPUT_NO_ACTION, {"action": "NO_ACTION"})
        assert errors == []

    def test_unknown_has_no_schema(self):
        errors = validate_against_schema(OUTPUT_UNKNOWN, {"whatever": True})
        assert errors == []


# ── 6. ArtifactWriter ─────────────────────────────────────────────────────────

class TestArtifactWriter:

    def setup_method(self):
        """Work in a temp directory so we don't touch real artifacts."""
        self._tmpdir = tempfile.TemporaryDirectory()
        self._orig_artifacts = os.environ.get("ARTIFACTS_OVERRIDE", "")
        # Patch ARTIFACTS_DIR in agent_pipeline for each test
        self.tmppath = Path(self._tmpdir.name)

    def teardown_method(self):
        self._tmpdir.cleanup()

    def _writer_with_tmp(self, seed_risks=None, seed_sprints=None):
        """Create an ArtifactWriter that writes to temp dir."""
        writer = ArtifactWriter()

        # Monkey-patch write paths
        risk_path = self.tmppath / "risk_register.json"
        vel_path  = self.tmppath / "velocity_log.json"
        sh_path   = self.tmppath / "stakeholder_map.json"

        seed_risk = {"project_id": "PROJ-001", "last_updated": "2026-05-01",
                     "risks": seed_risks or []}
        seed_vel  = {"project_id": "PROJ-001", "last_updated": "2026-05-01",
                     "sprints": seed_sprints or []}

        risk_path.write_text(json.dumps(seed_risk), encoding="utf-8")
        vel_path.write_text(json.dumps(seed_vel), encoding="utf-8")

        # Patch the paths inside the module
        import agent_pipeline as ap
        self._orig_artifacts_dir = ap.ARTIFACTS_DIR
        ap.ARTIFACTS_DIR = self.tmppath

        return writer, risk_path, vel_path, sh_path

    def teardown_method(self):
        import agent_pipeline as ap
        if hasattr(self, "_orig_artifacts_dir"):
            ap.ARTIFACTS_DIR = self._orig_artifacts_dir
        self._tmpdir.cleanup()

    def test_upsert_risk_creates_new_entry(self):
        writer, risk_path, _, _ = self._writer_with_tmp()
        new_risk = json.loads(VALID_RISK_RESPONSE)
        writer.upsert_risk(new_risk)
        data = json.loads(risk_path.read_text(encoding="utf-8"))
        assert any(r["risk_id"] == "RSK-004" for r in data["risks"])

    def test_upsert_risk_updates_existing_entry(self):
        existing = [{"risk_id": "RSK-004", "title": "Old title", "status": "Open",
                     "probability": "Medium", "impact_score": 5}]
        writer, risk_path, _, _ = self._writer_with_tmp(seed_risks=existing)
        updated = json.loads(VALID_RISK_RESPONSE)
        updated["probability"] = "Critical"
        writer.upsert_risk(updated)
        data = json.loads(risk_path.read_text(encoding="utf-8"))
        risks = [r for r in data["risks"] if r["risk_id"] == "RSK-004"]
        assert len(risks) == 1
        assert risks[0]["probability"] == "Critical"
        assert risks[0]["title"] == updated["title"]  # updated

    def test_upsert_risk_preserves_existing_risks(self):
        existing = [{"risk_id": "RSK-001", "title": "Existing", "status": "Open"}]
        writer, risk_path, _, _ = self._writer_with_tmp(seed_risks=existing)
        new_risk = json.loads(VALID_RISK_RESPONSE)
        writer.upsert_risk(new_risk)
        data = json.loads(risk_path.read_text(encoding="utf-8"))
        assert len(data["risks"]) == 2

    def test_upsert_risk_strips_internal_fields(self):
        writer, risk_path, _, _ = self._writer_with_tmp()
        risk_with_internals = json.loads(VALID_RISK_RESPONSE)
        risk_with_internals["_output_type"] = "RISK"
        risk_with_internals["_parsed_at"] = "2026-05-22T10:00:00Z"
        writer.upsert_risk(risk_with_internals)
        data = json.loads(risk_path.read_text(encoding="utf-8"))
        saved = data["risks"][0]
        assert "_output_type" not in saved
        assert "_parsed_at" not in saved

    def test_upsert_velocity_creates_sprint(self):
        writer, _, vel_path, _ = self._writer_with_tmp()
        sprint = json.loads(VALID_VELOCITY_RESPONSE)
        writer.upsert_velocity(sprint)
        data = json.loads(vel_path.read_text(encoding="utf-8"))
        assert any(s["sprint_id"] == "SP-03" for s in data["sprints"])

    def test_upsert_velocity_updates_existing_sprint(self):
        existing_sprint = json.loads(VALID_VELOCITY_RESPONSE)
        existing_sprint["status"] = "Active"
        writer, _, vel_path, _ = self._writer_with_tmp(seed_sprints=[existing_sprint])
        updated = json.loads(VALID_VELOCITY_RESPONSE)
        updated["status"] = "Complete"
        writer.upsert_velocity(updated)
        data = json.loads(vel_path.read_text(encoding="utf-8"))
        sprints = [s for s in data["sprints"] if s["sprint_id"] == "SP-03"]
        assert len(sprints) == 1
        assert sprints[0]["status"] == "Complete"


# ── 7. AgentPipeline (mocked LLM) ────────────────────────────────────────────

class TestAgentPipelineMocked:
    """Tests the full pipeline loop with the LLM call mocked out."""

    def _make_pipeline(self, mock_response_content: str) -> AgentPipeline:
        pipeline = AgentPipeline.__new__(AgentPipeline)
        pipeline.push_kanban = False
        pipeline.kanban_provider = "trello"
        pipeline.dry_run = True    # never write to real artifacts in tests
        pipeline.loader  = ContextLoader()
        pipeline.writer  = ArtifactWriter()

        from llm_client import TokenBudget
        pipeline.budget = TokenBudget()

        mock_llm = MagicMock()
        mock_llm.__class__.__name__ = "MockAdapter"
        mock_response = make_mock_llm_response(mock_response_content)
        mock_llm.call.return_value = mock_response
        pipeline.llm = mock_llm
        return pipeline

    def test_pipeline_returns_risk_result(self):
        pipeline = self._make_pipeline(VALID_RISK_RESPONSE)
        result = pipeline.run(SAMPLE_SNAPSHOT)
        assert result.output_type == OUTPUT_RISK
        assert result.payload["risk_id"] == "RSK-004"

    def test_pipeline_returns_velocity_result(self):
        pipeline = self._make_pipeline(VALID_VELOCITY_RESPONSE)
        result = pipeline.run(SAMPLE_SNAPSHOT)
        assert result.output_type == OUTPUT_VELOCITY
        assert result.payload["sprint_id"] == "SP-03"

    def test_pipeline_returns_no_action_result(self):
        pipeline = self._make_pipeline(NO_ACTION_RESPONSE)
        result = pipeline.run(SAMPLE_SNAPSHOT)
        assert result.output_type == OUTPUT_NO_ACTION

    def test_pipeline_populates_token_counts(self):
        pipeline = self._make_pipeline(VALID_RISK_RESPONSE)
        result = pipeline.run(SAMPLE_SNAPSHOT)
        assert result.input_tokens  == 1200
        assert result.output_tokens == 280

    def test_pipeline_records_llm_provider(self):
        pipeline = self._make_pipeline(VALID_RISK_RESPONSE)
        result = pipeline.run(SAMPLE_SNAPSHOT)
        assert result.llm_provider == "anthropic"

    def test_pipeline_success_flag_true_on_valid_output(self):
        pipeline = self._make_pipeline(VALID_RISK_RESPONSE)
        result = pipeline.run(SAMPLE_SNAPSHOT)
        assert result.success is True
        assert result.validation_errors == []

    def test_pipeline_success_flag_false_on_invalid_schema(self):
        bad_risk = json.dumps({"risk_id": "RSK-004", "title": "Missing fields"})
        pipeline = self._make_pipeline(bad_risk)
        result = pipeline.run(SAMPLE_SNAPSHOT)
        assert result.success is False
        assert len(result.validation_errors) > 0

    def test_pipeline_assigns_run_id(self):
        pipeline = self._make_pipeline(NO_ACTION_RESPONSE)
        result = pipeline.run(SAMPLE_SNAPSHOT)
        assert result.run_id != ""
        assert len(result.run_id) == 8

    def test_pipeline_custom_run_id_preserved(self):
        pipeline = self._make_pipeline(NO_ACTION_RESPONSE)
        result = pipeline.run(SAMPLE_SNAPSHOT, run_id="test-run-1")
        assert result.run_id == "test-run-1"

    def test_pipeline_duration_is_positive(self):
        pipeline = self._make_pipeline(NO_ACTION_RESPONSE)
        result = pipeline.run(SAMPLE_SNAPSHOT)
        assert result.duration_sec > 0


# ── 8. Error recovery ─────────────────────────────────────────────────────────

class TestPipelineErrorRecovery:

    def _make_pipeline_with_bad_llm(self, bad_content: str) -> AgentPipeline:
        pipeline = AgentPipeline.__new__(AgentPipeline)
        pipeline.push_kanban = False
        pipeline.dry_run = True
        pipeline.loader  = ContextLoader()
        pipeline.writer  = ArtifactWriter()
        from llm_client import TokenBudget
        pipeline.budget = TokenBudget()

        mock_llm = MagicMock()
        mock_llm.__class__.__name__ = "MockAdapter"
        mock_response = MagicMock(spec=LLMResponse)
        mock_response.content = bad_content
        mock_response.provider = "anthropic"
        mock_response.model = "claude"
        mock_response.input_tokens = 500
        mock_response.output_tokens = 50
        mock_response.attempts = 1
        mock_response.extract_json.side_effect = json.JSONDecodeError("bad json", "", 0)
        mock_llm.call.return_value = mock_response
        pipeline.llm = mock_llm
        return pipeline

    def test_pipeline_handles_json_parse_failure_gracefully(self):
        pipeline = self._make_pipeline_with_bad_llm("I cannot comply with this request.")
        result = pipeline.run(SAMPLE_SNAPSHOT)
        assert result.success is False
        assert result.output_type == OUTPUT_UNKNOWN
        assert any("JSON parse" in e for e in result.validation_errors)

    def test_pipeline_includes_raw_output_on_parse_failure(self):
        pipeline = self._make_pipeline_with_bad_llm("Not JSON")
        result = pipeline.run(SAMPLE_SNAPSHOT)
        assert "raw" in result.payload


# ── 9. PipelineResult ─────────────────────────────────────────────────────────

class TestPipelineResult:

    def test_success_true_when_no_errors(self):
        r = PipelineResult(output_type=OUTPUT_RISK, payload={}, validation_errors=[])
        assert r.success is True

    def test_success_false_when_errors_present(self):
        r = PipelineResult(output_type=OUTPUT_RISK, payload={}, validation_errors=["bad field"])
        assert r.success is False

    def test_summary_contains_key_info(self):
        r = PipelineResult(
            output_type=OUTPUT_RISK, payload={},
            llm_provider="anthropic", llm_model="claude",
            input_tokens=800, output_tokens=200,
            duration_sec=2.5, validation_errors=[]
        )
        summary = r.summary()
        assert "SUCCESS" in summary
        assert "RISK" in summary
        assert "anthropic" in summary
        assert "2.5" in summary

    def test_summary_shows_failed_on_errors(self):
        r = PipelineResult(output_type=OUTPUT_UNKNOWN, payload={},
                           validation_errors=["something broke"])
        assert "FAILED" in r.summary()


# ── 10. LLM adapter factory ───────────────────────────────────────────────────

class TestBuildLLMClient:

    def test_raises_when_no_keys_set(self):
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "", "OPENAI_API_KEY": ""}, clear=False):
            with pytest.raises(EnvironmentError, match="No LLM API key"):
                build_llm_client()

    def test_prefers_anthropic_when_both_set(self):
        with patch.dict(os.environ, {
            "ANTHROPIC_API_KEY": "sk-ant-fake",
            "OPENAI_API_KEY": "sk-fake"
        }, clear=False):
            with patch("llm_client.AnthropicAdapter.__init__", return_value=None):
                client = build_llm_client()
                assert isinstance(client, AnthropicAdapter)

    def test_falls_back_to_openai(self):
        with patch.dict(os.environ, {
            "ANTHROPIC_API_KEY": "",
            "OPENAI_API_KEY": "sk-fake"
        }, clear=False):
            with patch("llm_client.OpenAIAdapter.__init__", return_value=None):
                client = build_llm_client()
                assert isinstance(client, OpenAIAdapter)

    def test_explicit_provider_openai(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-fake"}, clear=False):
            with patch("llm_client.OpenAIAdapter.__init__", return_value=None):
                client = build_llm_client(provider="openai")
                assert isinstance(client, OpenAIAdapter)


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
