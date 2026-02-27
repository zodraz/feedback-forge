# FeedbackForge - Session Management Guide

## Overview

FeedbackForge uses different session management strategies depending on the mode:

---

## 1. Chat Mode Sessions (DevUI)

### How It Works
- **Mode**: Development interface using `agent-framework-devui`
- **Session Type**: Interactive terminal-based
- **State**: Single-user, ephemeral
- **Storage**: In-memory only

### Characteristics
```python
# In __main__.py
def run_chat_mode(port: int = 8090):
    agent = create_dashboard_agent()
    serve(entities=[agent], port=port, auto_open=True)
```

- No persistent sessions
- Each DevUI instance is isolated
- Agent state resets on restart
- Uses browser-based WebSocket connection

---

## 2. Dashboard Sessions (AG-UI Protocol)

### Frontend Session Management

The React dashboard maintains **client-side session state**:

```typescript
// dashboard/src/App.tsx
const [threadId] = useState(() => `thread-${Date.now()}`);
const [messages, setMessages] = useState<Message[]>([...]);
```

#### Key Points:
- **Thread ID**: Generated once per browser session: `thread-${Date.now()}`
- **Persistence**: Only in browser memory (lost on page refresh)
- **Message History**: Maintained in React state
- **Context Passing**: Full conversation history sent with each request

#### Message Flow:
```typescript
// Build message history for AG-UI
const agUiMessages = messages
  .filter((m) => m.id !== "welcome")
  .map((m) => ({
    id: m.id,
    role: m.role,
    content: m.content,
  }));

// Send to backend
fetch(AG_UI_URL, {
  method: "POST",
  body: JSON.stringify({
    thread_id: threadId,        // Session identifier
    run_id: `run-${Date.now()}`, // Request identifier
    messages: agUiMessages,      // Full conversation history
  }),
});
```

### Backend Session Management

The FastAPI backend is **stateless**:

```python
# server.py
agent = create_dashboard_agent()
add_agent_framework_fastapi_endpoint(app, agent, "/agent")
```

#### Key Points:
- **No server-side session storage**
- **Stateless processing**: Each request is independent
- **Agent re-created**: One agent instance per application start
- **Context from client**: Relies on frontend sending full message history

#### AG-UI Protocol Flow:
```
Frontend                    Backend
   |                           |
   |---(POST /agent)---------->|
   |   {thread_id, messages}   |
   |                           |
   |                    [Process with Agent]
   |                           |
   |<---(SSE Stream)-----------|
   |   data: {type, content}   |
   |<--------------------------|
```

### Agent Framework Session Handling

The Agent Framework (by Microsoft) handles:
- **Tool execution context**
- **Streaming responses**
- **Internal agent state** (per request)

```python
# dashboard_agent.py
agent = chat_client.create_agent(
    name="FeedbackForge",
    instructions=AGENT_INSTRUCTIONS,
    tools=TOOLS
)
# Agent is stateless - no built-in session persistence
```

---

## 3. Workflow Mode Sessions

### How It Works
- **Mode**: Batch processing using multi-agent workflow
- **Session Type**: Single execution run
- **State**: `AnalysisState` object passed through pipeline
- **Storage**: Results saved to JSON file

### State Management:

```python
# workflow.py
async def analyze(self, surveys: List[SurveyResponse]) -> Dict[str, Any]:
    final_result = None
    async for event in self.workflow.run_stream(AnalysisState(surveys=surveys)):
        if isinstance(event, WorkflowOutputEvent):
            final_result = event.data
    return final_result
```

#### Workflow State Object:
```python
# models.py
@dataclass
class AnalysisState:
    surveys: List[SurveyResponse]

    # Stage results
    orchestrator_initial: Optional[Dict] = None
    preprocessing: Optional[Dict] = None
    sentiment: Optional[Dict] = None
    topics: Optional[Dict] = None
    # ... etc
```

#### Characteristics:
- **Ephemeral**: Exists only during workflow execution
- **Sequential**: State passed through each executor
- **Fan-in/Fan-out**: Multiple executors can read/write same state
- **No session**: Each workflow run is independent

---

## Session Comparison Table

| Feature | Chat Mode (DevUI) | Dashboard (AG-UI) | Workflow Mode |
|---------|------------------|-------------------|---------------|
| **Session Storage** | In-memory (server) | Client-side only | None (ephemeral) |
| **Conversation History** | Terminal session | Browser memory | N/A |
| **State Persistence** | ❌ No | ❌ No | ❌ No |
| **Multi-user** | ❌ No | ✅ Yes (isolated) | ✅ Yes (parallel runs) |
| **Thread/Session ID** | N/A | Client-generated | Run-specific |
| **Authentication** | None | None | None |
| **Context Retention** | Session only | Page refresh lost | Single run only |

---

## Limitations & Gaps

### ❌ Current Issues:

1. **No Session Persistence**
   - Conversation history lost on page refresh
   - No ability to resume previous conversations
   - Each new session starts from scratch

2. **No User Authentication**
   - All users share same data
   - No user-specific context
   - No access control

3. **No Multi-Session Support**
   - Can't have multiple concurrent conversations
   - No conversation switching
   - No conversation history list

4. **No State Storage**
   - Agent has no memory between requests
   - Must send full context every time
   - Inefficient for long conversations

---

## Proposed Improvements

### 1. Add Session Persistence

```python
# sessions.py (NEW)
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import redis

class SessionManager:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.ttl = 3600  # 1 hour

    async def save_session(
        self,
        thread_id: str,
        messages: List[Dict],
        metadata: Dict = None
    ):
        """Save conversation session to Redis."""
        session_data = {
            "thread_id": thread_id,
            "messages": messages,
            "metadata": metadata or {},
            "updated_at": datetime.now().isoformat()
        }
        await self.redis.setex(
            f"session:{thread_id}",
            self.ttl,
            json.dumps(session_data)
        )

    async def load_session(
        self,
        thread_id: str
    ) -> Optional[Dict]:
        """Load conversation session from Redis."""
        data = await self.redis.get(f"session:{thread_id}")
        if data:
            return json.loads(data)
        return None

    async def list_sessions(
        self,
        user_id: str = None
    ) -> List[Dict]:
        """List all active sessions."""
        pattern = f"session:*{user_id}*" if user_id else "session:*"
        keys = await self.redis.keys(pattern)

        sessions = []
        for key in keys:
            data = await self.redis.get(key)
            if data:
                sessions.append(json.loads(data))

        return sorted(sessions, key=lambda x: x["updated_at"], reverse=True)
```

### 2. Update Server to Use Sessions

```python
# server.py (UPDATED)
from .sessions import SessionManager

# Initialize session manager
redis_client = redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379"))
session_manager = SessionManager(redis_client)

@app.post("/agent")
async def agent_endpoint(request: Request):
    body = await request.json()
    thread_id = body.get("thread_id")

    # Load existing session
    session = await session_manager.load_session(thread_id)

    # Merge with new messages
    messages = body.get("messages", [])

    # Process with agent...

    # Save updated session
    await session_manager.save_session(thread_id, messages)

    # Return response...
```

### 3. Add Session Management UI

```typescript
// New component: SessionList.tsx
function SessionList() {
  const [sessions, setSessions] = useState([]);

  useEffect(() => {
    fetch('/api/sessions')
      .then(r => r.json())
      .then(setSessions);
  }, []);

  return (
    <div className="session-list">
      <h3>Recent Conversations</h3>
      {sessions.map(session => (
        <button
          key={session.thread_id}
          onClick={() => loadSession(session.thread_id)}
        >
          {session.metadata?.title || 'Untitled'}
          <span>{new Date(session.updated_at).toLocaleString()}</span>
        </button>
      ))}
    </div>
  );
}
```

### 4. Add User Authentication

```python
# auth.py (NEW)
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def get_current_user(token: str = Depends(security)):
    """Validate JWT token and return user."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        return {"user_id": user_id}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Use in endpoints
@app.post("/agent")
async def agent_endpoint(
    request: Request,
    user: dict = Depends(get_current_user)
):
    # User-specific processing...
    pass
```

---

## Implementation Roadmap

### Phase 1: Basic Session Storage (Week 1)
- [ ] Set up Redis for session storage
- [ ] Implement SessionManager class
- [ ] Update server to save/load sessions
- [ ] Test session persistence

### Phase 2: Frontend Integration (Week 2)
- [ ] Add session list UI component
- [ ] Implement session switching
- [ ] Add "New Conversation" button
- [ ] Show session metadata (title, timestamp)

### Phase 3: Authentication (Week 3)
- [ ] Add JWT authentication
- [ ] User registration/login endpoints
- [ ] Protect agent endpoints
- [ ] User-specific session isolation

### Phase 4: Advanced Features (Week 4)
- [ ] Session search and filtering
- [ ] Export conversation history
- [ ] Share conversations
- [ ] Auto-save draft messages
- [ ] Session expiration management

---

## Configuration

### Environment Variables

```bash
# .env
REDIS_URL=redis://localhost:6379
SESSION_TTL=3600  # 1 hour
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION=86400  # 24 hours
```

### Redis Setup

```bash
# Docker
docker run -d -p 6379:6379 redis:7-alpine

# Or install locally
sudo apt-get install redis-server
sudo systemctl start redis
```

---

## Current Session Flow Diagram

```
┌─────────────────┐
│  User Browser   │
│  (Dashboard)    │
└────────┬────────┘
         │ 1. Generate thread_id
         │    thread-1709123456789
         │
         │ 2. Send POST /agent
         │    {thread_id, messages}
         ▼
┌─────────────────┐
│  FastAPI        │
│  (Stateless)    │
└────────┬────────┘
         │ 3. Process with Agent
         │    (No session storage)
         │
         │ 4. Return SSE stream
         ▼
┌─────────────────┐
│  User Browser   │
│  (Stores in     │
│   React state)  │
└─────────────────┘

❌ Lost on page refresh!
```

## Proposed Session Flow

```
┌─────────────────┐
│  User Browser   │
│  (Dashboard)    │
└────────┬────────┘
         │ 1. Generate thread_id
         │    thread-1709123456789
         │
         │ 2. Send POST /agent
         │    {thread_id, messages}
         ▼
┌─────────────────┐
│  FastAPI        │
│  (Stateful)     │
└────────┬────────┘
         │ 3. Load from Redis
         │
         │ 4. Process with Agent
         │
         │ 5. Save to Redis
         ▼
┌─────────────────┐
│  Redis          │
│  (Persistent)   │
└─────────────────┘

✅ Survives page refresh!
✅ Can resume conversations!
✅ Multi-device sync possible!
```

---

**Current Status**: No session persistence
**Priority**: High (affects user experience)
**Effort**: Medium (2-3 weeks with testing)
