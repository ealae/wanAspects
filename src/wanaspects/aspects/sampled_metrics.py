from __future__ import annotations

from typing import Any

from ..core.context import AdviceContext
from .metrics import MetricsAspect

_MIN_SAMPLE_RATE = 0.0
_MAX_SAMPLE_RATE = 1.0


class SampledMetricsAspect(MetricsAspect):
    """Metrics aspect with configurable sampling for high-throughput scenarios.

    In high-throughput production environments, collecting metrics on every single
    call can add significant overhead (62x). Sampling allows you to collect metrics
    on a fraction of calls while still getting statistically significant data.

    Sampling strategy:
    - Errors are ALWAYS tracked (100% coverage)
    - Successful calls are sampled at the specified rate
    - Sample rate of 0.1 (10%) is recommended for most production use cases

    Example:
        # 10% sampling for metrics (reduces 62x overhead to ~6.2x)
        aspect = SampledMetricsAspect(sample_rate=0.1)

        # 1% sampling for extremely high throughput (reduces to ~0.62x)
        aspect = SampledMetricsAspect(sample_rate=0.01)
    """

    def __init__(self, sample_rate: float = 0.1) -> None:
        """Initialize sampled metrics aspect.

        Args:
            sample_rate: Fraction of successful calls to sample (0.0 to 1.0).
                        0.1 = 10%, 0.01 = 1%, etc.
                        Errors are always tracked regardless of sample rate.
        """
        super().__init__()
        if not _MIN_SAMPLE_RATE < sample_rate <= _MAX_SAMPLE_RATE:
            msg = (
                "sample_rate must be between "
                f"{_MIN_SAMPLE_RATE} and {_MAX_SAMPLE_RATE}, got {sample_rate}"
            )
            raise ValueError(msg)

        self.sample_rate = sample_rate
        self._counter = 0
        self._sample_interval = int(_MAX_SAMPLE_RATE / sample_rate)

    def _should_sample(self, error: Exception | None) -> bool:
        """Determine if this call should be sampled for metrics.

        Args:
            error: Exception if call failed, None if successful

        Returns:
            True if metrics should be collected for this call
        """
        # ALWAYS track errors (100% coverage)
        if error is not None:
            return True

        # Sample successful calls at specified rate
        self._counter += 1
        return (self._counter % self._sample_interval) == 0

    def after(
        self, ctx: AdviceContext, result: Any, error: Exception | None
    ) -> None:
        """Collect metrics only if this call is sampled.

        Errors are always tracked. Successful calls are sampled at the
        configured sample_rate.
        """
        if self._should_sample(error):
            super().after(ctx, result, error)
