from enum import Enum

from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI

load_dotenv()


class ChatModel(Enum):
    TURBO = "gpt-3.5-turbo"
    GPT4 = "gpt-4"


def get_chat_model(model: ChatModel):
    return ChatOpenAI(model_name=model.value, temperature=0.6)
