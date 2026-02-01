from openrouter import OpenRouter
# import os

with OpenRouter(api_key=os.getenv("OPENROUTER_API_KEY")) as client:
    response = client.chat.send(
        model="minimax/minimax-m2",
        messages=[{"role": "user", "content": "Please introduce yourself."}],
    )

    print(response)


# from anthropic import Anthropic

# from .base import Client, LLMResponse, Message


# # TODO: type response
# def _extract_text_and_reasoning(response) -> tuple[str, str]:
#     text = []
#     reasoning = []

#     for block in response.content:
#         if block.type == "text":
#             text.append(block.text)
#         elif block.type == "thinking":
#             reasoning.append(block.thinking)

#     text = "\n".join(text).strip()
#     reasoning = "\n".join(reasoning).strip()

#     return text, reasoning


# class AnthropicClient(Client):
#     def __init__(self, *, api_key: str, model: str) -> None:
#         self._client = Anthropic(api_key=api_key)
#         self._model = model

#     def generate(
#         self,
#         *,
#         messages: list[Message],
#         system: str | None = None,
#         max_tokens: int = 1024,
#         temperature: float | None = None,
#         reasoning: dict | None = None,
#     ) -> LLMResponse:
#         request = {
#             "model": self._model,
#             "max_tokens": max_tokens,
#             "messages": messages,
#         }
#         if system is not None:
#             request["system"] = system
#         if temperature is not None:
#             request["temperature"] = temperature
#         if reasoning is not None:
#             request["thinking"] = reasoning

#         response = self._client.messages.create(**request)

#         response_text, response_reasoning = _extract_text_and_reasoning(response)

#         return LLMResponse(
#             text=response_text, reasoning=response_reasoning, raw=response
#         )
