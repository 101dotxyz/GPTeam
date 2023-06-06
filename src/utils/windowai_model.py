import langchain
from langchain.chat_models.base import BaseChatModel, SimpleChatModel
from langchain.schema import BaseMessage
from langchain.schema import (
    AIMessage,
    BaseMessage,
    ChatGeneration,
    ChatResult,
    HumanMessage,
    SystemMessage,
    LLMResult,
    PromptValue,
)
from typing import Any, Dict, List, Mapping, Optional, Sequence
import websocket
import uuid
import json

class ChatWindowAI(BaseChatModel):
    model_name: str = "window"
    """Model name to use."""
    temperature: float = 0.7
    """What sampling temperature to use."""
    streaming: bool = False
    """Whether to stream the results."""
    request_timeout: int = 3600
    """Timeout in seconds for the request."""

    @property
    def _llm_type(self) -> str:
        """Return type of chat model."""
        return "window-chat"
    
    def _generate(
        self, messages: List[BaseMessage], stop: Optional[List[str]] = None
    ) -> ChatResult:
        output_str = self._call(messages, stop=stop)
        message = AIMessage(content=output_str)
        generation = ChatGeneration(message=message)
        result = ChatResult(generations=[generation])
        return result
    
    async def _agenerate(
        self, messages: List[BaseMessage], stop: Optional[List[str]] = None
    ) -> ChatResult:
        return self._generate(messages, stop=stop)

    def _call(
        self, messages: List[BaseMessage], stop: Optional[List[str]] = None
    ) -> str:
        request_id = str(uuid.uuid4())
        request = {
            "messages": [],
            "temperature": self.temperature,
            "request_id": request_id,
        }

        for message in messages:
            role = "user" # default role is user
            if isinstance(message, HumanMessage):
                role = "user"
            elif isinstance(message, AIMessage):
                role = "assistant"
            elif isinstance(message, SystemMessage):
                role = "system"

            request["messages"].append({
                "role": role,
                "content": message.content,
            })

        ws = websocket.WebSocket()
        ws.connect("ws://127.0.0.1:5000/windowmodel")
        ws.send(json.dumps(request))
        message = ws.recv()
        ws.close()

        message = json.loads(message)

        response_content = message["content"]
        response_request_id = message["request_id"]

        # sanity check that response corresponds to request
        if request_id != response_request_id:
            raise ValueError(f"Invalid request ID: {response_request_id}, expected: {request_id}")

        return response_content