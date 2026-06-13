import os
from typing import Any, Callable, Dict, List, Optional
from .config import settings


SUMMARY_PROMPT = (
    "Provide a detailed but concise summary of the conversation above. "
    "Focus on information that would be helpful for continuing the conversation, "
    "including: what was discussed, what decisions were made, "
    "what files were modified, and what the next step is."
)


def count_tokens(text: str) -> int:
    """Estimate token count. 1 token ≈ 4 chars in English, 2 chars in Chinese."""
    return len(text) // 4


def count_messages_tokens(messages: List[Dict[str, Any]]) -> int:
    """Count total tokens in a messages list."""
    total = 0
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str):
            total += count_tokens(content)
        elif isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and part.get("text"):
                    total += count_tokens(part["text"])
                elif isinstance(part, str):
                    total += count_tokens(part)
        tool_calls = msg.get("tool_calls")
        if tool_calls:
            for tc in tool_calls:
                if isinstance(tc, dict):
                    func = tc.get("function", {})
                    total += count_tokens(func.get("name", ""))
                    total += count_tokens(func.get("arguments", ""))
    return total


def should_compact(messages: List[Dict[str, Any]], threshold: int) -> bool:
    """Check if messages should be compressed."""
    if threshold <= 0:
        return False
    return count_messages_tokens(messages) >= threshold


def build_summary_messages(
    messages: List[Dict[str, Any]],
    summary_text: str,
) -> List[Dict[str, Any]]:
    """
    After a summary is generated, rebuild the message list.
    Summary is prepended to system messages, and latest turns are kept.
    """
    summary_msg = {
        "role": "user",
        "content": f"Previous conversation summary:\n{summary_text}"
    }
    return [summary_msg]


class ConversationCompactor:
    """
    Manages conversation compression.
    """

    def __init__(self, threshold: int = 0):
        self.threshold = threshold
        self.last_summary: Optional[str] = None

    def check_and_compact(
        self,
        messages: List[Dict[str, Any]],
        client,  # OpenAI client
        model: str,
    ) -> List[Dict[str, Any]]:
        """
        If total tokens >= threshold, compress messages.
        Returns the compressed message list.
        """
        if not should_compact(messages, self.threshold):
            return messages

        # Build messages for summarization
        summary_prompt = {
            "role": "user",
            "content": SUMMARY_PROMPT
        }
        summarize_messages = messages + [summary_prompt]

        # Call LLM to summarize
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=summarize_messages,
                max_tokens=1024,
                temperature=0.3,
            )
            summary_text = resp.choices[0].message.content or ""
            if not summary_text:
                return messages
        except Exception:
            return messages

        self.last_summary = summary_text
        return build_summary_messages(messages, summary_text)
