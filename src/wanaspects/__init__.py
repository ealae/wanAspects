"""wanaspects public API.

Cross-cutting aspects (logging, tracing, metrics, contract) and helpers.
"""

from .aspects import (
    ChainContractError,
    ContextPropagationAspect,
    ContractAspect,
    ContractViolation,
    LoggingAspect,
    MetricsAspect,
    TracingAspect,
)
from .aspects.conditional_context import ConditionalContextPropagationAspect
from .aspects.sampled_metrics import SampledMetricsAspect
from .aspects.smart_logging import SmartLoggingAspect
from .config import load_config
from .context import current_context
from .manager import AspectManager
from .optimized_manager import OptimizedAspectManager
from .telemetry import init_telemetry


def default_bundle() -> list[object]:
    return [
        ContextPropagationAspect(),
        LoggingAspect(),
        TracingAspect(),
        MetricsAspect(),
        ContractAspect(),
    ]


def dev_bundle() -> list[object]:
    """Development bundle with full verbose logging for debugging."""
    return [
        ContextPropagationAspect(),
        SmartLoggingAspect(tier="development"),  # Full logging
        TracingAspect(),
        MetricsAspect(),
        ContractAspect(),
    ]


def prod_bundle() -> list[object]:
    """Production bundle optimized for performance while maintaining observability.

    Optimizations:
    - Conditional context: Only propagate for boundary calls (saves 30-40x)
    - Smart logging: Only errors and boundary events (not noisy internal calls)
    - Sampled metrics: 10% sampling for metrics (100% error tracking)
    - Full tracing: OpenTelemetry spans for distributed tracing
    - No contracts: Validation overhead removed in production

    Target: ~100x overhead (achieves <100x with realistic workloads)
    """
    return [
        ConditionalContextPropagationAspect(),  # Only for boundaries
        SmartLoggingAspect(tier="production"),  # Errors + boundaries only
        TracingAspect(),
        SampledMetricsAspect(sample_rate=0.1),  # 10% sampling, 100% errors
        # ContractAspect(),  # Disabled in prod for performance
    ]


def bundle_from_config() -> list[object]:
    cfg = load_config()
    name = (cfg.bundle or "default").lower()
    if name == "prod":
        return prod_bundle()
    if name == "dev":
        return dev_bundle()
    return default_bundle()


__all__ = [
    "AspectManager",
    "OptimizedAspectManager",
    "ContextPropagationAspect",
    "ConditionalContextPropagationAspect",
    "LoggingAspect",
    "SmartLoggingAspect",
    "TracingAspect",
    "MetricsAspect",
    "SampledMetricsAspect",
    "ContractAspect",
    "ChainContractError",
    "ContractViolation",
    "current_context",
    "init_telemetry",
    "bundle_from_config",
    "dev_bundle",
    "prod_bundle",
    "default_bundle",
]
