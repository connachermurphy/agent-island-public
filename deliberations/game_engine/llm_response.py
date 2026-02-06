from dataclasses import dataclass
from typing import Any


@dataclass
class LLMResponse:
    text: str
    reasoning: str | None
    metadata: dict[str, Any] | None = None


def parse_openrouter_response(raw: Any) -> LLMResponse:
    if raw is None:
        return LLMResponse(text="", reasoning=None, metadata=None)

    message = _extract_message(raw)
    text = _as_str(_get_attr(message, ["content"])) if message is not None else None
    reasoning = (
        _as_str(_get_attr(message, ["reasoning"])) if message is not None else None
    )

    return LLMResponse(
        text=text or "",
        reasoning=reasoning,
        metadata=_extract_usage(raw) or None,
    )


def _extract_message(raw: Any) -> Any | None:
    choices = _get_attr(raw, ["choices"])
    if isinstance(choices, list) and choices:
        choice0 = choices[0]
        if isinstance(choice0, dict):
            return choice0.get("message")
        return _get_attr(choice0, ["message"])
    if isinstance(raw, dict):
        choices = raw.get("choices")
        if isinstance(choices, list) and choices:
            choice0 = choices[0]
            if isinstance(choice0, dict):
                return choice0.get("message")
    return None


def _extract_usage(raw: Any) -> dict[str, Any]:
    """Extract token counts and cost from an OpenRouter response."""
    usage = _get_attr(raw, ["usage"])
    if usage is None:
        return {}

    result: dict[str, Any] = {}

    result["cost"] = _as_float(_get_attr(usage, ["cost"])) or 0.0
    result["input_tokens"] = _as_int(_get_attr(usage, ["prompt_tokens"]))
    result["completion_tokens"] = _as_int(_get_attr(usage, ["completion_tokens"]))
    result["total_tokens"] = _as_int(_get_attr(usage, ["total_tokens"]))

    ct_details = _get_attr(usage, ["completion_tokens_details"])
    if ct_details is not None:
        result["reasoning_tokens"] = _as_int(
            _get_attr(ct_details, ["reasoning_tokens"])
        )

    return {k: v for k, v in result.items() if v is not None}


def _get_attr(obj: Any, names: list[str]) -> Any | None:
    if obj is None:
        return None
    for name in names:
        if hasattr(obj, name):
            return getattr(obj, name)
        if isinstance(obj, dict) and name in obj:
            return obj.get(name)
    return None


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _as_str(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return str(value)
