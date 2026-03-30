"""
Intent detection for ALFRED.
Auto-classifies user queries as 'command' (system operation) or 'knowledge' (Q&A).
Uses a combination of keyword heuristics and an LLM classifier fallback.
"""
import os
import re
from typing import Literal

import google.generativeai as genai

_api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
if _api_key:
    genai.configure(api_key=_api_key)

IntentType = Literal['command', 'knowledge']

# ── Heuristic patterns ──────────────────────────────────────────────

# Strong command indicators: verbs that imply system actions
COMMAND_PATTERNS = [
    r'\b(create|make|delete|remove|rename|move|copy|open|close|run|execute|install)\b.*\b(file|folder|directory|app|program|process|service|shortcut)\b',
    r'\b(list|show|display|get)\b.*\b(files|folders|directories|processes|services|drives)\b',
    r'\b(shut\s*down|restart|log\s*off|sleep|hibernate)\b',
    r'\b(powershell|cmd|terminal|command\s*prompt|pip|npm|git)\b',
    r'\b(mkdir|rmdir|del|copy|move|ren|echo|cd|ls|dir|cat|type)\b',
    r'\b(set|unset|export)\b.*\b(env|environment|variable|path)\b',
    r'\b(start|stop|kill)\b.*\b(process|service|task)\b',
    r'\b(download|upload|extract|zip|unzip|compress)\b',
]

# Strong knowledge indicators: question words, conceptual queries
KNOWLEDGE_PATTERNS = [
    r'^(what|who|where|when|why|how|explain|describe|summarize|tell me about|define)\b',
    r'\b(meaning|definition|concept|theory|difference between|compare)\b',
    r'\b(according to|based on|from the|in the document|in my notes|in my files)\b',
    r'\b(summary|overview|key points|main idea|takeaway)\b',
    r'\?([\s]*)$',  # Ends with a question mark
]

COMMAND_RE = [re.compile(p, re.IGNORECASE) for p in COMMAND_PATTERNS]
KNOWLEDGE_RE = [re.compile(p, re.IGNORECASE) for p in KNOWLEDGE_PATTERNS]


def _heuristic_classify(text: str) -> IntentType | None:
    """
    Fast heuristic classification. Returns None if uncertain.
    """
    cmd_score = sum(1 for r in COMMAND_RE if r.search(text))
    know_score = sum(1 for r in KNOWLEDGE_RE if r.search(text))

    if cmd_score > 0 and know_score == 0:
        return 'command'
    if know_score > 0 and cmd_score == 0:
        return 'knowledge'
    if cmd_score > know_score:
        return 'command'
    if know_score > cmd_score:
        return 'knowledge'

    return None  # Ambiguous — fall back to LLM


def _llm_classify(text: str) -> IntentType:
    """
    Use the LLM to classify intent when heuristics are ambiguous.
    """
    prompt = (
        "You are an intent classifier. Given a user message, respond with EXACTLY "
        "one word: either 'command' or 'knowledge'.\n\n"
        "- 'command' means the user wants to perform a system action "
        "(create files, run programs, manage processes, execute shell commands, etc.)\n"
        "- 'knowledge' means the user is asking a question, seeking information, "
        "or wants an explanation.\n\n"
        f"User message: {text}\n\n"
        "Classification:"
    )

    try:
        from .model_resolver import get_model
        model = get_model()
        response = model.generate_content(prompt)
        result = (response.text or '').strip().lower()
        if 'command' in result:
            return 'command'
        return 'knowledge'
    except Exception:
        # Default to knowledge on failure — it's the safer fallback
        return 'knowledge'


def classify_intent(text: str, has_knowledge_base: bool = True) -> IntentType:
    """
    Classify whether the user's query is a system command or a knowledge question.

    If no documents are in the knowledge base, always routes to 'command' mode
    (the original behavior) to avoid empty RAG responses.
    """
    if not has_knowledge_base:
        return 'command'

    result = _heuristic_classify(text)
    if result is not None:
        return result

    return _llm_classify(text)
