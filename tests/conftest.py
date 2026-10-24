import os
import sys
from pathlib import Path

# Dummy secrets so module imports succeed; no real API is ever called
os.environ.setdefault("READWISE_TOKEN", "test-token")
os.environ.setdefault("OPENAI_API_KEY", "test-key")

sys.path.insert(0, str(Path(__file__).parent.parent))
