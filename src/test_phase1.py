"""
test_phase1.py
--------------
Self-contained tests for Phase 1 (git_extractor + kanban_connector).
All HTTP calls are mocked — no real tokens required.

Run:
    pytest src/test_phase1.py -v
"""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

import pytest
import responses as resp_mock

from git_extractor import (
    GitHubClient,
    build_agent_payload,
    format_commits,
    _truncate,
    _fmt_date,
)
from kanban_connector import (
    validate_payload,
    build_card_title,
    build_card_description,
    VALID_CATEGORIES,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

MOCK_COMMIT = {
    "sha": "abc12345def67890",
    "commit": {
        "author": {"name": "Priya Sharma", "date": "2026-05-20T10:30:00Z"},
        "message": "fix: resolve memory leak in QGIS trajectory processing module\n\nDetailed description follows.",
    },
    "html_url": "https://github.com/org/repo/commit/abc12345",
}

MOCK_PR = {
    "number": 42,
    "title": "Revert drone trajectory calculation algorithm",
    "user": {"login": "dev-arjun"},
    "state": "open",
    "draft": False,
    "labels": [{"name": "bug"}, {"name": "high-priority"}],
    "body": "Reverting because trajectory diverges at altitude > 200m",
    "created_at": "2026-05-18T08:00:00Z",
    "updated_at": "2026-05-21T12:00:00Z",
    "review_comments": 3,
    "html_url": "https://github.com/org/repo/pull/42",
}

MOCK_ISSUE = {
    "number": 99,
    "title": "QGIS plugin crashes on startup with large datasets",
    "user": {"login": "qa-kavya"},
    "labels": [{"name": "bug"}, {"name": "blocker"}],
    "body": "Reproducible with any dataset > 10GB. Stack trace attached.",
    "comments": 5,
    "created_at": "2026-05-15T09:00:00Z",
    "updated_at": "2026-05-22T14:00:00Z",
    "html_url": "https://github.com/org/repo/issues/99",
}

MOCK_REPO_META = {
    "full_name": "org/repo",
    "default_branch": "main",
    "open_issues_count": 12,
    "language": "Python",
    "description": "Drone trajectory analysis platform",
}

VALID_RISK_PAYLOAD = {
    "risk_id": "RSK-001",
    "title": "Memory leak in QGIS trajectory processing module",
    "category": "Technical",
    "probability": "High",
    "impact_score": 8,
    "mitigation": "Profile memory allocation in processing loop, add ceiling threshold, add unit tests for memory usage",
    "status": "Open",
    "raised_from": "commit:abc12345",
    "date": "2026-05-22",
}


# ── git_extractor tests ───────────────────────────────────────────────────────

class TestGitHubClient:

    @resp_mock.activate
    def test_get_commits_returns_formatted_list(self):
        resp_mock.add(
            resp_mock.GET,
            "https://api.github.com/repos/org/repo/commits",
            json=[MOCK_COMMIT],
            status=200,
        )
        client = GitHubClient(token="fake-token", repo="org/repo")
        commits = client.get_commits(limit=10)

        assert len(commits) == 1
        assert commits[0]["sha"] == "abc12345"    # truncated to 8 chars
        assert commits[0]["author"] == "Priya Sharma"
        assert "memory leak" in commits[0]["message"]

    @resp_mock.activate
    def test_get_commits_raises_on_404(self):
        resp_mock.add(
            resp_mock.GET,
            "https://api.github.com/repos/org/missing-repo/commits",
            json={"message": "Not Found"},
            status=404,
        )
        client = GitHubClient(token="fake-token", repo="org/missing-repo")
        with pytest.raises(FileNotFoundError):
            client.get_commits()

    @resp_mock.activate
    def test_get_pull_requests_excludes_no_prs(self):
        resp_mock.add(
            resp_mock.GET,
            "https://api.github.com/repos/org/repo/pulls",
            json=[MOCK_PR],
            status=200,
        )
        client = GitHubClient(token="fake-token", repo="org/repo")
        prs = client.get_pull_requests()

        assert len(prs) == 1
        assert prs[0]["number"] == 42
        assert "bug" in prs[0]["labels"]
        assert prs[0]["draft"] is False

    @resp_mock.activate
    def test_get_issues_excludes_pull_requests(self):
        # GitHub returns PRs in the issues endpoint — should be filtered out
        pr_as_issue = {**MOCK_ISSUE, "pull_request": {"url": "..."}}
        resp_mock.add(
            resp_mock.GET,
            "https://api.github.com/repos/org/repo/issues",
            json=[MOCK_ISSUE, pr_as_issue],
            status=200,
        )
        client = GitHubClient(token="fake-token", repo="org/repo")
        issues = client.get_issues()

        assert len(issues) == 1
        assert issues[0]["number"] == 99

    def test_requires_token(self):
        with pytest.raises(ValueError, match="GITHUB_TOKEN"):
            GitHubClient(token="", repo="org/repo")


class TestFormatters:

    def test_format_commits_returns_placeholder_on_empty(self):
        result = format_commits([])
        assert "no commits" in result

    def test_truncate_adds_ellipsis(self):
        long_text = "a" * 400
        result = _truncate(long_text, 300)
        assert len(result) == 301  # 300 chars + "…"
        assert result.endswith("…")

    def test_truncate_leaves_short_text_unchanged(self):
        assert _truncate("short", 300) == "short"

    def test_fmt_date_parses_iso(self):
        result = _fmt_date("2026-05-22T10:30:00Z")
        assert result == "2026-05-22 10:30"

    def test_fmt_date_returns_original_on_bad_input(self):
        assert _fmt_date("not-a-date") == "not-a-date"

    def test_build_agent_payload_contains_all_sections(self):
        commits = [{"sha": "abc12345", "author": "Dev", "date": "2026-05-22T10:00:00Z", "message": "fix: memory leak", "url": ""}]
        prs     = []
        issues  = []
        meta    = {"name": "org/repo", "default_branch": "main", "language": "Python"}

        payload = build_agent_payload(meta, commits, prs, issues, 50, 7)
        assert "GIT REPOSITORY SNAPSHOT" in payload
        assert "COMMITS" in payload
        assert "OPEN PULL REQUESTS" in payload
        assert "OPEN ISSUES" in payload
        assert "END SNAPSHOT" in payload
        assert "memory leak" in payload


# ── kanban_connector tests ────────────────────────────────────────────────────

class TestValidatePayload:

    def test_valid_payload_passes(self):
        errors = validate_payload(VALID_RISK_PAYLOAD)
        assert errors == []

    def test_missing_required_fields_fails(self):
        bad = {"risk_id": "RSK-001", "title": "Something"}
        errors = validate_payload(bad)
        assert any("Missing required fields" in e for e in errors)

    def test_invalid_category_fails(self):
        bad = {**VALID_RISK_PAYLOAD, "category": "Political"}
        errors = validate_payload(bad)
        assert any("category" in e for e in errors)

    def test_invalid_probability_fails(self):
        bad = {**VALID_RISK_PAYLOAD, "probability": "Extreme"}
        errors = validate_payload(bad)
        assert any("probability" in e for e in errors)

    def test_impact_score_out_of_range_fails(self):
        bad = {**VALID_RISK_PAYLOAD, "impact_score": 15}
        errors = validate_payload(bad)
        assert any("impact_score" in e for e in errors)

    def test_all_valid_categories_accepted(self):
        for cat in VALID_CATEGORIES:
            payload = {**VALID_RISK_PAYLOAD, "category": cat}
            assert validate_payload(payload) == [], f"Category '{cat}' should be valid"


class TestCardBuilders:

    def test_card_title_includes_risk_id(self):
        title = build_card_title(VALID_RISK_PAYLOAD)
        assert "RSK-001" in title

    def test_card_title_includes_priority_emoji(self):
        title = build_card_title(VALID_RISK_PAYLOAD)  # probability=High
        assert "🟠" in title

    def test_card_description_contains_all_key_fields(self):
        desc = build_card_description(VALID_RISK_PAYLOAD)
        assert "RSK-001" in desc
        assert "Technical" in desc          # category appears in the table
        assert "Profile memory" in desc     # mitigation text
        assert "Auto-generated" in desc

    def test_card_description_shows_impact_score(self):
        desc = build_card_description(VALID_RISK_PAYLOAD)
        assert "8 / 10" in desc


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
