import os

import dotenv
from llm_wrapper import create_client

# TODO: classes to create
# Game (or GameEngine?)
# Player

if __name__ == "__main__":
    dotenv.load_dotenv()

    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    client = create_client(
        provider="anthropic",
        api_key=ANTHROPIC_API_KEY,
        model="claude-haiku-4-5-20251001",
    )

    # With system prompt and temperature
    response = client.generate(
        messages=[
            {
                "role": "user",
                "content": "Hello, Claude",
            }
        ],
        max_tokens=1024,
        system="You should end every response with ':)'",
        temperature=0.0,
    )

    print(response.text)
