# FeedbackForge - Project Structure

## Directory Layout

```
feedback-forge/
├── .claude/                  # Claude Code settings
├── .git/                     # Git repository
├── .venv/                    # Python virtual environment
├── .vscode/                  # VS Code settings
├── dashboard/                # React + TypeScript executive dashboard
│   ├── src/
│   │   ├── App.tsx          # Main dashboard component
│   │   ├── App.css          # Dashboard styles
│   │   ├── main.tsx         # React entry point
│   │   └── index.css        # Global styles
│   ├── index.html           # HTML template
│   ├── package.json         # Node dependencies
│   ├── tsconfig.json        # TypeScript config
│   └── vite.config.ts       # Vite build config
├── src/feedbackforge/        # Python backend package
│   ├── templates/           # Jinja2 HTML templates
│   │   └── welcome.html     # Welcome page template
│   ├── __init__.py          # Package initialization
│   ├── __main__.py          # CLI entry point
│   ├── chat_tools.py        # Agent tools for chat mode
│   ├── dashboard_agent.py   # Agent creation and configuration
│   ├── data_store.py        # In-memory data store with mock data
│   ├── executors.py         # Workflow executor classes (11 agents)
│   ├── models.py            # Data models (Pydantic/dataclasses)
│   ├── server.py            # FastAPI AG-UI server
│   └── workflow.py          # Multi-agent workflow orchestration
├── .env                      # Environment variables (not in git)
├── .gitignore               # Git ignore rules
├── IMPROVEMENTS.md          # Detailed improvement suggestions
├── PROJECT_STRUCTURE.md     # This file
├── README.md                # Main documentation
└── pyproject.toml           # Python project configuration

```

## Key Components

### Backend (Python)
- **Entry Point**: `src/feedbackforge/__main__.py`
- **Operating Modes**: Chat (DevUI), Serve (AG-UI), Workflow (Batch)
- **Framework**: Microsoft Agent Framework + Azure OpenAI
- **API Server**: FastAPI with AG-UI protocol
- **Port**: 8080 (default for serve mode)

### Dashboard (React + TypeScript)
- **Entry Point**: `dashboard/src/main.tsx`
- **Framework**: React 18 + Vite
- **Features**: Chat interface, quick actions, real-time streaming
- **Port**: 3000 (default)
- **Connects To**: Backend AG-UI endpoint at `http://localhost:8080/agent`

### Templates
- **Location**: `src/feedbackforge/templates/`
- **Engine**: Jinja2
- **Current Templates**:
  - `welcome.html` - Welcome page with API information

## Running the Application

### Backend Only
```bash
# Development mode (DevUI)
python -m feedbackforge

# Production server (AG-UI)
python -m feedbackforge serve --port 8080

# Batch workflow
python -m feedbackforge workflow --max-surveys 20
```

### Dashboard Only
```bash
cd dashboard
npm install
npm run dev
```

### Full Stack (Backend + Dashboard)
```bash
# Terminal 1 - Backend
python -m feedbackforge serve --port 8080

# Terminal 2 - Dashboard
cd dashboard && npm run dev
```

Then open http://localhost:3000/ in your browser.

## Dependencies

### Python (pyproject.toml)
- `agent-framework` - Microsoft Agent Framework
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `jinja2` - Template engine
- `azure-identity` - Azure authentication

### Node.js (dashboard/package.json)
- `react` - UI framework
- `vite` - Build tool
- `typescript` - Type safety

## Configuration Files

- `.env` - Environment variables (Azure credentials)
- `pyproject.toml` - Python dependencies and build config
- `dashboard/package.json` - Node dependencies
- `dashboard/vite.config.ts` - Vite configuration
- `dashboard/tsconfig.json` - TypeScript configuration

## Build Outputs

### Python
- Not applicable (interpreted)

### Dashboard
```bash
cd dashboard
npm run build
# Output: dashboard/dist/
```

## Development Tips

1. **Backend with auto-reload**:
   ```bash
   python -m feedbackforge serve --reload
   ```

2. **Dashboard with hot reload**:
   ```bash
   cd dashboard && npm run dev
   ```
   (Vite provides hot module replacement by default)

3. **View API docs**:
   Open http://localhost:8080/docs in your browser

4. **Check logs**:
   - Backend: stdout/stderr
   - Dashboard: Browser console (F12)

## Git Status

```bash
# Check what's changed
git status

# Current modified files:
# - src/feedbackforge/dashboard_agent.py
# - src/feedbackforge/executors.py
# - src/feedbackforge/workflow.py
```

---

**Last Updated**: 2026-02-27
