from typing import List, Dict, Any
from langchain_core.messages import BaseMessage
from app.config import get_settings


class ShortTermMemory:
    def __init__(self, max_size: int = None):
        settings = get_settings()
        self.max_size = max_size or settings.short_term_memory_size
        self.messages: List[Dict[str, Any]] = []
        self.recent_context: Dict[str, Any] = {}

    def add_message(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})
        if len(self.messages) > self.max_size:
            self.messages.pop(0)

    def add_context(self, key: str, value: Any):
        self.recent_context[key] = value

    def get_messages(self) -> List[Dict[str, Any]]:
        return self.messages

    def get_context(self) -> Dict[str, Any]:
        return self.recent_context

    def clear(self):
        self.messages = []
        self.recent_context = {}

    def to_messages(self) -> List[BaseMessage]:
        from langchain_core.messages import HumanMessage, AIMessage
        result = []
        for msg in self.messages:
            if msg["role"] == "user":
                result.append(HumanMessage(content=msg["content"]))
            else:
                result.append(AIMessage(content=msg["content"]))
        return result