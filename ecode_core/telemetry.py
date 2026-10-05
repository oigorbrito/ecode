from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


class NullTelemetry:
    def emit(self, event: Mapping[str, Any]) -> None:
        return None


class JsonlTelemetry:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, event: Mapping[str, Any]) -> None:
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(dict(event), sort_keys=True) + "\n")
