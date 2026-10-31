from pathlib import Path
from typing import TypeVar

import yaml
from pydantic import BaseModel

TESTCASES_DIR = Path("data/testcases")

T = TypeVar("T", bound=BaseModel)


def load_cases(filename: str, model: type[T]) -> list[T]:
    """Load a YAML list of test cases and validate each entry with a Pydantic model."""
    raw = yaml.safe_load((TESTCASES_DIR / filename).read_text(encoding="utf-8"))
    return [model.model_validate(item) for item in raw]
