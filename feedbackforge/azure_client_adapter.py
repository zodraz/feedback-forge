"""
Azure AI Projects Client Adapter
=================================

Adapter class that bridges the new Azure AI Projects SDK (AIProjectClient) with
the agent_framework's ChatAgent which expects a ChatClientProtocol interface.
"""

import logging
from typing import Any, AsyncIterator
from azure.ai.projects.aio import AIProjectClient

logger = logging.getLogger(__name__)


class MessageWrapper:
    """Wrapper for message to match agent_framework expectations."""

    def __init__(self, content, role="assistant"):
        self.text = content
        self.role = role
        self.content = content
        self.author_name = None  # agent_framework checks this attribute
        self.metadata = {}
        self.tool_calls = []
        self.tool_call_id = None


class ResponseWrapper:
    """
    Wrapper for Azure SDK Response to match agent_framework's expected interface.

    The Azure SDK Response has different attributes than agent_framework expects:
    - Azure: response.conversation, response.output_text, response.id
    - agent_framework: response.conversation_id, response.messages, response.text, response.response_id
    """

    def __init__(self, azure_response):
        # Store the original response
        object.__setattr__(self, '_response', azure_response)

        # Always set these core attributes (agent_framework expects them)
        object.__setattr__(self, 'messages', [])
        object.__setattr__(self, 'text', "")
        object.__setattr__(self, 'value', "")
        object.__setattr__(self, 'conversation_id', None)
        object.__setattr__(self, 'response_id', None)
        object.__setattr__(self, 'metadata', {})
        object.__setattr__(self, 'usage', None)
        object.__setattr__(self, 'usage_details', None)
        object.__setattr__(self, 'model', None)
        object.__setattr__(self, 'additional_properties', {})

        # Now populate from azure_response
        if hasattr(azure_response, 'conversation'):
            object.__setattr__(self, 'conversation_id', azure_response.conversation)

        if hasattr(azure_response, 'id'):
            object.__setattr__(self, 'response_id', azure_response.id)

        if hasattr(azure_response, 'output_text'):
            output = azure_response.output_text
            object.__setattr__(self, 'text', output)
            object.__setattr__(self, 'value', output)
            object.__setattr__(self, 'messages', [MessageWrapper(output)])

    def __getattr__(self, name):
        """Delegate all other attributes to the wrapped response."""
        # Safeguard: return None for known optional attributes instead of delegating
        if name in ('usage_details', 'usage', 'metadata', 'model', 'finish_reason', 'stop_reason', 'tool_calls'):
            return None

        # If messages/text/value are not set, return defaults
        if name == 'messages':
            return []
        if name == 'text' or name == 'value':
            return ""
        if name == 'conversation_id' or name == 'response_id':
            return None
        if name == 'additional_properties':
            return {}

        return getattr(self._response, name)


class AIProjectChatClient:
    """
    Adapter class that wraps AIProjectClient to implement ChatClientProtocol.

    This bridges the new Azure AI Projects SDK (AIProjectClient) with the
    agent_framework's ChatAgent which expects a ChatClientProtocol interface.

    Follows the pattern from JavaScript @azure/ai-projects:
    - project.getOpenAIClient() → openAIClient
    - openAIClient.conversations.create() → creates conversations
    - openAIClient.responses.create() → generates agent responses
    """

    def __init__(self, project: AIProjectClient, agent_version, model: str):
        self.project = project
        self.agent_version = agent_version
        # Extract deployment name from connection/deployment format if present
        # e.g., "feedbackforgev3-connection/gpt-5.1-chat" -> "gpt-5.1-chat"
        self.model = model.split('/')[-1] if '/' in model else model
        self.additional_properties: dict[str, Any] = {}
        self.openai_client = project.get_openai_client()

        logger.info(f"✅ AIProjectChatClient initialized with model: {self.model} (original: {model})")

    async def get_response(self, messages: Any, **kwargs: Any) -> Any:
        """Get a response from the agent for the given messages."""
        # Create a conversation with initial messages
        conversation_items = []
        if isinstance(messages, list):
            for msg in messages:
                if isinstance(msg, dict):
                    conversation_items.append({
                        "type": "message",
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", str(msg))
                    })
                else:
                    conversation_items.append({
                        "type": "message",
                        "role": "user",
                        "content": str(msg)
                    })
        else:
            conversation_items.append({
                "type": "message",
                "role": "user",
                "content": str(messages)
            })

        # Create conversation
        conversation = await self.openai_client.conversations.create(
            items=conversation_items
        )

        # Prepare request parameters with agent reference and model
        # The Azure AI Gateway requires BOTH agent_reference and model parameter
        extra_body_dict = {
            "agent_reference": {
                "name": self.agent_version.name,
                "type": "agent_reference"
            }
        }

        request_params = {
            "conversation": conversation.id,
            "model": self.model,  # Required by Azure AI Gateway for routing
            "extra_body": extra_body_dict
        }

        logger.debug(f"Creating response for conversation {conversation.id}, model={self.model}, agent={self.agent_version.name}")
        response = await self.openai_client.responses.create(**request_params)

        # Wrap response to add conversation_id for agent_framework compatibility
        return ResponseWrapper(response)

    async def get_streaming_response(self, messages: Any, **kwargs: Any) -> AsyncIterator[Any]:
        """Get a streaming response from the agent for the given messages."""
        # Create a conversation with initial messages
        conversation_items = []
        if isinstance(messages, list):
            for msg in messages:
                if isinstance(msg, dict):
                    conversation_items.append({
                        "type": "message",
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", str(msg))
                    })
                else:
                    conversation_items.append({
                        "type": "message",
                        "role": "user",
                        "content": str(msg)
                    })
        else:
            conversation_items.append({
                "type": "message",
                "role": "user",
                "content": str(messages)
            })

        # Create conversation
        conversation = await self.openai_client.conversations.create(
            items=conversation_items
        )

        # Prepare streaming request parameters
        # The Azure AI Gateway requires BOTH agent_reference and model parameter
        extra_body_dict = {
            "agent_reference": {
                "name": self.agent_version.name,
                "type": "agent_reference"
            }
        }

        request_params = {
            "conversation": conversation.id,
            "model": self.model,  # Required by Azure AI Gateway for routing
            "extra_body": extra_body_dict
        }

        logger.debug(f"Creating streaming response for conversation {conversation.id}, model={self.model}, agent={self.agent_version.name}")
        stream = await self.openai_client.responses.create(**request_params)

        async for chunk in stream:
            yield chunk
