from typing import Any, Dict, List, Mapping, Optional, Sequence
import uuid
import time
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
import asyncio
import websocket
import json


class WindowAIRouter:
    _instance = None

    window_requests = []
    window_responses = {}

    def __new__(cls):
        if cls._instance is None:
            print('Creating the object')
            cls._instance = super(WindowAIRouter, cls).__new__(cls)
            # Put any initialization here.
        return cls._instance

    def add_window_request(self, request):
        self.window_requests.append(request)

    def add_window_response(self, request_id, response):
        self.window_responses[request_id] = response

    def get_window_requests(self):
        return self.window_requests

    def get_window_response(self, request_id):
        if request_id not in self.window_responses:
            return None
        
        return self.window_responses[request_id]

    def delete_window_request(self, request):
        self.window_requests.remove(request)

    def delete_window_response(self, request_id):
        del self.window_responses[request_id]

window_router = WindowAIRouter()


class ChatWindowAI(BaseChatModel):
    model_name: str = "window"
    """Model name to use."""
    temperature: float = 0.7
    """What sampling temperature to use."""

    # TODO: use temperature in window.ai API call

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

        print("ChatWindowAI _generate result", result)

        return result
    
    async def _agenerate(
        self, messages: List[BaseMessage], stop: Optional[List[str]] = None
    ) -> ChatResult:
        return self._generate(messages, stop=stop)

    def _call(
        self, messages: List[BaseMessage], stop: Optional[List[str]] = None
    ) -> str:
        """Simpler interface."""
        print("ChatWindowAI _call messages", messages)

        request_id = str(uuid.uuid4())

        # python object with messages and request ID
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

        # websocket.enableTrace(True)
        ws = websocket.WebSocket()
        ws.connect("ws://127.0.0.1:5000/windowmodel")
        ws.send(json.dumps(request))
        message = ws.recv()
        ws.close()

        print(f"Received: {message}")

        message = json.loads(message)

        response = message["content"]

        """
        request_id = str(uuid.uuid4())

        # python object with messages and request ID
        request = {
            "messages": messages,
            "request_id": request_id,
        }

        window_router.add_window_request(request)

        response = None
        while True:
            requests = window_router.get_window_requests()
            print("ChatWindowAI _call requests", requests)

            response = window_router.get_window_response(request_id)
            if response:
                # window_router.delete_window_request(request)
                # window_router.delete_window_response(request_id)
                break
            time.sleep(0.25)

            # print("ChatWindowAI _call waiting for response")
        """

        print("ChatWindowAI _call response", response)

        return response

        #return "Hello from ChatWindowAI._call"