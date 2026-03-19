# Action Planner Agent

Autonomous agent that converts feedback insights into trackable action items across multiple ticketing systems (Jira).

## Features

- **A2A Protocol**: Seamless agent-to-agent communication with FeedbackForge Dashboard
- **Multi-Platform Support**: Create tickets in Jira
- **Intelligent Prioritization**: Analyzes feedback severity and affected customer count
- **Auto-Assignment**: Suggests team owners based on issue category
- **Effort Estimation**: Provides T-shirt size estimates (S/M/L/XL)
- **Progress Tracking**: Links tickets back to feedback items

## Architecture

```
┌─────────────────────────────────┐
│   FeedbackForge                 │
│   Dashboard Agent                │
│   Port: 8081                     │
└───────────┬─────────────────────┘
            │
            │ A2A Protocol
            │ HTTP POST /agent
            │
            ▼
┌─────────────────────────────────┐
│   Action Planner                │
│   Action Planning Agent          │
│   Port: 8084                     │
│                                  │
│   Integrations:                  │
│   ├─ Jira REST API              │

└─────────────────────────────────┘
```

## Installation

```bash
# Clone the repository
cd /home/abel/git/action-planner

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Copy environment template
cp .env.example .env
# Edit .env with your credentials
```

## Configuration

Configure at least one ticketing system in `.env`:

### Jira Setup
1. Generate API token: https://id.atlassian.com/manage-profile/security/api-tokens
2. Set `JIRA_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`, `JIRA_PROJECT_KEY`

## Usage

### Standalone Mode (for testing)

```bash
# Start the agent server
python -m actionplanner

# Or with custom port
python -m actionplanner --port 8084
```

### A2A Mode (integrated with FeedbackForge)

```bash
# Start FeedbackForge dashboard (in feedback-forge directory)
cd /home/abel/git/feedback-forge
python -m feedbackforge serve

# Start Action Planner (in action-planner directory)
cd /home/abel/git/action-planner
python -m actionplanner
```

The dashboard agent can now call the action planner:

```
User: "Create tickets for the iOS crash issues"
Dashboard Agent: [Analyzes feedback, identifies 45 crash reports]
Dashboard Agent: [Calls Action Planner via A2A]
Action Planner: [Creates Jira ticket FEED-123]
Action Planner: [Returns ticket URL and details]
Dashboard Agent: "Created ticket FEED-123: Fix iOS payment flow crash (45 affected users)"
```

## API Endpoints

### AG-UI Endpoint (A2A)
- **URL**: `POST http://localhost:8084/agent`
- **Protocol**: AG-UI (agent-framework)
- **Usage**: Called by other agents using A2A protocol

### REST API
- **Health**: `GET http://localhost:8084/health`
- **Info**: `GET http://localhost:8084/info`

## Example A2A Call from Dashboard Agent

```python
# In FeedbackForge dashboard_agent.py
from agent_framework.a2a import call_agent

async def create_action_items(issue_summary: str, affected_count: int):
    """Tool: Create action items via Action Planner agent."""
    response = await call_agent(
        agent_url="http://localhost:8084/agent",
        prompt=f"""Create action plan for this issue:

        Issue: {issue_summary}
        Affected Customers: {affected_count}
        Priority: High

        Create appropriate tickets and return the ticket IDs."""
    )
    return response
```

## Agent Capabilities

The Action Planner agent can:

1. **Analyze Issue Details**
   - Severity assessment
   - Category detection (bug, feature, improvement)
   - Platform identification (iOS, Android, Web)

2. **Create Tickets**
   - Auto-fill title, description, labels
   - Set priority based on affected users
   - Add custom fields (affected_customers, feedback_ids)

3. **Assign Ownership**
   - Suggest team based on category
   - Route to appropriate assignee

4. **Estimate Effort**
   - T-shirt sizing (S/M/L/XL)
   - Complexity analysis

5. **Link & Track**
   - Link tickets to original feedback
   - Track ticket progress
   - Update stakeholders

## Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=actionplanner

# Type checking
pyright actionplanner/
```

## Docker

```bash
# Build
docker build -t action-planner .

# Run
docker run -p 8084:8084 --env-file .env action-planner
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Lint
ruff check actionplanner/

# Format
ruff format actionplanner/

# Type check
pyright actionplanner/
```

## License

MIT
