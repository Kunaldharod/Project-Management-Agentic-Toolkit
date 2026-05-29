# Agentic PMBOK Toolkit

An AI agent that reads your GitHub repository and keeps your project management documentation up to date — automatically.

Every six hours (or on every push), it scans your commits, pull requests, and open issues, identifies risks your team hasn't logged yet, and writes them to a structured risk register. It updates sprint velocity summaries, flags blockers, and pushes tickets to your Kanban board — all without anyone filling out a form.

---

## What it does

The agent acts as a background Scrum Master. It watches for patterns that experienced engineers recognize as warning signs: a module being reverted three times in a week, a PR sitting open with no reviewers, a senior developer who has gone quiet. When it spots something, it creates a PMBOK-formatted risk entry with an impact score, a mitigation strategy, and a direct link to the commit or PR that triggered it.

The output is a set of JSON files — `risk_register.json`, `velocity_log.json`, `stakeholder_map.json` — that stay current as long as the pipeline runs. A FastAPI server exposes these as REST endpoints. A React dashboard reads from those endpoints and refreshes every 30 seconds.

---
<img width="2125" height="1812" alt="agentic_pmbok_architecture" src="https://github.com/user-attachments/assets/9ec7a316-21e8-4826-9841-f86e89b522f8" />

---

## Project structure

```
agentic-pmbok/
├── src/
│   ├── git_extractor.py      # pulls commits, PRs, issues from GitHub
│   ├── kanban_connector.py   # creates/updates Trello or Jira tickets
│   ├── schema_validator.py   # validates AI output before writing to disk
│   ├── llm_client.py         # Anthropic/OpenAI adapter with retry logic
│   ├── agent_pipeline.py     # end-to-end orchestration loop
│   ├── test_phase1.py        # 21 tests — extractors and connectors
│   ├── test_phase2.py        # 36 tests — schemas, workflow, prompt
│   ├── test_phase3.py        # 52 tests — pipeline with mocked LLM
│   └── test_api.py           # 52 tests — all API endpoints
├── api/
│   └── main.py               # FastAPI server (12 endpoints)
├── schemas/
│   ├── risk_register.schema.json
│   ├── charter.schema.json
│   ├── stakeholder_map.schema.json
│   └── velocity_log.schema.json
├── artifacts/                # live output — updated by the agent
│   ├── risk_register.json
│   └── velocity_log.json
├── prompts/
│   └── agent_system_prompt.md  # agent persona and detection rules
├── n8n/
│   └── workflow.json           # importable n8n workflow
├── dashboard/
│   └── pmbok_dashboard.jsx     # React dashboard
├── logs/                       # runtime logs, created automatically
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## Setup

### 1. Clone and configure

```bash
git clone https://github.com/yourname/agentic-pmbok-toolkit.git
cd agentic-pmbok-toolkit
cp .env.example .env
```

Fill in `.env` at minimum:

```env
GITHUB_TOKEN=ghp_your_token_here
GITHUB_REPO=owner/your-repo
ANTHROPIC_API_KEY=sk-ant-your_key_here
KANBAN_PROVIDER=trello
TRELLO_API_KEY=...
TRELLO_TOKEN=...
TRELLO_BOARD_ID=...
TRELLO_LIST_ID=...
CURRENT_SPRINT=SP-01
SPRINT_START_DATE=2026-01-01
SPRINT_END_DATE=2026-01-14
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the tests

```bash
pytest src/test_phase1.py src/test_phase2.py src/test_phase3.py src/test_api.py -v
```

Expected: 161 passed. No API keys needed — all LLM calls are mocked.

### 4. Start the API server

```bash
uvicorn api.main:app --reload --port 8000
```

Check it's working:

```
http://localhost:8000/api/health      → { "status": "ok" }
http://localhost:8000/api/risks       → seed risk data
http://localhost:8000/api/dashboard   → full dashboard payload
http://localhost:8000/docs            → interactive API docs
```

### 5. Test the extractor (needs GitHub token)

```bash
python src/git_extractor.py --repo owner/your-repo --commits 20 --days 7
```

This prints the structured snapshot the agent will analyse. No LLM involved yet.

### 6. Run a dry-run pipeline call (needs LLM key)

```bash
python src/agent_pipeline.py \
  --repo owner/your-repo \
  --sprint SP-01 \
  --start 2026-01-01 \
  --end 2026-01-14 \
  --dry-run \
  --output text
```

`--dry-run` calls the LLM and shows you what it would write, without touching any files or Kanban boards.

### 7. Run a live pipeline call

Remove `--dry-run`. The agent will write to `artifacts/risk_register.json` and, if a risk is found, push a ticket to your Kanban board.

```bash
python src/agent_pipeline.py \
  --repo owner/your-repo \
  --sprint SP-01 \
  --start 2026-01-01 \
  --end 2026-01-14
```

### 8. Start the dashboard

```bash
cd dashboard
npm create vite@latest . -- --template react
# select "Ignore files and continue" when prompted
npm install recharts
```

Copy `pmbok_dashboard.jsx` into `dashboard/src/`, then replace `dashboard/src/App.jsx` with:

```jsx
import ProjectDashboard from './pmbok_dashboard'
export default function App() { return <ProjectDashboard /> }
```

```bash
npm run dev
# open http://localhost:5173
```

---

## Running with Docker

Both the API server and n8n run as Docker services:

```bash
docker compose up -d

# API   → http://localhost:8000
# n8n   → http://localhost:5678
```

---

## n8n workflow

The `n8n/workflow.json` file is a ready-to-import n8n workflow that runs the full pipeline on a 6-hour schedule (or on GitHub webhook push). After importing:

1. Add your OpenAI or Anthropic credential under **Settings → Credentials**
2. Connect the LLM sub-node to the AI Agent node's language model input
3. Confirm file paths match your setup (Docker vs local)
4. Run manually once to verify before activating the schedule

---

## API endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Server and artifact file status |
| GET | `/api/risks` | All risks (filterable by status, category, impact) |
| GET | `/api/risks/summary` | KPI aggregations |
| GET | `/api/risks/{risk_id}` | Single risk entry |
| GET | `/api/velocity` | Full sprint velocity log |
| GET | `/api/velocity/current` | Active sprint |
| GET | `/api/velocity/{sprint_id}` | Single sprint |
| GET | `/api/stakeholders` | Stakeholder map |
| GET | `/api/pipeline/runs` | Pipeline audit log |
| GET | `/api/pipeline/stats` | Aggregated run statistics |
| POST | `/api/pipeline/trigger` | Trigger a pipeline run manually |
| GET | `/api/dashboard` | Single payload for the dashboard |

Interactive docs at `http://localhost:8000/docs`.

---

## How the agent decides what to flag

The system prompt in `prompts/agent_system_prompt.md` defines six detection rules:

- **Repetition** — three or more commits touching the same module with words like `revert`, `hotfix`, or `workaround` → Technical risk
- **Revert** — any explicit git revert → automatic impact score of 7 or higher
- **Blocker labels** — issues tagged `blocker` or `p0` open for more than 3 days → Schedule risk
- **Stale PRs** — a PR open for 5+ days with no review comments → Resource risk
- **Contributor silence** — a developer who normally commits 5+ times per sprint goes quiet → Resource risk
- **Confidence threshold** — risks need at least two independent signals to be created; a single data point goes in a watch list instead

The agent outputs strict JSON matching the schemas in `schemas/`. If the output doesn't validate, nothing is written.

---

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GITHUB_TOKEN` | Yes | Personal access token (scopes: repo, issues) |
| `GITHUB_REPO` | Yes | `owner/repo-name` |
| `ANTHROPIC_API_KEY` | One of these | Claude API key |
| `OPENAI_API_KEY` | One of these | OpenAI API key |
| `KANBAN_PROVIDER` | Yes | `trello` or `jira` |
| `TRELLO_API_KEY` | Trello | Developer key from trello.com/app-key |
| `TRELLO_TOKEN` | Trello | OAuth token |
| `TRELLO_BOARD_ID` | Trello | Board ID from board URL |
| `TRELLO_LIST_ID` | Trello | Column ID for the Risks list |
| `JIRA_BASE_URL` | Jira | `https://yourorg.atlassian.net` |
| `JIRA_USER_EMAIL` | Jira | Atlassian account email |
| `JIRA_API_TOKEN` | Jira | Atlassian API token |
| `JIRA_PROJECT_KEY` | Jira | e.g. `PROJ` |
| `CURRENT_SPRINT` | Yes | e.g. `SP-03` |
| `SPRINT_START_DATE` | Yes | `YYYY-MM-DD` |
| `SPRINT_END_DATE` | Yes | `YYYY-MM-DD` |
| `SLACK_CHANNEL_ID` | Optional | For Slack notifications from n8n |

---

## Test coverage

| Phase | Scope | Tests |
|-------|-------|-------|
| Phase 1 | GitHub extractor, Kanban connector | 21 |
| Phase 2 | PMBOK schemas, n8n workflow, system prompt | 36 |
| Phase 3 | LLM pipeline end-to-end (mocked) | 52 |
| API | All FastAPI endpoints | 52 |
| **Total** | | **161** |

---

## Deployment checklist

- [ ] All 161 tests passing locally
- [ ] `.env` filled in with real tokens
- [ ] `python src/agent_pipeline.py --dry-run` produces valid JSON
- [ ] `http://localhost:8000/api/health` returns `{ "status": "ok" }`
- [ ] Dashboard loading at `http://localhost:5173`
- [ ] n8n workflow imported and manually triggered once successfully
- [ ] n8n workflow activated (enables the 6-hour schedule)

---

## License

MIT
