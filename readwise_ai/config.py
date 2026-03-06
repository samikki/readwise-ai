import os
from dotenv import load_dotenv

load_dotenv()

READWISE_TOKEN: str = os.getenv("READWISE_TOKEN", "")
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")

PRIORITY_TAGS: list[str] = ["Local", "Tesla", "AI", "Movies", "TV", "Games", "Technology"]
IGNORE_TAGS: list[str] = ["Humour", "Summary"]
