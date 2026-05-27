"""
test_api.py
-----------
FastAPI endpoint tests. Uses FastAPI's built-in TestClient — no running
server required. All file reads are tested against the real seed artifacts.

Run:
    pytest src/test_api.py -v
"""

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

# Patch ARTIFACTS_DIR to point at our real seed artifacts before importing app
import api.main as api_module

BASE         = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = BASE / "artifacts"
LOGS_DIR      = BASE / "logs"

# Ensure logs dir exists for tests
LOGS_DIR.mkdir(exist_ok=True)

api_module.ARTIFACTS_DIR = ARTIFACTS_DIR
api_module.LOGS_DIR      = LOGS_DIR

from api.main import app

client = TestClient(app, raise_server_exceptions=True)


# ── /api/health ───────────────────────────────────────────────────────────────

class TestHealth:

    def test_health_returns_200(self):
        r = client.get("/api/health")
        assert r.status_code == 200

    def test_health_has_status_ok(self):
        r = client.get("/api/health")
        assert r.json()["status"] == "ok"

    def test_health_reports_artifact_files(self):
        r = client.get("/api/health")
        data = r.json()
        assert "artifacts" in data
        assert "risk_register.json" in data["artifacts"]
        assert "velocity_log.json"  in data["artifacts"]

    def test_health_risk_register_exists(self):
        r = client.get("/api/health")
        assert r.json()["artifacts"]["risk_register.json"]["exists"] is True

    def test_health_has_timestamp(self):
        r = client.get("/api/health")
        assert "timestamp" in r.json()


# ── /api/risks ────────────────────────────────────────────────────────────────

class TestRisks:

    def test_get_risks_returns_200(self):
        r = client.get("/api/risks")
        assert r.status_code == 200

    def test_get_risks_has_required_keys(self):
        data = client.get("/api/risks").json()
        for key in ["risks", "total", "last_updated"]:
            assert key in data, f"Missing key: {key}"

    def test_get_risks_returns_list(self):
        data = client.get("/api/risks").json()
        assert isinstance(data["risks"], list)

    def test_get_risks_total_matches_list_length(self):
        data = client.get("/api/risks").json()
        assert data["total"] == len(data["risks"])

    def test_get_risks_sorted_by_risk_score_desc(self):
        risks = client.get("/api/risks").json()["risks"]
        scores = [r.get("risk_score", 0) for r in risks]
        assert scores == sorted(scores, reverse=True)

    def test_get_risks_filter_by_status(self):
        r = client.get("/api/risks?status=Open")
        assert r.status_code == 200
        risks = r.json()["risks"]
        for risk in risks:
            assert risk["status"] == "Open"

    def test_get_risks_filter_by_category(self):
        r = client.get("/api/risks?category=Technical")
        assert r.status_code == 200
        risks = r.json()["risks"]
        for risk in risks:
            assert risk["category"] == "Technical"

    def test_get_risks_filter_by_min_impact(self):
        r = client.get("/api/risks?min_impact=8")
        assert r.status_code == 200
        risks = r.json()["risks"]
        for risk in risks:
            assert risk["impact_score"] >= 8

    def test_get_risks_empty_filter_returns_empty_list(self):
        r = client.get("/api/risks?status=Transferred")
        assert r.status_code == 200
        assert r.json()["risks"] == []
        assert r.json()["total"] == 0

    def test_each_risk_has_required_fields(self):
        risks = client.get("/api/risks").json()["risks"]
        required = {"risk_id", "title", "category", "probability", "impact_score", "status"}
        for risk in risks:
            missing = required - set(risk.keys())
            assert not missing, f"Risk {risk.get('risk_id')} missing: {missing}"


class TestRiskSummary:

    def test_summary_returns_200(self):
        r = client.get("/api/risks/summary")
        assert r.status_code == 200

    def test_summary_has_aggregation_fields(self):
        data = client.get("/api/risks/summary").json()
        for key in ["total", "open", "critical", "avg_impact", "by_status", "by_category"]:
            assert key in data, f"Missing key: {key}"

    def test_summary_total_is_integer(self):
        data = client.get("/api/risks/summary").json()
        assert isinstance(data["total"], int)
        assert data["total"] > 0

    def test_summary_avg_impact_in_valid_range(self):
        data = client.get("/api/risks/summary").json()
        assert 1 <= data["avg_impact"] <= 10

    def test_summary_by_category_is_dict(self):
        data = client.get("/api/risks/summary").json()
        assert isinstance(data["by_category"], dict)


class TestSingleRisk:

    def test_get_existing_risk_returns_200(self):
        r = client.get("/api/risks/RSK-001")
        assert r.status_code == 200

    def test_get_existing_risk_has_correct_id(self):
        data = client.get("/api/risks/RSK-001").json()
        assert data["risk_id"] == "RSK-001"

    def test_get_risk_case_insensitive(self):
        r = client.get("/api/risks/rsk-001")
        assert r.status_code == 200

    def test_get_nonexistent_risk_returns_404(self):
        r = client.get("/api/risks/RSK-999")
        assert r.status_code == 404

    def test_404_has_detail_message(self):
        r = client.get("/api/risks/RSK-999")
        assert "detail" in r.json()


# ── /api/velocity ─────────────────────────────────────────────────────────────

class TestVelocity:

    def test_get_velocity_returns_200(self):
        r = client.get("/api/velocity")
        assert r.status_code == 200

    def test_get_velocity_has_sprints(self):
        data = client.get("/api/velocity").json()
        assert "sprints" in data
        assert isinstance(data["sprints"], list)
        assert len(data["sprints"]) >= 1

    def test_get_velocity_has_sprint_count(self):
        data = client.get("/api/velocity").json()
        assert data["sprint_count"] == len(data["sprints"])

    def test_each_sprint_has_velocity_pct(self):
        sprints = client.get("/api/velocity").json()["sprints"]
        for s in sprints:
            assert "velocity_pct" in s
            assert 0 <= s["velocity_pct"] <= 100

    def test_each_sprint_has_required_fields(self):
        sprints = client.get("/api/velocity").json()["sprints"]
        required = {"sprint_id", "start_date", "end_date", "status", "metrics", "summary"}
        for s in sprints:
            missing = required - set(s.keys())
            assert not missing, f"Sprint {s.get('sprint_id')} missing: {missing}"

    def test_get_current_sprint_returns_200(self):
        r = client.get("/api/velocity/current")
        assert r.status_code == 200

    def test_current_sprint_is_active_or_latest(self):
        data = client.get("/api/velocity/current").json()
        assert data.get("status") in ("Active", "Complete", "Cancelled")

    def test_get_sprint_by_id(self):
        r = client.get("/api/velocity/SP-01")
        assert r.status_code == 200
        assert r.json()["sprint_id"] == "SP-01"

    def test_get_sprint_case_insensitive(self):
        r = client.get("/api/velocity/sp-01")
        assert r.status_code == 200

    def test_get_nonexistent_sprint_returns_404(self):
        r = client.get("/api/velocity/SP-99")
        assert r.status_code == 404

    def test_velocity_pct_calculation_correct(self):
        sprints = client.get("/api/velocity").json()["sprints"]
        sp1 = next(s for s in sprints if s["sprint_id"] == "SP-01")
        planned   = sp1["metrics"]["story_points_planned"]
        completed = sp1["metrics"]["story_points_completed"]
        expected  = round(completed / planned * 100, 1)
        assert sp1["velocity_pct"] == expected


# ── /api/stakeholders ─────────────────────────────────────────────────────────

class TestStakeholders:

    def test_get_stakeholders_returns_200(self):
        r = client.get("/api/stakeholders")
        assert r.status_code == 200

    def test_get_stakeholders_returns_dict(self):
        data = client.get("/api/stakeholders").json()
        assert isinstance(data, dict)
        assert "stakeholders" in data


# ── /api/pipeline ─────────────────────────────────────────────────────────────

class TestPipeline:

    def test_get_runs_returns_200(self):
        r = client.get("/api/pipeline/runs")
        assert r.status_code == 200

    def test_get_runs_has_required_keys(self):
        data = client.get("/api/pipeline/runs").json()
        assert "runs"  in data
        assert "total" in data
        assert "limit" in data

    def test_get_runs_default_limit_respected(self):
        data = client.get("/api/pipeline/runs").json()
        assert data["limit"] == 50

    def test_get_runs_custom_limit(self):
        r = client.get("/api/pipeline/runs?limit=5")
        assert r.status_code == 200
        assert r.json()["limit"] == 5

    def test_get_stats_returns_200(self):
        r = client.get("/api/pipeline/stats")
        assert r.status_code == 200

    def test_get_stats_has_key_fields(self):
        data = client.get("/api/pipeline/stats").json()
        # Either real stats or a "no runs" message — both valid
        assert "total_runs" in data

    def test_trigger_without_github_token_returns_400(self):
        """Without a GITHUB_TOKEN set, trigger should return 400."""
        import api.main as m
        original = os.environ.pop("GITHUB_TOKEN", None)
        m_original = m.os.environ.pop("GITHUB_TOKEN", None)
        try:
            r = client.post("/api/pipeline/trigger", json={
                "repo": "owner/repo",
                "dry_run": True,
            })
            assert r.status_code == 400
            assert "GITHUB_TOKEN" in r.json()["detail"]
        finally:
            if original:
                os.environ["GITHUB_TOKEN"] = original
            if m_original:
                m.os.environ["GITHUB_TOKEN"] = m_original


# ── /api/dashboard ────────────────────────────────────────────────────────────

class TestDashboard:

    def test_dashboard_returns_200(self):
        r = client.get("/api/dashboard")
        assert r.status_code == 200

    def test_dashboard_has_all_sections(self):
        data = client.get("/api/dashboard").json()
        for key in ["meta", "kpis", "risks", "sprints", "pipeline_runs"]:
            assert key in data, f"Dashboard missing section: {key}"

    def test_dashboard_kpis_has_required_fields(self):
        kpis = client.get("/api/dashboard").json()["kpis"]
        for key in ["open_risks", "critical_risks", "active_blockers",
                    "sprint_velocity", "pipeline_runs", "total_tokens",
                    "ai_confidence", "current_sprint"]:
            assert key in kpis, f"KPIs missing: {key}"

    def test_dashboard_risks_sorted_by_score(self):
        risks = client.get("/api/dashboard").json()["risks"]
        scores = [r.get("risk_score", 0) for r in risks]
        assert scores == sorted(scores, reverse=True)

    def test_dashboard_meta_has_timestamps(self):
        meta = client.get("/api/dashboard").json()["meta"]
        assert "generated_at" in meta
        assert "risks_updated" in meta

    def test_dashboard_kpi_open_risks_matches_risk_endpoint(self):
        dashboard_open = client.get("/api/dashboard").json()["kpis"]["open_risks"]
        risks_open     = client.get("/api/risks?status=Open").json()["total"]
        risks_mitig    = client.get("/api/risks?status=Mitigating").json()["total"]
        assert dashboard_open == risks_open + risks_mitig

    def test_dashboard_sprint_count_matches_velocity_endpoint(self):
        dashboard_sprints  = len(client.get("/api/dashboard").json()["sprints"])
        velocity_sprints   = client.get("/api/velocity").json()["sprint_count"]
        assert dashboard_sprints == velocity_sprints


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
