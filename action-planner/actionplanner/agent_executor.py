# Copyright (c) Microsoft. All rights reserved.

"""AgentExecutor bridge between the a2a-sdk server and Agent Framework agents.

Implements the a2a-sdk ``AgentExecutor`` interface so that incoming A2A
requests are forwarded to an Agent Framework agent and the response is
published back through the a2a-sdk event queue.
"""

from __future__ import annotations

import asyncio
import uuid
from typing import TYPE_CHECKING

from a2a.server.agent_execution.agent_executor import AgentExecutor
from a2a.types import (
    Message,
    Part,
    Role,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
    TextPart,
)

if TYPE_CHECKING:
    from a2a.server.agent_execution.context import RequestContext
    from a2a.server.events.event_queue import EventQueue
    from agent_framework import ChatAgent


class AgentFrameworkExecutor(AgentExecutor):
    """Bridges A2A protocol requests to an Agent Framework agent.

    For each incoming ``execute`` call the executor:
    1. Extracts the user's text from the A2A ``RequestContext``.
    2. Runs the Agent Framework agent (non-streaming).
    3. Publishes the result as an A2A ``Message`` to the ``EventQueue``.
    """

    def __init__(self, agent: ChatAgent) -> None:
        """Initialize the executor with an Agent Framework ChatAgent.

        Args:
            agent: The ChatAgent instance to execute requests against
        """
        self.agent = agent

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Run the agent and publish the response.

        Args:
            context: The A2A request context containing user input
            event_queue: Queue for publishing status updates and results
        """
        user_text = context.get_user_input()
        if not user_text:
            user_text = "Hello"

        task_id = context.task_id or str(uuid.uuid4())
        context_id = context.context_id or str(uuid.uuid4())

        # Signal that the agent is working
        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                task_id=task_id,
                context_id=context_id,
                status=TaskStatus(state=TaskState.working),
                final=False,
            )
        )

        try:
            response = await self.agent.run(user_text)

            # Build response text from agent messages
            response_parts: list[Part] = []

            # Handle different response types
            if isinstance(response, str):
                # Direct string response
                response_parts.append(TextPart(text=response))
            elif hasattr(response, 'messages'):
                # Agent Framework response with messages
                for msg in response.messages:
                    if msg.text:
                        response_parts.append(TextPart(text=msg.text))

            if not response_parts:
                response_parts.append(TextPart(text=str(response)))

            # Publish the agent's response as a completed message
            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    task_id=task_id,
                    context_id=context_id,
                    status=TaskStatus(
                        state=TaskState.completed,
                        message=Message(
                            message_id=str(uuid.uuid4()),
                            role=Role.agent,
                            parts=response_parts,
                        ),
                    ),
                    final=True,
                )
            )
        except asyncio.CancelledError:
            raise
        except Exception as e:
            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    task_id=task_id,
                    context_id=context_id,
                    status=TaskStatus(
                        state=TaskState.failed,
                        message=Message(
                            message_id=str(uuid.uuid4()),
                            role=Role.agent,
                            parts=[TextPart(text=f"Agent error: {e}")],
                        ),
                    ),
                    final=True,
                )
            )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Handle cancellation by publishing a canceled status.

        Args:
            context: The A2A request context
            event_queue: Queue for publishing status updates
        """
        task_id = context.task_id or str(uuid.uuid4())
        context_id = context.context_id or str(uuid.uuid4())

        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                task_id=task_id,
                context_id=context_id,
                status=TaskStatus(state=TaskState.canceled),
                final=True,
            )
        )
