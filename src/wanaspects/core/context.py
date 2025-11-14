from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

ContainerShape = Literal["single", "batch", "workflow"]
Boundary = Literal["none", "geo", "io"]


@dataclass(frozen=True, slots=True)
class AdviceContext:
    step_name: str
    container_shape: ContainerShape
    boundary: Boundary = "none"
    run_id: str | None = None
    tenant: str | None = None
    trace_id: str | None = None
    span_id: str | None = None
    config_hash: str | None = None
    package_versions: dict[str, str] = field(default_factory=dict)
