"""
git_extractor.py
----------------
Pulls the last N commits, open pull requests, and recent issues from a
GitHub repository and returns a structured plain-text summary suitable
for ingestion by the n8n AI Agent node.

Usage (standalone / CLI):
    python git_extractor.py --repo owner/repo-name --commits 50 --days 7

Usage (called by n8n Execute Command node):
    python git_extractor.py --repo owner/repo-name
    # Output is printed to stdout and captured by n8n

Environment variables (via .env or n8n credentials):
    GITHUB_TOKEN   — personal access token or GitHub App token (required)
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/git_extractor.log"),
        logging.StreamHandler(sys.stderr),
    ],
)
log = logging.getLogger(__name__)


# ── Constants ─────────────────────────────────────────────────────────────────
GITHUB_API = "https://api.github.com"
MAX_COMMIT_MESSAGE_LEN = 300   # truncate noisy long messages
MAX_PR_BODY_LEN = 500
MAX_ISSUE_BODY_LEN = 400


# ── GitHub REST client ────────────────────────────────────────────────────────
class GitHubClient:
    """Thin wrapper around the GitHub REST API v3."""

    def __init__(self, token: str, repo: str) -> None:
        if not token:
            raise ValueError("GITHUB_TOKEN is required but not set.")
        self.repo = repo
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
        )

    def _get(self, path: str, params: Optional[dict] = None) -> list | dict:
        url = f"{GITHUB_API}/repos/{self.repo}{path}"
        response = self.session.get(url, params=params, timeout=20)

        if response.status_code == 401:
            raise PermissionError("GitHub token is invalid or expired.")
        if response.status_code == 404:
            raise FileNotFoundError(f"Repository '{self.repo}' not found or private.")
        response.raise_for_status()
        return response.json()

    # ── Commits ───────────────────────────────────────────────────────────────
    def get_commits(self, limit: int = 50, since_days: int = 30) -> list[dict]:
        """Return the last `limit` commits from the default branch."""
        since = (datetime.now(timezone.utc) - timedelta(days=since_days)).isoformat()
        raw = self._get("/commits", params={"per_page": min(limit, 100), "since": since})
        commits = []
        for c in raw[:limit]:
            commit = c.get("commit", {})
            author = commit.get("author", {})
            commits.append(
                {
                    "sha": c["sha"][:8],
                    "author": author.get("name", "unknown"),
                    "date": author.get("date", ""),
                    "message": _truncate(commit.get("message", ""), MAX_COMMIT_MESSAGE_LEN),
                    "url": c.get("html_url", ""),
                }
            )
        log.info("Fetched %d commits from %s", len(commits), self.repo)
        return commits

    # ── Pull Requests ─────────────────────────────────────────────────────────
    def get_pull_requests(self, state: str = "open") -> list[dict]:
        """Return open (or closed) pull requests with labels and review status."""
        raw = self._get("/pulls", params={"state": state, "per_page": 50, "sort": "updated"})
        prs = []
        for pr in raw:
            prs.append(
                {
                    "number": pr["number"],
                    "title": pr["title"],
                    "author": pr.get("user", {}).get("login", "unknown"),
                    "state": pr["state"],
                    "draft": pr.get("draft", False),
                    "labels": [lb["name"] for lb in pr.get("labels", [])],
                    "body_preview": _truncate(pr.get("body") or "", MAX_PR_BODY_LEN),
                    "created_at": pr["created_at"],
                    "updated_at": pr["updated_at"],
                    "review_comments": pr.get("review_comments", 0),
                    "url": pr["html_url"],
                }
            )
        log.info("Fetched %d PRs (state=%s) from %s", len(prs), state, self.repo)
        return prs

    # ── Issues ────────────────────────────────────────────────────────────────
    def get_issues(self, since_days: int = 7) -> list[dict]:
        """Return issues updated within the last `since_days` days (excludes PRs)."""
        since = (datetime.now(timezone.utc) - timedelta(days=since_days)).isoformat()
        raw = self._get(
            "/issues",
            params={"state": "open", "per_page": 50, "since": since, "sort": "updated"},
        )
        issues = []
        for issue in raw:
            if "pull_request" in issue:   # GitHub returns PRs in issue list too
                continue
            issues.append(
                {
                    "number": issue["number"],
                    "title": issue["title"],
                    "author": issue.get("user", {}).get("login", "unknown"),
                    "labels": [lb["name"] for lb in issue.get("labels", [])],
                    "body_preview": _truncate(issue.get("body") or "", MAX_ISSUE_BODY_LEN),
                    "comments": issue.get("comments", 0),
                    "created_at": issue["created_at"],
                    "updated_at": issue["updated_at"],
                    "url": issue["html_url"],
                }
            )
        log.info("Fetched %d issues (since %d days) from %s", len(issues), since_days, self.repo)
        return issues

    # ── Repo meta ─────────────────────────────────────────────────────────────
    def get_repo_meta(self) -> dict:
        meta = self._get("")
        return {
            "name": meta.get("full_name"),
            "default_branch": meta.get("default_branch", "main"),
            "open_issues_count": meta.get("open_issues_count", 0),
            "language": meta.get("language"),
            "description": meta.get("description", ""),
        }


# ── Formatters ────────────────────────────────────────────────────────────────
def format_commits(commits: list[dict]) -> str:
    if not commits:
        return "  (no commits found in the specified window)\n"
    lines = []
    for c in commits:
        date_str = _fmt_date(c["date"])
        first_line = c["message"].split("\n")[0]
        lines.append(f"  [{c['sha']}] {date_str} | {c['author']}: {first_line}")
    return "\n".join(lines)


def format_pull_requests(prs: list[dict]) -> str:
    if not prs:
        return "  (no open pull requests)\n"
    lines = []
    for pr in prs:
        draft_tag = " [DRAFT]" if pr["draft"] else ""
        labels = f" labels={pr['labels']}" if pr["labels"] else ""
        lines.append(
            f"  PR#{pr['number']}{draft_tag}: {pr['title']}"
            f"\n    author={pr['author']} | reviews={pr['review_comments']}{labels}"
            f"\n    updated={_fmt_date(pr['updated_at'])} | {pr['url']}"
        )
        if pr["body_preview"]:
            lines.append(f"    desc: {pr['body_preview'][:200]}")
    return "\n".join(lines)


def format_issues(issues: list[dict]) -> str:
    if not issues:
        return "  (no open issues updated in the window)\n"
    lines = []
    for issue in issues:
        labels = f" labels={issue['labels']}" if issue["labels"] else ""
        lines.append(
            f"  Issue#{issue['number']}: {issue['title']}"
            f"\n    author={issue['author']} | comments={issue['comments']}{labels}"
            f"\n    updated={_fmt_date(issue['updated_at'])} | {issue['url']}"
        )
        if issue["body_preview"]:
            lines.append(f"    desc: {issue['body_preview'][:200]}")
    return "\n".join(lines)


def build_agent_payload(
    meta: dict,
    commits: list[dict],
    prs: list[dict],
    issues: list[dict],
    commit_limit: int,
    since_days: int,
) -> str:
    """
    Returns the structured text block that is sent as the 'user' message
    to the n8n AI Agent node. Keep this deterministic and token-efficient.
    """
    extracted_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    payload = f"""=== GIT REPOSITORY SNAPSHOT ===
Repo        : {meta['name']}
Branch      : {meta['default_branch']}
Language    : {meta['language']}
Extracted   : {extracted_at}
Window      : last {commit_limit} commits / issues updated in past {since_days} days

--- COMMITS (last {len(commits)}) ---
{format_commits(commits)}

--- OPEN PULL REQUESTS ({len(prs)}) ---
{format_pull_requests(prs)}

--- OPEN ISSUES updated in past {since_days}d ({len(issues)}) ---
{format_issues(issues)}

=== END SNAPSHOT ===
"""
    return payload


# ── Helpers ───────────────────────────────────────────────────────────────────
def _truncate(text: str, max_len: int) -> str:
    text = text.replace("\r\n", " ").replace("\n", " ").strip()
    return text[:max_len] + "…" if len(text) > max_len else text


def _fmt_date(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return iso


# ── Save raw JSON snapshot (optional, for debugging / audit trail) ────────────
def save_snapshot(data: dict, repo: str) -> None:
    slug = repo.replace("/", "_")
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = f"artifacts/{slug}_{ts}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    log.info("Raw snapshot saved to %s", path)


# ── CLI entry point ───────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(description="Extract GitHub repo activity for AI agent")
    parser.add_argument("--repo", required=True, help="GitHub repo in owner/name format")
    parser.add_argument("--commits", type=int, default=50, help="Number of commits to fetch")
    parser.add_argument("--days", type=int, default=7, help="Issue/PR activity window in days")
    parser.add_argument("--save-snapshot", action="store_true", help="Save raw JSON to artifacts/")
    parser.add_argument("--json", action="store_true", help="Output raw JSON instead of text")
    args = parser.parse_args()

    token = os.getenv("GITHUB_TOKEN")
    if not token:
        log.error("GITHUB_TOKEN environment variable is not set.")
        sys.exit(1)

    try:
        client = GitHubClient(token=token, repo=args.repo)

        meta = client.get_repo_meta()
        commits = client.get_commits(limit=args.commits, since_days=args.days * 4)
        prs = client.get_pull_requests(state="open")
        issues = client.get_issues(since_days=args.days)

        if args.save_snapshot:
            save_snapshot(
                {"meta": meta, "commits": commits, "pull_requests": prs, "issues": issues},
                args.repo,
            )

        if args.json:
            print(json.dumps(
                {"meta": meta, "commits": commits, "pull_requests": prs, "issues": issues},
                indent=2,
            ))
        else:
            # Default: print the plain-text agent payload to stdout
            # n8n's Execute Command node captures this as its output
            payload = build_agent_payload(meta, commits, prs, issues, args.commits, args.days)
            print(payload)

    except (PermissionError, FileNotFoundError) as e:
        log.error(str(e))
        sys.exit(1)
    except requests.exceptions.ConnectionError:
        log.error("Cannot reach GitHub API. Check network connectivity.")
        sys.exit(1)
    except Exception as e:
        log.exception("Unexpected error: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
