import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_PROMPTS_DIR = Path(__file__).resolve().parent


@lru_cache(maxsize=16)
def _read_template(filename: str) -> str:
    path = _PROMPTS_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Prompt template not found: {path}")
    return path.read_text(encoding="utf-8")


@lru_cache(maxsize=4)
def _read_json_templates(filename: str = "responses.json") -> dict[str, Any]:
    return json.loads(_read_template(filename))


def load_prompt(filename: str, **kwargs) -> str:
    """Dynamically loads a prompt template from app/ai/prompts/ and formats variables."""
    template = _read_template(filename)
    return template.format(**kwargs) if kwargs else template


def load_response(key: str, **kwargs) -> str:
    """Dynamically loads a static node response from app/ai/prompts/responses.json."""
    templates = _read_json_templates()
    if key not in templates:
        raise KeyError(f"Response template key not found: {key}")
    text = templates[key]
    return text.format(**kwargs) if kwargs else text
