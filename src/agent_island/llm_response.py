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

    text = None
    reasoning_parts: list[str] = []

    for item in getattr(raw, "output", []):
        item_type = getattr(item, "type", None)
        if item_type == "message" and text is None:
            for c in getattr(item, "content", []):
                t = getattr(c, "text", None)
                if t:
                    text = t
                    break
        elif item_type == "reasoning":
            # Concatenate all reasoning blocks. In standard text generation there
            # is only one, but interleaved tool use can produce multiple.
            for c in getattr(item, "content", None) or []:
                t = getattr(c, "text", None)
                if t:
                    reasoning_parts.append(t)

    reasoning = "\n\n".join(reasoning_parts) if reasoning_parts else None
    metadata = _extract_usage(raw) or None

    return LLMResponse(text=text or "", reasoning=reasoning, metadata=metadata)


def _extract_usage(raw: Any) -> dict[str, Any]:
    usage = getattr(raw, "usage", None)
    if usage is None:
        return {}

    result: dict[str, Any] = {}
    result["input_tokens"] = _as_int(getattr(usage, "input_tokens", None))
    result["completion_tokens"] = _as_int(getattr(usage, "output_tokens", None))
    result["total_tokens"] = _as_int(getattr(usage, "total_tokens", None))

    ct_details = getattr(usage, "output_tokens_details", None)
    if ct_details is not None:
        result["reasoning_tokens"] = _as_int(
            getattr(ct_details, "reasoning_tokens", None)
        )

    cost = getattr(usage, "cost", None)
    if cost is not None:
        result["cost"] = float(cost)

    return {k: v for k, v in result.items() if v is not None}


def _as_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
