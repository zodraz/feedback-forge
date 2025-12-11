# FeedbackForge Frontend

React application with AG-UI streaming integration for the FeedbackForge Executive Dashboard.

## Prerequisites

- Node.js 18+
- npm or yarn
- FeedbackForge AG-UI server running

## Quick Start

### 1. Start the Backend (AG-UI Server)

```bash
# From the python directory
cd /home/abel/git/agent-framework/python

# Start the AG-UI server
python -m feedbackforge serve
```

The server will start at `http://localhost:8080`.

### 2. Start the Frontend

```bash
# From the frontend directory
cd feedbackforge/frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will start at `http://localhost:3000`.

## Architecture

```
┌─────────────────────┐     AG-UI Protocol     ┌─────────────────────┐
│   React Frontend    │ ◄─────────────────────► │  FeedbackForge API  │
│   (Custom AG-UI)    │      SSE Streaming      │  (FastAPI + AG-UI)  │
│   localhost:3000    │                         │   localhost:8080    │
└─────────────────────┘                         └─────────────────────┘
```

## Features

- **Custom AG-UI Client** - Direct SSE streaming from AG-UI server
- **Quick Actions Sidebar** - One-click common queries
- **Real-time Streaming** - Token-by-token response display
- **Tool Call Indicators** - Shows when tools are being used
- **Dark Theme** - Executive dashboard styling

## Available Queries

Try these in the chat:

- "Show me this week's feedback summary"
- "What are the top issues this week?"
- "Tell me more about the iOS crashes"
- "What are customers saying about competitors?"
- "Check for any anomalies in recent feedback"
- "Show me customers at risk of churning"
- "Get context for customer ENT001"
- "Generate action items for the iOS issue"
- "Escalate the crash issue to Engineering"

## Development

```bash
# Development with hot reload
npm run dev

# Type checking
npx tsc --noEmit

# Production build
npm run build

# Preview production build
npm run preview
```

## Configuration

The backend URL is configured in `src/App.tsx`:

```tsx
const AG_UI_URL = "http://localhost:8080";
```

For production, update this to your deployed AG-UI server URL.

## AG-UI Protocol

This frontend implements a custom AG-UI client that:

1. Sends messages via POST to the AG-UI endpoint
2. Receives SSE (Server-Sent Events) stream
3. Parses AG-UI event types:
   - `TEXT_MESSAGE_CONTENT` - Streaming text tokens
   - `TEXT_MESSAGE_END` - Message complete
   - `TOOL_CALL_START` - Tool invocation begins
   - `TOOL_CALL_END` - Tool invocation complete
   - `RUN_FINISHED` - Conversation turn complete

## Troubleshooting

### CORS Errors

If you see CORS errors, ensure the AG-UI server is running. The server includes CORS middleware by default.

### Connection Refused

Make sure the AG-UI server is running:
```bash
python -m feedbackforge serve
```

### No Response

Check the browser console for errors. Ensure:
1. The AG-UI server is running on port 8080
2. No firewall is blocking the connection
3. The server logs show incoming requests
