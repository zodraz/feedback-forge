"""
FeedbackForge MCP Server
========================

Model Context Protocol server for Zendesk integration.

This MCP server provides:
- Tools: Fetch and create Zendesk tickets
- Resources: Expose feedback streams as readable resources
- Integration: Populate FeedbackForge data store with Zendesk data

Usage:
    # Run as standalone MCP server
    python -m feedbackforge.mcp_server

    # Or configure in MCP client (Claude Desktop, IDEs)
    {
        "mcpServers": {
            "feedbackforge": {
                "command": "python",
                "args": ["-m", "feedbackforge.mcp_server"]
            }
        }
    }
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
)
from pydantic import AnyUrl

from .data_store import feedback_store
from .models import FeedbackItem

logger = logging.getLogger(__name__)

# Initialize MCP server
app = Server("feedbackforge-mcp")


# ============================================================================
# TOOLS - External Feedback Fetching
# ============================================================================

@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available MCP tools for Zendesk integration."""
    return [
        Tool(
            name="fetch_zendesk_tickets",
            description="Fetch support tickets from Zendesk as feedback items. Requires ZENDESK_SUBDOMAIN and ZENDESK_API_TOKEN env vars.",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["new", "open", "pending", "solved", "all"],
                        "default": "open",
                        "description": "Ticket status filter"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "normal", "high", "urgent", "all"],
                        "default": "all",
                        "description": "Priority filter"
                    },
                    "days": {
                        "type": "integer",
                        "default": 7,
                        "description": "Fetch tickets from the last N days"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 100,
                        "description": "Maximum number of tickets to fetch"
                    }
                }
            }
        ),
        Tool(
            name="ingest_feedback_to_store",
            description="Ingest fetched feedback items into FeedbackForge data store (Cosmos DB or in-memory). Call this after fetching from Zendesk.",
            inputSchema={
                "type": "object",
                "properties": {
                    "feedback_items": {
                        "type": "array",
                        "description": "Array of feedback items to ingest (in FeedbackItem format)",
                        "items": {
                            "type": "object"
                        }
                    },
                    "source": {
                        "type": "string",
                        "description": "Source name (e.g., 'zendesk')"
                    }
                },
                "required": ["feedback_items", "source"]
            }
        ),
        Tool(
            name="analyze_sentiment_batch",
            description="Run sentiment analysis on a batch of text feedback using Azure AI. Useful for external data that doesn't have sentiment yet.",
            inputSchema={
                "type": "object",
                "properties": {
                    "texts": {
                        "type": "array",
                        "description": "Array of text strings to analyze",
                        "items": {
                            "type": "string"
                        }
                    }
                },
                "required": ["texts"]
            }
        ),
        Tool(
            name="create_zendesk_ticket",
            description="Create a new support ticket in Zendesk. Use this to escalate FeedbackForge feedback items to Zendesk. Requires ZENDESK_SUBDOMAIN, ZENDESK_EMAIL, and ZENDESK_API_TOKEN env vars.",
            inputSchema={
                "type": "object",
                "properties": {
                    "subject": {
                        "type": "string",
                        "description": "Ticket subject/title"
                    },
                    "description": {
                        "type": "string",
                        "description": "Ticket description/body"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "normal", "high", "urgent"],
                        "default": "normal",
                        "description": "Ticket priority"
                    },
                    "type": {
                        "type": "string",
                        "enum": ["problem", "incident", "question", "task"],
                        "default": "problem",
                        "description": "Ticket type"
                    },
                    "tags": {
                        "type": "array",
                        "description": "Array of tags to apply (e.g., ['bug', 'ios', 'urgent'])",
                        "items": {
                            "type": "string"
                        }
                    },
                    "custom_fields": {
                        "type": "object",
                        "description": "Custom field values (field_id: value pairs)"
                    }
                },
                "required": ["subject", "description"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    """Handle tool calls for Zendesk integration."""

    if name == "fetch_zendesk_tickets":
        return await fetch_zendesk_tickets(arguments)
    elif name == "ingest_feedback_to_store":
        return await ingest_feedback_to_store(arguments)
    elif name == "analyze_sentiment_batch":
        return await analyze_sentiment_batch(arguments)
    elif name == "create_zendesk_ticket":
        return await create_zendesk_ticket(arguments)
    else:
        return [TextContent(
            type="text",
            text=json.dumps({"error": f"Unknown tool: {name}"})
        )]


async def fetch_zendesk_tickets(args: Dict[str, Any]) -> List[TextContent]:
    """Fetch Zendesk tickets and convert to feedback format."""
    try:
        logger.info("🎫 Starting fetch_zendesk_tickets...")
        logger.info(f"📥 Input args: {args}")

        import httpx

        subdomain = os.environ.get("ZENDESK_SUBDOMAIN")
        api_token = os.environ.get("ZENDESK_API_TOKEN")
        email = os.environ.get("ZENDESK_EMAIL")

        logger.info(f"🔑 Credentials check: subdomain={bool(subdomain)}, token={bool(api_token)}, email={bool(email)}")

        if not subdomain or not api_token or not email:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": "Missing Zendesk credentials",
                    "required_env_vars": ["ZENDESK_SUBDOMAIN", "ZENDESK_API_TOKEN", "ZENDESK_EMAIL"]
                })
            )]

        status = args.get("status", "open")
        priority = args.get("priority", "all")
        days = args.get("days", 7)
        limit = args.get("limit", 100)

        logger.info(f"📊 Fetch parameters: status={status}, priority={priority}, days={days}, limit={limit}")

        # Build Zendesk search query
        date_filter = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        query_parts = [f"created>{date_filter}"]

        if status != "all":
            query_parts.append(f"status:{status}")
        if priority != "all":
            query_parts.append(f"priority:{priority}")

        query = " ".join(query_parts)

        url = f"https://{subdomain}.zendesk.com/api/v2/search.json"
        params = {
            "query": f"type:ticket {query}",
            "sort_by": "updated_at",
            "sort_order": "desc"
        }

        auth = (f"{email}/token", api_token)

        async with httpx.AsyncClient() as client:
            logger.info(f"🌐 Calling Zendesk API: {url}")
            logger.info(f"📋 Query params: {params}")

            response = await client.get(url, params=params, auth=auth, timeout=30.0)
            response.raise_for_status()

            logger.info(f"✅ Zendesk API response status: {response.status_code}")

            data = response.json()

        logger.info(f"📊 Zendesk API response type: {type(data)}")
        logger.debug(f"📊 Zendesk API response keys: {list(data.keys()) if isinstance(data, dict) else 'not a dict'}")

        if not isinstance(data, dict):
            logger.error(f"❌ Unexpected Zendesk API response type: {type(data)}")
            return [TextContent(type="text", text=json.dumps({
                "error": f"Invalid response from Zendesk API: expected dict, got {type(data).__name__}",
                "source": "zendesk"
            }))]

        # Get results with explicit None check
        tickets = data.get("results")

        if tickets is None:
            logger.warning(f"⚠️  'results' key is None in Zendesk response. Response keys: {list(data.keys())}")
            logger.warning(f"⚠️  Full response: {json.dumps(data, indent=2)[:500]}")
            tickets = []

        if not tickets:
            logger.info("No tickets found in Zendesk search results")
            return [TextContent(type="text", text=json.dumps({
                "success": True,
                "source": "zendesk",
                "fetched_count": 0,
                "feedback_items": []
            }))]

        tickets = tickets[:limit]

        # Convert to FeedbackItem format
        feedback_items = []
        for i, ticket in enumerate(tickets):
            try:
                if ticket is None:
                    logger.warning(f"Skipping ticket at index {i}: ticket is None")
                    continue

                if not isinstance(ticket, dict):
                    logger.warning(f"Skipping ticket at index {i}: not a dict, got {type(ticket)}")
                    continue

                ticket_id = ticket.get('id')
                if not ticket_id:
                    logger.warning(f"Skipping ticket at index {i}: missing 'id' field")
                    continue

                # Convert ticket_id to integer safely
                try:
                    ticket_id_int = int(ticket_id)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Skipping ticket at index {i}: invalid ticket_id '{ticket_id}' - {e}")
                    continue

                # Get fields safely with type checking
                priority = ticket.get("priority")
                sentiment = "negative" if priority in ["high", "urgent"] else "neutral"
                is_urgent = priority == "urgent"

                # Get subject safely
                subject = ticket.get('subject') or 'No subject'
                if not isinstance(subject, str):
                    subject = str(subject)

                # Get description safely
                description = ticket.get('description') or ''
                if not isinstance(description, str):
                    description = str(description) if description else ''
                if len(description) > 500:
                    description = description[:500]

                # Get timestamp safely
                timestamp = ticket.get("created_at")
                if not timestamp:
                    timestamp = datetime.now().isoformat()
                elif not isinstance(timestamp, str):
                    timestamp = str(timestamp)

                # Get requester_id safely
                requester_id = ticket.get('requester_id', 'unknown')

                feedback_items.append({
                    "id": f"ZD{ticket_id_int:08d}",
                    "text": f"{subject}\n\n{description}",
                    "sentiment": sentiment,
                    "sentiment_score": -0.7 if is_urgent else -0.3 if sentiment == "negative" else 0.0,
                    "topics": [ticket.get("type", "support"), "support"],
                    "customer_segment": "Unknown",
                    "customer_id": f"ZD_{requester_id}",
                    "customer_name": f"Zendesk User {requester_id}",
                    "rating": 1 if is_urgent else 2 if sentiment == "negative" else 3,
                    "timestamp": timestamp,
                    "product_version": "Unknown",
                    "platform": "Zendesk",
                    "is_urgent": is_urgent,
                    "competitor_mentions": []
                    # Note: metadata removed - not part of FeedbackItem model
                    # Original metadata: source=zendesk, ticket_id={ticket_id_int}, status={status}, priority={priority}
                })
            except Exception as ticket_error:
                logger.error(f"Error processing ticket at index {i}: {ticket_error}", exc_info=True)
                logger.error(f"Problematic ticket data: {ticket}")
                continue

        result = {
            "success": True,
            "source": "zendesk",
            "fetched_count": len(feedback_items),
            "feedback_items": feedback_items
        }

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"❌ Error fetching Zendesk tickets: {e}")
        logger.error(f"❌ Error type: {type(e).__name__}")
        logger.error(f"❌ Full traceback:\n{error_trace}")

        return [TextContent(
            type="text",
            text=json.dumps({
                "error": str(e),
                "error_type": type(e).__name__,
                "traceback": error_trace,
                "source": "zendesk"
            })
        )]


async def create_zendesk_ticket(args: Dict[str, Any]) -> List[TextContent]:
    """Create a new ticket in Zendesk."""
    try:
        import httpx

        subdomain = os.environ.get("ZENDESK_SUBDOMAIN")
        api_token = os.environ.get("ZENDESK_API_TOKEN")
        email = os.environ.get("ZENDESK_EMAIL")

        if not subdomain or not api_token or not email:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": "Missing Zendesk credentials",
                    "required_env_vars": ["ZENDESK_SUBDOMAIN", "ZENDESK_API_TOKEN", "ZENDESK_EMAIL"]
                })
            )]

        subject = args["subject"]
        description = args["description"]
        priority = args.get("priority", "normal")
        ticket_type = args.get("type", "problem")
        tags = args.get("tags", [])
        custom_fields = args.get("custom_fields", {})

        # Build ticket payload
        ticket_data = {
            "ticket": {
                "subject": subject,
                "comment": {
                    "body": description
                },
                "priority": priority,
                "type": ticket_type,
                "tags": tags
            }
        }

        # Add custom fields if provided
        if custom_fields:
            ticket_data["ticket"]["custom_fields"] = [
                {"id": field_id, "value": value}
                for field_id, value in custom_fields.items()
            ]

        url = f"https://{subdomain}.zendesk.com/api/v2/tickets.json"
        auth = (f"{email}/token", api_token)
        headers = {
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=ticket_data,
                auth=auth,
                headers=headers,
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()

        ticket = data.get("ticket", {})

        result = {
            "success": True,
            "ticket_id": ticket.get("id"),
            "ticket_url": f"https://{subdomain}.zendesk.com/agent/tickets/{ticket.get('id')}",
            "subject": ticket.get("subject"),
            "status": ticket.get("status"),
            "priority": ticket.get("priority"),
            "created_at": ticket.get("created_at")
        }

        logger.info(f"Created Zendesk ticket #{ticket.get('id')}: {subject}")

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        logger.error(f"Error creating Zendesk ticket: {e}", exc_info=True)
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": str(e),
                "message": "Failed to create Zendesk ticket"
            })
        )]


async def ingest_feedback_to_store(args: Dict[str, Any]) -> List[TextContent]:
    """Ingest fetched feedback items into FeedbackForge data store with idempotency."""
    try:
        feedback_items = args["feedback_items"]
        source = args["source"]

        # Convert dict to FeedbackItem and store
        ingested_count = 0
        skipped_count = 0
        errors = []

        for item_dict in feedback_items:
            try:
                # Parse timestamp if it's a string
                if isinstance(item_dict.get("timestamp"), str):
                    item_dict["timestamp"] = datetime.fromisoformat(
                        item_dict["timestamp"].replace("Z", "+00:00")
                    )

                # Create FeedbackItem
                feedback_item = FeedbackItem(**item_dict)

                # Use idempotent ingest method
                was_ingested = feedback_store.ingest_feedback_item(feedback_item)

                if was_ingested:
                    ingested_count += 1
                else:
                    skipped_count += 1

            except Exception as e:
                errors.append({"item_id": item_dict.get("id"), "error": str(e)})

        result = {
            "success": True,
            "source": source,
            "ingested_count": ingested_count,
            "skipped_count": skipped_count,
            "total_items": len(feedback_items),
            "errors": errors[:5]  # Show first 5 errors
        }

        logger.info(f"Ingested {ingested_count}/{len(feedback_items)} feedback items from {source} (skipped {skipped_count} duplicates)")

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        logger.error(f"Error ingesting feedback: {e}", exc_info=True)
        return [TextContent(
            type="text",
            text=json.dumps({"error": str(e), "success": False})
        )]


async def analyze_sentiment_batch(args: Dict[str, Any]) -> List[TextContent]:
    """Analyze sentiment for a batch of texts using Azure AI."""
    try:
        texts = args["texts"]

        # Placeholder for Azure AI sentiment analysis
        # In production, integrate with Azure Cognitive Services
        results = []
        for text in texts:
            # Simple heuristic for demo
            text_lower = text.lower()

            if any(word in text_lower for word in ["bug", "crash", "broken", "error", "fail"]):
                sentiment = "negative"
                score = -0.6
            elif any(word in text_lower for word in ["great", "love", "excellent", "amazing"]):
                sentiment = "positive"
                score = 0.7
            else:
                sentiment = "neutral"
                score = 0.0

            results.append({
                "text": text[:100] + "..." if len(text) > 100 else text,
                "sentiment": sentiment,
                "sentiment_score": score
            })

        return [TextContent(type="text", text=json.dumps({
            "success": True,
            "analyzed_count": len(results),
            "results": results
        }, indent=2))]

    except Exception as e:
        logger.error(f"Error analyzing sentiment: {e}", exc_info=True)
        return [TextContent(
            type="text",
            text=json.dumps({"error": str(e)})
        )]


# ============================================================================
# RESOURCES - Feedback Streams
# ============================================================================

@app.list_resources()
async def list_resources() -> List[Resource]:
    """List available feedback stream resources."""
    return [
        Resource(
            uri=AnyUrl("feedbackforge://feedback/recent"),
            name="Recent Feedback",
            description="Stream of recent feedback items from the data store",
            mimeType="application/json"
        ),
        Resource(
            uri=AnyUrl("feedbackforge://feedback/urgent"),
            name="Urgent Feedback",
            description="High-priority feedback items requiring immediate attention",
            mimeType="application/json"
        ),
        Resource(
            uri=AnyUrl("feedbackforge://feedback/negative"),
            name="Negative Feedback",
            description="Feedback with negative sentiment for issue tracking",
            mimeType="application/json"
        ),
        Resource(
            uri=AnyUrl("feedbackforge://analytics/summary"),
            name="Feedback Analytics Summary",
            description="Weekly summary statistics and top issues",
            mimeType="application/json"
        )
    ]


@app.read_resource()
async def read_resource(uri: AnyUrl) -> str:
    """Read feedback stream resources."""
    try:
        uri_str = str(uri)
        if uri_str == "feedbackforge://feedback/recent":
            # Get last 50 feedback items
            feedback_items = feedback_store.feedback[:50]
            return json.dumps([
                {
                    "id": f.id,
                    "text": f.text[:200],
                    "sentiment": f.sentiment,
                    "topics": f.topics,
                    "timestamp": f.timestamp.isoformat(),
                    "customer_segment": f.customer_segment,
                    "is_urgent": f.is_urgent
                }
                for f in feedback_items
            ], indent=2)

        elif uri_str == "feedbackforge://feedback/urgent":
            # Get urgent feedback
            urgent = [f for f in feedback_store.feedback if f.is_urgent][:25]
            return json.dumps([
                {
                    "id": f.id,
                    "text": f.text[:200],
                    "sentiment": f.sentiment,
                    "topics": f.topics,
                    "timestamp": f.timestamp.isoformat(),
                    "customer_name": f.customer_name,
                    "customer_segment": f.customer_segment
                }
                for f in urgent
            ], indent=2)

        elif uri_str == "feedbackforge://feedback/negative":
            # Get negative feedback
            negative = [f for f in feedback_store.feedback if f.sentiment == "negative"][:50]
            return json.dumps([
                {
                    "id": f.id,
                    "text": f.text[:200],
                    "topics": f.topics,
                    "sentiment_score": f.sentiment_score,
                    "timestamp": f.timestamp.isoformat(),
                    "customer_segment": f.customer_segment
                }
                for f in negative
            ], indent=2)

        elif uri_str == "feedbackforge://analytics/summary":
            # Get weekly summary
            summary = feedback_store.get_weekly_summary()
            return json.dumps(summary, indent=2)

        else:
            return json.dumps({"error": f"Unknown resource: {uri_str}"})

    except Exception as e:
        logger.error(f"Error reading resource {uri_str}: {e}", exc_info=True)
        return json.dumps({"error": str(e)})


# ============================================================================
# PROMPTS - Pre-built Analysis Prompts
# ============================================================================

@app.list_prompts()
async def list_prompts() -> List[Any]:
    """List available analysis prompts."""
    from mcp.types import Prompt, PromptArgument

    return [
        Prompt(
            name="analyze_feedback_trends",
            description="Analyze feedback trends and identify emerging issues",
            arguments=[
                PromptArgument(
                    name="days",
                    description="Number of days to analyze",
                    required=False
                )
            ]
        ),
        Prompt(
            name="generate_executive_summary",
            description="Generate executive summary of customer feedback",
            arguments=[]
        )
    ]


@app.get_prompt()
async def get_prompt(name: str, arguments: Dict[str, str] | None = None) -> Any:
    """Get pre-built analysis prompts."""
    from mcp.types import GetPromptResult, PromptMessage, TextContent as PromptTextContent

    if name == "analyze_feedback_trends":
        days = arguments.get("days", "7") if arguments else "7"
        summary = feedback_store.get_weekly_summary()

        return GetPromptResult(
            description="Analyze recent feedback trends",
            messages=[
                PromptMessage(
                    role="user",
                    content=PromptTextContent(
                        type="text",
                        text=f"""Analyze the following feedback data from the last {days} days and identify:

1. Top emerging issues requiring attention
2. Sentiment trends and shifts
3. Customer segment-specific concerns
4. Recommended immediate actions

Feedback Summary:
{json.dumps(summary, indent=2)}

Provide a structured analysis with priorities and action items."""
                    )
                )
            ]
        )

    elif name == "generate_executive_summary":
        summary = feedback_store.get_weekly_summary()
        anomalies = feedback_store.detect_anomalies()

        return GetPromptResult(
            description="Generate executive summary",
            messages=[
                PromptMessage(
                    role="user",
                    content=PromptTextContent(
                        type="text",
                        text=f"""Generate an executive summary of customer feedback with:

1. Key metrics and trends
2. Critical issues and anomalies
3. Customer satisfaction indicators
4. Strategic recommendations

Weekly Summary:
{json.dumps(summary, indent=2)}

Detected Anomalies:
{json.dumps(anomalies, indent=2)}

Provide a concise, actionable executive summary suitable for leadership review."""
                    )
                )
            ]
        )

    else:
        raise ValueError(f"Unknown prompt: {name}")


# ============================================================================
# SSE Server for HTTP Transport
# ============================================================================

def create_sse_app():
    """Create Starlette app with SSE transport for MCP server."""
    from starlette.applications import Starlette
    from starlette.routing import Route
    from starlette.responses import JSONResponse
    from starlette.middleware import Middleware
    from starlette.middleware.cors import CORSMiddleware
    from mcp.server.sse import SseServerTransport

    # Create SSE transport - messages will be posted to /messages
    sse = SseServerTransport("/messages")

    async def handle_sse(scope, receive, send):
        """
        ASGI app for SSE endpoint.
        This must be a raw ASGI app, not a Starlette route handler.
        """
        logger.info("🔌 SSE connection initiated")
        logger.info(f"   Scope type: {scope.get('type')}")
        logger.info(f"   Path: {scope.get('path')}")

        async with sse.connect_sse(scope, receive, send) as streams:
            logger.info("✅ SSE streams connected")
            read_stream, write_stream = streams
            logger.info(f"   Read stream type: {type(read_stream)}")
            logger.info(f"   Write stream type: {type(write_stream)}")

            try:
                logger.info("🚀 Starting MCP app.run()...")
                init_options = app.create_initialization_options()
                logger.info(f"   Init options: {init_options}")

                await app.run(
                    read_stream,
                    write_stream,
                    init_options
                )
                logger.info("✅ MCP app.run() completed normally")
            except Exception as e:
                logger.error(f"❌ Error in MCP app.run(): {e}", exc_info=True)

    async def handle_messages(scope, receive, send):
        """
        ASGI app for messages endpoint.
        This must be a raw ASGI app, not a Starlette route handler.
        """
        await sse.handle_post_message(scope, receive, send)

    async def health_check(request):
        """Health check endpoint."""
        _ = request  # Required by Starlette Route signature
        return JSONResponse({
            "status": "healthy",
            "server": "feedbackforge-mcp",
            "transport": "sse"
        })

    # Create Starlette app
    from starlette.routing import Mount

    starlette_app = Starlette(
        routes=[
            Mount("/sse", app=handle_sse),
            Mount("/messages", app=handle_messages),
            Route("/health", health_check),
        ],
        middleware=[
            Middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
        ],
    )

    return starlette_app


# ============================================================================
# MAIN - Run MCP Server
# ============================================================================

async def main():
    """Run the MCP server with stdio transport."""
    logger.info("Starting FeedbackForge MCP Server (stdio)...")

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


def run_sse_server(host: str = "127.0.0.1", port: int = 8082):
    """Run the MCP server with SSE transport over HTTP."""
    import uvicorn

    logger.info("=" * 60)
    logger.info("  FeedbackForge MCP Server (SSE/HTTP)")
    logger.info("=" * 60)
    logger.info(f"SSE endpoint:  http://{host}:{port}/sse")
    logger.info(f"POST endpoint: http://{host}:{port}/messages")
    logger.info(f"Health check:  http://{host}:{port}/health")
    logger.info("=" * 60)

    sse_app = create_sse_app()
    uvicorn.run(sse_app, host=host, port=port)


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)

    # Check for SSE mode
    if "--sse" in sys.argv:
        host = "127.0.0.1"
        port = 8082

        for i, arg in enumerate(sys.argv):
            if arg == "--host" and i + 1 < len(sys.argv):
                host = sys.argv[i + 1]
            elif arg == "--port" and i + 1 < len(sys.argv):
                port = int(sys.argv[i + 1])

        run_sse_server(host, port)
    else:
        asyncio.run(main())
